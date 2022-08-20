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
#from Queue import Queue
from queue import Queue

# Basic needed vars - Part 1
q=Queue()
verbose=0
laststatus = 0
lastvalues = 0
lastalive = 0
stop = 0
devices = dict()
device_list = list()
pconfig = dict()
sconfig = dict()
mqttconfig = dict()

lbpconfigdir = os.popen("perl -e 'use LoxBerry::System; print $lbpconfigdir; exit;'").read()
lbpdatadir = os.popen("perl -e 'use LoxBerry::System; print $lbpdatadir; exit;'").read()
lbplogdir = os.popen("perl -e 'use LoxBerry::System; print $lbplogdir; exit;'").read()

#############################################################################
# Atlas Scientific Lib functions
#############################################################################

class AtlasI2C:

    # the timeout needed to query readings and calibrations
    LONG_TIMEOUT = 1.5
    # timeout for regular commands
    SHORT_TIMEOUT = 0.5
    # the default bus for I2C on the newer Raspberry Pis, 
    # certain older boards use bus 0
    DEFAULT_BUS = 1
    # the default address for the sensor
    DEFAULT_ADDRESS = 98
    LONG_TIMEOUT_COMMANDS = ("R", "CAL")
    SLEEP_COMMANDS = ("SLEEP", )

    def __init__(self, address=None, moduletype = "", name = "", bus=None):
        '''
        open two file streams, one for reading and one for writing
        the specific I2C channel is selected with bus
        it is usually 1, except for older revisions where its 0
        wb and rb indicate binary read and write
        '''
        self._address = address or self.DEFAULT_ADDRESS
        self.bus = bus or self.DEFAULT_BUS
        self._long_timeout = self.LONG_TIMEOUT
        self._short_timeout = self.SHORT_TIMEOUT
        self.file_read = io.open(file="/dev/i2c-{}".format(self.bus), 
                                 mode="rb", 
                                 buffering=0)
        self.file_write = io.open(file="/dev/i2c-{}".format(self.bus),
                                  mode="wb", 
                                  buffering=0)
        self.set_i2c_address(self._address)
        self._name = name
        self._module = moduletype

	
    @property
    def long_timeout(self):
        return self._long_timeout

    @property
    def short_timeout(self):
        return self._short_timeout

    @property
    def name(self):
        return self._name
        
    @property
    def address(self):
        return self._address
        
    @property
    def moduletype(self):
        return self._module
        
        
    def set_i2c_address(self, addr):
        '''
        set the I2C communications to the slave specified by the address
        the commands for I2C dev using the ioctl functions are specified in
        the i2c-dev.h file from i2c-tools
        '''
        I2C_SLAVE = 0x703
        fcntl.ioctl(self.file_read, I2C_SLAVE, addr)
        fcntl.ioctl(self.file_write, I2C_SLAVE, addr)
        self._address = addr

    def write(self, cmd):
        '''
        appends the null character and sends the string over I2C
        '''
        cmd += "\00"
        self.file_write.write(cmd.encode('latin-1'))

    def handle_raspi_glitch(self, response):
        '''
        Change MSB to 0 for all received characters except the first 
        and get a list of characters
        NOTE: having to change the MSB to 0 is a glitch in the raspberry pi, 
        and you shouldn't have to do this!
        '''
        if self.app_using_python_two():
            return list(map(lambda x: chr(ord(x) & ~0x80), list(response)))
        else:
            return list(map(lambda x: chr(x & ~0x80), list(response)))
            
    def app_using_python_two(self):
        return sys.version_info[0] < 3

    def get_response(self, raw_data):
        if self.app_using_python_two():
            response = [i for i in raw_data if i != '\x00']
        else:
            response = raw_data

        return response

    def response_valid(self, response):
        valid = True
        error_code = None
        if(len(response) > 0):
            
            if self.app_using_python_two():
                error_code = str(ord(response[0]))
            else:
                error_code = str(response[0])
                
            if error_code != '1': #1:
                valid = False

        return valid, error_code

    def get_device_info(self):
        if(self._name == ""):
            return self._module + " " + str(self.address)
        else:
            return self._module + " " + str(self.address) + " " + self._name
        
    def read(self, num_of_bytes=31):
        '''
        reads a specified number of bytes from I2C, then parses and displays the result
        '''
        
        raw_data = self.file_read.read(num_of_bytes)
        response = self.get_response(raw_data=raw_data)
        is_valid, error_code = self.response_valid(response=response)

        if is_valid:
            char_list = self.handle_raspi_glitch(response[1:])
            result = "Success " + self.get_device_info() + ": " +  str(''.join(char_list))
        else:
            result = "Error " + self.get_device_info() + ": " + error_code

        return result

    def get_command_timeout(self, command):
        timeout = None
        if command.upper().startswith(self.LONG_TIMEOUT_COMMANDS):
            timeout = self._long_timeout
        elif not command.upper().startswith(self.SLEEP_COMMANDS):
            timeout = self.short_timeout

        return timeout

    def query(self, command):
        '''
        write a command to the board, wait the correct timeout, 
        and read the response
        '''
        self.write(command)
        current_timeout = self.get_command_timeout(command=command)
        if not current_timeout:
            return "sleep mode"
        else:
            time.sleep(current_timeout)
            return self.read()

    def close(self):
        self.file_read.close()
        self.file_write.close()

    def list_i2c_devices(self):
        '''
        save the current address so we can restore it after
        '''
        prev_addr = copy.deepcopy(self._address)
        i2c_devices = []
        for i in range(0, 128):
            try:
                self.set_i2c_address(i)
                self.read(1)
                i2c_devices.append(i)
            except IOError:
                pass
        # restore the address we were using
        self.set_i2c_address(prev_addr)

        return i2c_devices

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
                dev.write(q)
    time.sleep(delaytime)
    # Commands equal for all sensors
    commands = sconfig["all"]
    log.info("Updating status equal for all devices")
    for q in commands:
        for dev in device_list:
            log.debug("Sending command %s for sensor %s" % (str(commands[q]), str(dev.address)))
            dev.write(commands[q])

        time.sleep(delaytime)

        for dev in device_list:
            response = dev.read().rstrip('\x00').strip()
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
                dev.write(commandlists[dev.address][i-1])
            else:
                sends[dev.address] = 0
                
        time.sleep(delaytime)

        for dev in device_list:
            if sends[dev.address] == 1:
                response = dev.read().rstrip('\x00').strip()
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
    
    delaytime = device.long_timeout
    for dev in device_list:
        log.debug("Get sensor value for sensor %s" % str(dev.address))
        dev.write("R")
    time.sleep(delaytime)
    for dev in device_list:
        response = dev.read().rstrip('\x00').strip()
        values_arr = response.split(": ")[1].split(",")
        address = response.split(": ")[0].split(" ")[2]
        log.debug("Sensor response: %s" % response)
        if response.startswith("Success"):
            topic = pretopic + "/" + str(dev.address)
            settimestamp(topic)
            i = 0
            for value in values_arr:
                i += 1
                client.publish(topic + "/value" + str(i),value,retain=1)
                time.sleep(mqttpause)
        else:
            log.error("Error updating values for sensor %s. Sensor response: %s" % (str(dev.address), response))

