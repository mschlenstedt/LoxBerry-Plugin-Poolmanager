#!/usr/bin/python3
# -*- coding: utf-8 -*-

import io
import sys
import fcntl
import time
import copy
import string
import paho.mqtt.client as mqtt
import json
import logging
import os
from datetime import datetime
import getopt
#import atexit
import signal
from queue import Queue
from AtlasI2C import (
	 AtlasI2C
)

# Basic needed vars - Part 1
q=Queue()
verbose=0
laststatus = 0
lastvalues = 0
lastalive = 0
stop = 0
calibrate = 0
valuecycle = 0
devices = dict()
device_list = list()
pconfig = dict()
sconfig = dict()
mqttconfig = dict()

lbpconfigdir = os.popen("perl -e 'use LoxBerry::System; print $lbpconfigdir; exit;'").read()
lbpdatadir = os.popen("perl -e 'use LoxBerry::System; print $lbpdatadir; exit;'").read()
lbplogdir = os.popen("perl -e 'use LoxBerry::System; print $lbplogdir; exit;'").read()

#############################################################################
# MQTT Lib functions
#############################################################################

def on_connect(client, userdata, flags, rc):
    if rc==0:
        client.connected_flag=True #set flag
        log.info("MQTT: Connected OK")
    else:
        log.critical("MQTT: Bad connection, Returned code=",rc)

def on_message(client, userdata, message):
    q.put(message)

#############################################################################
# Plugin Lib functions
#############################################################################

def remove_non_ascii(string):
    return ''.join(char for char in string if ord(char) < 128)

def readconfig():
    device_list.clear()
    try:
        with open(lbpconfigdir + '/plugin.json') as f:
            global pconfig
            global devices
            pconfig = json.load(f)

        # Set default values
        if int(pconfig['statuscycle']) < 1.5:
            log.warning("Status Cycle is smaller than 1.5 seconds or not defined. Setting it to 300 seconds.")
            pconfig['statuscycle'] = 300
        if int(pconfig['valuecycle']) < 1.5:
            log.warning("Values Cycle is smaller than 1.5 seconds or not defined. Setting it to 5 seconds.")
            pconfig['statuscycle'] = 5
        if str(pconfig['topic']) == "":
            log.warning("MQTT Topic is not set. Set it to default topic 'poolmanager'.")
            pconfig['topic'] = "poolmanager"
        global valuecycle
        valuecycle = int(pconfig['valuecycle'])

        # Parse snesors and actors
        for item in pconfig['sensors']:
            devices[item["address"]] = item
        for item in pconfig['actors']:
            devices[item["address"]] = item
        for i in devices:
            nameascii = remove_non_ascii(devices[i]["name"].replace(" ", ""))
            device_list.append(AtlasI2C(address = int(i), moduletype = devices[i]["type"], name = nameascii[:16]))
    except:
        log.critical("Cannot read plugin configuration")
        sys.exit()

def readstatusconfig():
    try:
        with open(lbpdatadir + '/status.json') as f:
            global sconfig
            sconfig = json.load(f)
    except:
        log.critical("Cannot read status configuration")
        sys.exit()

def exit_handler(a="", b=""):
    # Close MQTT
    client.loop_stop()
    log.info("MQTT: Disconnecting from Broker.")
    client.disconnect()
    # close the log
    if str(logdbkey) != "":
        logging.shutdown()
        os.system("perl -e 'use LoxBerry::Log; my $log = LoxBerry::Log->new ( dbkey => \"" + logdbkey + "\", append => 1 ); LOGEND \"Good Bye.\"; $log->close; exit;'")
    else:
        log.info("Good Bye.")
    # End
    sys.exit();

