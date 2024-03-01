#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import time
import string
import paho.mqtt.client as mqtt
import json
import logging
import os
from datetime import datetime
import getopt
import signal
from queue import Queue
import board
from adafruit_character_lcd.character_lcd_rgb_i2c import Character_LCD_RGB_I2C

#############################################################################
# Global vars
#############################################################################

q=Queue()
verbose=0
devices = dict()
pconfig = dict()
measurements = dict()
mqttconfig = dict()
now=time.time()
lastaction=now
last=0
cyclemode=1
singlevaluemode=1
calibrationmode=0
displaytimeout=120
cycletime=3
lastactiontimeout=30
display=1
i=0

lbpconfigdir = os.popen("perl -e 'use LoxBerry::System; print $lbpconfigdir; exit;'").read()
lbpdatadir = os.popen("perl -e 'use LoxBerry::System; print $lbpdatadir; exit;'").read()
lbplogdir = os.popen("perl -e 'use LoxBerry::System; print $lbplogdir; exit;'").read()
pluginversion = os.popen("perl -e 'use LoxBerry::System; my $version = LoxBerry::System::pluginversion(); print $version; exit;'").read()

menu_s1 = dict = {
    '0':{
        "name":"Calibration",
        "do":"calibration"
    },
    '1':{
        "name":"Exit",
        "do":"exit"
    },
}

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
# LCD functions
#############################################################################

def display_off():
    lcd.display = False
    lcd.backlight = False
    lcd.color = (0, 0, 0)
    global display
    display = 0
    return()

def display_on():
    lcd.display = True
    lcd.backlight = True
    lcd.color = (100, 100, 100)
    global display
    display = 1
    return()

def show_measurement(i):
    if display < 1:
        return(0)
    lcdname = remove_non_ascii(devices[list(devices.keys())[i]]["name"])
    lcdunit = remove_non_ascii(devices[list(devices.keys())[i]]["lcd_unit"])
    if devices[list(devices.keys())[i]]["address"] in measurements:
        lcdvalue = measurements[devices[list(devices.keys())[i]]["address"]][devices[list(devices.keys())[i]]["lcd_value"]]
    else:
        lcdvalue = "NA"
    lcd.clear()
    if lcdunit:
        lcd.message = lcdname + "\n" + lcdvalue + " " + lcdunit
    else:
        lcd.message = lcdname + "\n" + lcdvalue
    return(1)

#############################################################################
# Plugin Lib functions
#############################################################################

def remove_non_ascii(string):
    return ''.join(char for char in string if ord(char) < 128)

def readconfig():
    try:
        with open(lbpconfigdir + '/plugin.json') as f:
            global pconfig
            global devices
            global displaytimeout
            global cycletime
            global pretopic
            global totaldevices
            pconfig = json.load(f)
        # Main Topic
        pretopic = pconfig['topic']
        # Times
        displaytimeout = int(pconfig['lcd']['displaytimeout'])
        cycletime = int(pconfig['lcd']['cycletime'])
        # Parse snesors and actors
        for item in pconfig['sensors']:
            if int(item["lcd"]) > 0:
                devices[item["address"]] = item
        for item in pconfig['actors']:
            if int(item["lcd"]) > 0:
                devices[item["address"]] = item
        for item in pconfig['lcd']['external_values']:
            if item["name"]:
                devices[item["address"]] = item
                item["calibrate"] = "0"
                item["lcd"] = "1"
                item["external"] = "1"
                item["lcd_value"] = "value"
        totaldevices = len(devices) - 1
        log.debug("Devices: " + str(devices))
    except:
        log.critical("Cannot read plugin configuration")
        sys.exit()

def readmeasurements():
    try:
        counter=0
        mfile = '/dev/shm/poolmanager-measurements.json'
        while not os.path.isfile(mfile): #wait in loop
            log.info("Wait for measurements file from atlasi2c-gateway...")
            time.sleep(1)
            counter+=1
            if counter > 60:
                log.critical("Measurements file does not exist. Maybe a problem with the gateway. I will exist now. %s." % mfile)
                exit()
        with open('/dev/shm/poolmanager-measurements.json') as f:
            global measurements
            measurements = json.load(f)
    except:
        log.critical("Cannot read measurements")
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
    # Turn backlight off
    display = 0
    display_off()
    lcd.clear()
    # End
    sys.exit();

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
    logfile = str(lbplogdir) + "/" + datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3] + "_lcd_display.log"

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
log.info("Starting Logfile for lcd_display.py. The Loglevel is %s" % loglevel.upper())
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

# Read Plugin config
readconfig()
readmeasurements()

# Ecit if LCD Display is not enabled
if int(pconfig["lcd"]["active"]) < 1:
    log.info("LCD Display is not enabled. Exiting now.")
    sys.exit()

# Conncect to broker
client = mqtt.Client()
client.connected_flag=False
client.on_connect = on_connect

if mqttconfig['username'] and mqttconfig['password']:
    log.info("Using MQTT Username and password.")
    client.username_pw_set(username = mqttconfig['username'],password = mqttconfig['password'])

log.info("Connecting to Broker %s on port %s." % (mqttconfig['server'], str(mqttconfig['port'])))
client.connect(mqttconfig['server'], port = int(mqttconfig['port']))

# Subscriptions for PoolManager measurements
for y in devices:
    if devices[y]["address"].isdigit():
        topic = pretopic + "/" + devices[y]["address"] + "/" + devices[y]["lcd_value"]
        log.info("Subscribe to: " + topic)
        client.subscribe(topic, qos=0)
        client.on_message = on_message