def setnames():
    for dev in device_list:
        log.info("Set names for all sensors")
        log.debug("Sending command %s for sensor %s" % (str(dev.name), str(dev.address)))
        dev.write("name,"+dev.name)

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
log.info("Starting Logfile for acsensors.py. The Loglevel is %s" % loglevel.upper())
log.setLevel(numeric_loglevel)

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

# Exit handler
#atexit.register(exit_handler)
signal.signal(signal.SIGTERM, exit_handler)
signal.signal(signal.SIGINT, exit_handler)

# Loop
while True:

    # Check for any subscribed messages in the queue
    while not q.empty():
        message = q.get()
        if message is None or str(message.payload.decode("utf-8")) == "0":
            continue

        log.info("--> Received command: %s <--" % str(message.payload.decode("utf-8")))
        settimestamp(pretopic + "/set")

        # Check for valid comand
        if ":" in message.payload.decode("utf-8"):
            target = message.payload.decode("utf-8").split(":")[0].lower()
            command = message.payload.decode("utf-8").split(":")[1].lower()
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
                    stop = 0
                    response = "Success plugin: start"
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
        response = "Command==" + str(message.payload.decode("utf-8")) + "@@Response==" + str (response)
        client.publish(pretopic + "/set/response",str(response),retain=1)
        client.publish(pretopic + "/set/command","0",retain=1)
        client.publish(pretopic + "/set/lastcommand",str(message.payload.decode("utf-8")),retain=1)

    # Getting the current date and time
    now = time.time()
    log.debug("Timestamp: %s Last status: %s (Cycle: %s) Last values: %s (Cycle: %s)" % (str(now), str(laststatus), str(pconfig['statuscycle']), str(lastvalues), str(pconfig['valuecycle'])))

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
    if now > lastvalues + int(pconfig['valuecycle']) and stop == 0:
        lastvalues = now
        log.info("--> Getting sensor values <--")
        getvalues()

    # Slow down...
    time.sleep(1)