def getstatus():
    log.info("Updating status for all sensors and actors")
    delaytime = device.short_timeout
    # Initial commands
    for dev in device_list:
        if "initial" in sconfig[dev.moduletype]:
            log.info("Initial commands found for device %s" % str(dev.address))
            # Initial values - do not send any data to broker, just configure sensor
            for q in sconfig[dev.moduletype]["initial"].split("++"):
                log.debug("Sending command %s for sensor %s" % (str(q), str(dev.address)))
                try:
                    dev.write(q)
                except:
                    log.error("Could not write to sensor %s." % str(dev.address))
    time.sleep(delaytime)
    # Commands equal for all sensors
    commands = sconfig["all"]
    log.info("Updating status equal for all devices")
    for q in commands:
        for dev in device_list:
            log.debug("Sending command %s for sensor %s" % (str(commands[q]), str(dev.address)))
            try:
                dev.write(commands[q])
            except:
                log.error("Could not write to sensor %s." % str(dev.address))

        time.sleep(delaytime)

        for dev in device_list:
            try:
                response = dev.read().rstrip('\x00').strip()
            except:
                log.error("Could not read from sensor %s." % str(dev.address))
                continue
            values_arr = response.split(": ")[1].split(",")
            origcommand = response.split(": ")[1].split(",")[0]
            #print ("RESPONSE: " )
            #print (response.encode('utf-8'))
            #print ("ORIGNINAL COMMAND: ")
            #print (origcommand.encode('utf-8'))
            address = response.split(": ")[0].split(" ")[2]
            log.debug("Sensor response: %s" % response)
            if response.startswith("Success"):
                found = 0
                for q in commands:
                    if str("?" + commands[q].split(",")[0]).upper().startswith(str(origcommand.upper())):
                        command = q
                        found = 1
                        break
                if found != 1:
                    log.error ("Could not find original command in status.json (%s)" % str(origcommand))
                    continue
                if len(values_arr)-1 is not len(command.split("++")):
                    log.error ("Amount of Topics (%s) not equal to amount of received values (%s)" % (int(len(command.split("++"))), int(len(values_arr))-1))
                    continue
                c = 1
                for t in command.split("++"):
                    client.publish(pretopic + "/" + str(address) + "/status/" + str(t), values_arr[c], retain=1)
                    settimestamp(pretopic + "/" + str(address) + "/status")
                    c += 1

    # Commands individual for each sensors
    log.info("Updating individual status for all devices")
    commandlists = dict()
    commandlists.clear()
    commandlist = list()
    for dev in device_list:
        commandlist.clear()
        if dev.moduletype in sconfig:
            for q in sconfig[dev.moduletype]:
                if q == "initial":
                    continue
                commandlist.append(sconfig[dev.moduletype][q])
            commandlists[dev.address] = commandlist.copy()
        else:
            log.error("Cannot find config for module type %s" % str(dev.moduletype))

    loop = 1
    i = 0
    sends = dict()
    while loop == 1:
        i += 1
        loop = 0
        for dev in device_list:
            if len(commandlists[dev.address]) >= i:
                sends[dev.address] = 1
                loop = 1
                log.debug("Sending command %s for sensor %s" % (str(commandlists[dev.address][i-1]), str(dev.address)))
                try:
                    dev.write(commandlists[dev.address][i-1])
                except:
                    log.error("Could not write to sensor %s." % str(dev.address))
            else:
                sends[dev.address] = 0

        time.sleep(delaytime)

        for dev in device_list:
            if sends[dev.address] == 1:
                try:
                    response = dev.read().rstrip('\x00').strip()
                except:
                    log.error("Could not read from sensor %s." % str(dev.address))
                    continue
                values_arr = response.split(": ")[1].split(",")
                origcommand = response.split(": ")[1].split(",")[0]
                address = response.split(": ")[0].split(" ")[2]
                log.debug("Sensor response: %s" % response)
                if response.startswith("Success"):
                    commands = sconfig[dev.moduletype]
                    found = 0
                    for q in commands:
                        if str("?" + commands[q].split(",")[0]).upper().startswith(str(origcommand.upper())):
                            command = q
                            found = 1
                            break
                    if found != 1:
                        log.error ("Could not find original command in status.json (%s)" % str(origcommand))
                        continue
                    if len(values_arr)-1 is not len(command.split("++")):
                        log.error ("Amount of Topics (%s) not equal to amount of received values (%s)" % (int(len(command.split("++"))), int(len(values_arr))-1))
                        continue
                    c = 1
                    for t in command.split("++"):
                        client.publish(pretopic + "/" + str(address) + "/status/" + str(t), values_arr[c], retain=1)
                        settimestamp(pretopic + "/" + str(address) + "/status")
                        c += 1