# Subscriptions for External measurements
add_values = pconfig['lcd']['external_values']
for ev in add_values:
    if ev["name"]:
        topic = pretopic + "/lcd/" + ev["address"]
        client.publish(topic + "/name", ev["name"], retain=1)
        client.publish(topic + "/lcd_unit", ev["lcd_unit"], retain=1)
        log.info("Subscribe to: " + topic + "/value")
        client.subscribe(topic + "/value", qos=0)
        client.on_message = on_message

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

# Start MQTT Loop
client.loop_start()

# Exit handler
#atexit.register(exit_handler)
signal.signal(signal.SIGTERM, exit_handler)
signal.signal(signal.SIGINT, exit_handler)

# LCD Init
i2c = board.I2C()  # uses board.SCL and board.SDA
lcd = Character_LCD_RGB_I2C(i2c, 16, 2)

lcd.clear()
display_on()
lcd.message = "PoolManager\nVersion " + pluginversion
time.sleep(int(cycletime))
lcd.clear()

# Loop
while True:

    # Check for any subscribed messages in the queue

    while not q.empty():
        message = q.get()
        response = ""

        log.debug("Received subscription: " + str(message.topic) + " " + str(message.payload.decode("utf-8")))

        if message is None or str(message.payload.decode("utf-8")) == "0":
            continue

        # New measurement for external or internal value
        if "value" in message.topic:
            log.debug("Received measurement: " + str(message.topic) + " " + str(message.payload.decode("utf-8")))
            x = str(message.topic).replace(pconfig["topic"] + "/", "").replace("lcd/", "").split("/")
            measurements[x[0]] = { x[1] : str(message.payload.decode("utf-8")) }
            log.debug("Measurements: " + str(measurements))

        # Check for valid command
        elif ":" in message.payload.decode("utf-8"):
            log.info("--> Received command: %s <--" % str(message.payload.decode("utf-8")))
            target = message.payload.decode("utf-8").split(":")[0].lower()
            command = message.payload.decode("utf-8").split(":")[1].lower()
            # Plugin commands
            if target.startswith("plugin") and command.startswith("display"):
                log.debug("This is a plugin command: %s" % str(command))
                # Display on
                if command == "display_on":
                    log.info("Turn display on and keep it on.")
                    display_on()
                    displaytimeout=0
                    response = "Success plugin: display_on"
                # Display off
                elif command == "display_off":
                    log.info("Turn display off.")
                    display_off()
                    displaytimeout = int(pconfig['lcd']['displaytimeout'])
                    response = "Success plugin: display_off"
                # Display Auto
                elif command == "display_auto":
                    log.info("Turn display into auto mode.")
                    display_on()
                    displaytimeout = int(pconfig['lcd']['displaytimeout'])
                    response = "Success plugin: display_auto"
                else:
                    log.error("Unknown command: I do not know your given command.")
                    response = "Error plugin: Unknown command"
            else:
                log.error("This command seems to be for atlasi2c-gateway. I will ingore it. %s" % str(message.payload.decode("utf-8")))
        else:
            log.error("Unknown command. No target given with ':'. %s" % str(message.payload.decode("utf-8")))

        # Set status of command queue
        if response != "":
            response = "Command==" + str(message.payload.decode("utf-8")) + "@@Response==" + str (response)
            client.publish(pretopic + "/set/response",str(response),retain=1)
            client.publish(pretopic + "/set/command","0",retain=1)
            client.publish(pretopic + "/set/lastcommand",str(message.payload.decode("utf-8")),retain=1)

    # Main program

    if i > totaldevices:
        i = 0

    now = time.time()

    # Turn display off after timeout
    if now > lastaction + displaytimeout and cyclemode and displaytimeout > 0:
        display_off()

    # If not in Cycle Mode and not in Calibration Mode and Timeout reached, return to Cycle Mode
    if now > lastaction + lastactiontimeout and not cyclemode and not calibrationmode:
        lastaction = now
        cyclemode = 1
        singlevaluemode = 0

    # Update Display in Cylce Mode
    if now > last + cycletime and cyclemode:
        show_measurement(i)
        last = now
        i += 1

    if lcd.left_button:
        time.sleep(0.3)
        log.debug("Left Button pressed!")
        lastaction = now
        if cyclemode and display == 0:
            display_on()
        elif cyclemode and display == 1:
            last = now
            cyclemode = 0
            singlevaluemode = 1
        elif singlevaluemode:
            i -= 1
            if i > totaldevices:
                i = 0
            if i < 0:
                i = totaldevices
            show_measurement(i)
        else:
            pass

    elif lcd.up_button:
        time.sleep(0.3)
        log.debug("Up Button pressed!")
        lastaction = now
        if cyclemode and display == 0:
            display_on()

    elif lcd.down_button:
        time.sleep(0.3)
        log.debug("Down Button pressed!")
        lastaction = now
        if cyclemode and display == 0:
            display_on()

    elif lcd.right_button:
        time.sleep(0.3)
        log.debug("Right Button pressed!")
        lastaction = now
        if cyclemode and display == 0:
            display_on()
        elif cyclemode and display == 1:
            last = now
            cyclemode = 0
            singlevaluemode = 1
        elif singlevaluemode:
            i += 1
            if i > totaldevices:
                i = 0
            if i < 0:
                i = totaldevices
            show_measurement(i)
        else:
            pass

    elif lcd.select_button:
        time.sleep(0.3)
        log.debug("Select Button pressed!")
        lastaction = now
        if cyclemode and display == 0:
            display_on()
            continue

    else:
        time.sleep(0.1)