def getvalues():

    values_dict = dict()
    delaytime = device.long_timeout
    for dev in device_list:
        log.debug("Get sensor value for sensor %s" % str(dev.address))
        try:
            dev.write("R")
            values_dict[dev.address] = {}
        except:
            log.error("Could not write to sensor %s." % str(dev.address))
    time.sleep(delaytime)
    for dev in device_list:
        try:
            response = dev.read().rstrip('\x00').strip()
        except:
            log.error("Could not read from sensor %s." % str(dev.address))
            continue
        values_arr = response.split(": ")[1].split(",")
        address = response.split(": ")[0].split(" ")[2]
        log.debug("Sensor response: %s" % response)
        if response.startswith("Success"):
            topic = pretopic + "/" + str(dev.address)
            settimestamp(topic)
            i = 0
            for value in values_arr:
                i += 1
                if calibrate == 0:
                    client.publish(topic + "/value" + str(i),value,retain=1)
                    time.sleep(mqttpause)
                values_dict[dev.address]["value"+str(i)] = value
        else:
            log.error("Error updating values for sensor %s. Sensor response: %s" % (str(dev.address), response))
        # Save values also in tmp json for cal and lcd
        log.debug("Saving values to temporary json file for %s" % str(dev.address))
        try:
            with open('/dev/shm/poolmanager-measurements.json', 'w', encoding='utf-8') as f:
                json.dump(values_dict, f, ensure_ascii=False, indent=4)
        except:
            log.error("Could not save values to temporary json file for %s." % str(dev.address))

def setnames():
    for dev in device_list:
        log.info("Set names for all sensors")
        log.debug("Sending command name,%s for sensor %s" % (str(dev.name), str(dev.address)))
        try:
            dev.write("name,"+dev.name)
        except:
            log.error("Could not write to sensor %s." % str(dev.address))

def sendcmd(address, command):
    log.info("Send command %s for sensor %s" % (str(command), str(address)))
    device.set_i2c_address(int(address))
    try:
        response = device.query(str(command))
        log.debug("Sensor response: %s" % response)
    except:
        log.error("An error occurred Query '%s'." % str(command))

    return response.rstrip('\x00').strip()

def settimestamp(topic):
    dt = datetime.now()
    # Loxone Timestamp 01.01.2009
    tsl = 1230764400 
    ts = int(round(datetime.timestamp(dt),0))
    client.publish(topic + "/timestamp",ts,retain=1)
    client.publish(topic + "/timestamp_human",dt.strftime('%Y-%m-%d %H:%M:%S'),retain=1)
    client.publish(topic + "/timestamp_loxone",int(ts)-int(tsl),retain=1)

    return ts

#############################################################################
# Main Script
#############################################################################

# Standard loglevel
loglevel="ERROR"
logfile=""
logdbkey=""

# Get full command-line arguments
# https://stackabuse.com/command-line-arguments-in-python/
full_cmd_arguments = sys.argv
argument_list = full_cmd_arguments[1:]
short_options = "vlfd:"
long_options = ["verbose","loglevel=","logfile=","logdbkey="]

try:
    arguments, values = getopt.getopt(argument_list, short_options, long_options)
except getopt.error as err:
    print (str(err))
    sys.exit(2)

for current_argument, current_value in arguments:
    if current_argument in ("-v", "--verbose"):
        loglevel="DEBUG"
        verbose=1
    elif current_argument in ("-l", "--loglevel"):
        loglevel=current_value
    elif current_argument in ("-f", "--logfile"):
        logfile=current_value
    elif current_argument in ("-d", "--logdbkey"):
        logdbkey=current_value

# Logging with standard LoxBerry log format
numeric_loglevel = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_loglevel, int):
    raise ValueError('Invalid log level: %s' % loglevel)

if str(logfile) == "":
    logfile = str(lbplogdir) + "/" + datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3] + "_atlasi2c-gateway.log"

log = logging.getLogger()
fileHandler = logging.FileHandler(logfile)
formatter = logging.Formatter('%(asctime)s.%(msecs)03d <%(levelname)s> %(message)s',datefmt='%H:%M:%S')

if verbose == 1:
    streamHandler = logging.StreamHandler(sys.stdout)
    streamHandler.setFormatter(formatter)
    log.addHandler(streamHandler)

fileHandler.setFormatter(formatter)
log.addHandler(fileHandler)

# Logging Starting message
log.setLevel(logging.INFO)
log.info("Starting Logfile for atlasi2c-gateway.py. The Loglevel is %s" % loglevel.upper())
log.setLevel(numeric_loglevel)

log.debug("Environment:")
for k, v in os.environ.items():
    log.debug(f'{k}={v}')

# Read MQTT config
mqttconfig = dict()
mqttconfig['server'] = os.popen("perl -e 'use LoxBerry::IO; my $mqttcred = LoxBerry::IO::mqtt_connectiondetails(); print $mqttcred->{brokerhost}; exit'").read()
mqttconfig['port'] = os.popen("perl -e 'use LoxBerry::IO; my $mqttcred = LoxBerry::IO::mqtt_connectiondetails(); print $mqttcred->{brokerport}; exit'").read()
mqttconfig['username'] = os.popen("perl -e 'use LoxBerry::IO; my $mqttcred = LoxBerry::IO::mqtt_connectiondetails(); print $mqttcred->{brokeruser}; exit'").read()
mqttconfig['password'] = os.popen("perl -e 'use LoxBerry::IO; my $mqttcred = LoxBerry::IO::mqtt_connectiondetails(); print $mqttcred->{brokerpass}; exit'").read()

if mqttconfig['server'] == "" or mqttconfig['port'] == "":
    log.critical("Cannot find mqtt configuration")
    sys.exit()

# Read Plugin config
readconfig()
readstatusconfig()

# Conncect to broker
client = mqtt.Client()
client.connected_flag=False
client.on_connect = on_connect

if mqttconfig['username'] and mqttconfig['password']:
    log.info("Using MQTT Username and password.")
    client.username_pw_set(username = mqttconfig['username'],password = mqttconfig['password'])

log.info("Connecting to Broker %s on port %s." % (mqttconfig['server'], str(mqttconfig['port'])))
client.connect(mqttconfig['server'], port = int(mqttconfig['port']))

# Main Topic
pretopic = pconfig['topic']
mqttpause = 0 # Just in Case we need a slow down...

# Subscribe to the set/comand topic
stopic = pretopic + "/set/command"
log.info("Subscribe to: " + stopic)
client.subscribe(stopic, qos=0)
client.on_message = on_message

# Start MQTT Loop
client.loop_start()

# Wait for connection
counter=0
while not client.connected_flag: #wait in loop
    log.info("MQTT: Wait for connection...")
    time.sleep(1)
    counter+=1
    if counter > 60:
        log.critical("MQTT: Cannot connect to Broker %s on port %s." % (mqttconfig['server'], str(mqttconfig['port'])))
        exit()

# Basic needed vars - Part 2
device = AtlasI2C()
client.publish(pretopic + "/plugin/pause",0,retain=1)
client.publish(pretopic + "/plugin/calibration_mode",0,retain=1)

# Exit handler
#atexit.register(exit_handler)
signal.signal(signal.SIGTERM, exit_handler)
signal.signal(signal.SIGINT, exit_handler)

# Loop
while True:

    # Check for any subscribed messages in the queue
    while not q.empty():
        message = q.get()
        response = ""

        if message is None or str(message.payload.decode("utf-8")) == "0":
            continue

        log.info("--> Received command: %s <--" % str(message.payload.decode("utf-8")))
        settimestamp(pretopic + "/set")

        # Check for valid comand
        if ":" in message.payload.decode("utf-8"):
            target = message.payload.decode("utf-8").split(":")[0].lower()
            command = message.payload.decode("utf-8").split(":")[1].lower()

            # COmmands for LCD
            if command.startswith("display"):
                log.error("This command seems to be for lcd_display. I will ingore it. %s" % str(message.payload.decode("utf-8")))
                continue

            # Plugin commands
            if target.startswith("plugin"):
                log.debug("This is a plugin command: %s" % str(command))
                # Stop readings
                if command == "pause":
                    log.info("Pause reading from all sensors and set all sensors to sleep.")
                    client.publish(pretopic + "/plugin/pause",1,retain=1)
                    stop = 1
                    for item in pconfig['sensors']:
                        sendcmd (item['address'],"SLEEP")
                    response = "Success plugin: pause"
                # Start readings
                elif command == "start":
                    log.info("Start reading from all sensors.")
                    client.publish(pretopic + "/plugin/pause",0,retain=1)
                    client.publish(pretopic + "/plugin/calibration_mode",0,retain=1)
                    stop = 0
                    calibrate = 0
                    valuecycle = pconfig['valuecycle']
                    response = "Success plugin: start"
                # Calibrate
                elif command == "calibrate":
                    log.info("Start calibration mode.")
                    client.publish(pretopic + "/plugin/calibration_mode",1,retain=1)
                    client.publish(pretopic + "/plugin/pause",0,retain=1)
                    calibrate = 1
                    stop = 0
                    valuecycle = 1.5
                    response = "Success plugin: calibrate"
                # Read Status
                elif command == "getstatus":
                    log.info("Reading Status for all sensors.")
                    setnames()
                    getstatus()
                    response = "Success plugin: getstatus"
                # Read Values
                elif command == "getvalues":
                    log.info("Reading Values from all sensors.")
                    getvalues()
                    response = "Success plugin: getvalues"
                # Read Config
                elif command == "readconfig":
                    log.info("Re-Reading Config and update status for all sensors.")
                    readconfig()
                    setnames()
                    getstatus()
                    response = "Success plugin: readconfig"
                # Unknown
                else:
                    log.error("Unknown command: I do not know your given command.")
                    response = "Error plugin: Unknown command"
            # Sensor commands
            elif target.isdigit():
                log.debug("This is a sensor command: %s." % str(command))
                found = 0
                for x in devices:
                    if str(x) == str(target):
                        found = 1
                        response = sendcmd(target, command)
                if found != 1:
                    log.error("Unknown target %s: The sensor address is not known or not active." % str(target))
                    response = "Error " + str(target) + " Unknown target: The sensor address is not known or not active."
            # Unknown target
            else:
                log.error("Unknown command: target %s is not 'plugin' or a sensor address." % str(target))
                response = "Error: target is not 'plugin' or a sensor address."
        else:
            log.error("Unknown command. No target given with ':'")
            response = "Error: Unknown command. No target given with ':'."

        # Set status of command queue
        if response != "":
            response = "Command==" + str(message.payload.decode("utf-8")) + "@@Response==" + str (response)
            client.publish(pretopic + "/set/response",str(response),retain=1)
            client.publish(pretopic + "/set/command","0",retain=1)
            client.publish(pretopic + "/set/lastcommand",str(message.payload.decode("utf-8")),retain=1)

    # Getting the current date and time
    now = time.time()
    log.debug("Timestamp: %s Last status: %s (Cycle: %s) Last values: %s (Cycle: %s)" % (str(now), str(laststatus), str(pconfig['statuscycle']), str(lastvalues), str(valuecycle)))

    # Send alive timestamp every 60 seconds
    if now > lastalive + 60:
        lastalive = now
        log.info("Send alive timestamp to broker")
        settimestamp(pretopic + "/plugin")

    # Check if it is time to update the status
    if now > laststatus + int(pconfig['statuscycle']) and stop == 0:
        laststatus = now
        log.info("--> Getting sensor status <--")
        setnames()
        getstatus()

    # Check if it is time to update the values
    if now > lastvalues + int(valuecycle) and stop == 0:
        lastvalues = now
        log.info("--> Getting sensor values <--")
        getvalues()

    # Slow down...
    time.sleep(1)
