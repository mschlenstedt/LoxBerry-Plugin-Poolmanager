#!/usr/bin/python

import io
import sys
import fcntl
import time
import copy
import string
import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime
import getopt

class AtlasI2C:

    # the timeout needed to query readings and calibrations
    LONG_TIMEOUT = 1.5
    # timeout for regular commands
    SHORT_TIMEOUT = .3
    # the default bus for I2C on the newer Raspberry Pis, 
    # certain older boards use bus 0
    DEFAULT_BUS = 1
    # the default address for the sensor
    DEFAULT_ADDRESS = 99
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
        #print(response)
        is_valid, error_code = self.response_valid(response=response)

        if is_valid:
            char_list = self.handle_raspi_glitch(response[1:])
            result = "Success" + self.get_device_info() + ": " +  str(''.join(char_list))
            #result = "Success: " +  str(''.join(char_list))
        else:
            result = "Error: " + self.get_device_info() + ": " + error_code

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

def get_devices():
    device = AtlasI2C()
    device_address_list = device.list_i2c_devices()
    device_list = []

    for i in device_address_list:
        device.set_i2c_address(i)
        try:
            response = device.query("I")
            moduletype = response.split(",")[1]
            response = device.query("name,?").split(",")[1]
            device_list.append(AtlasI2C(address = i, moduletype = moduletype, name = response))
        except:
            continue
    return device_list

def on_connect(client, userdata, flags, rc):
    if rc==0:
        client.connected_flag=True #set flag
        log.info("MQTT: Connected OK")
    else:
        log.critical("MQTT: Bad connection, Returned code=",rc)

def getstatus(address):
    log.info("Get sensor status data for sensor %s" % str(address))
    device.set_i2c_address(address)
    try:
        log.debug("Sending Query 'I' to Sensor %s" % str(address))
        response = device.query("I")
        log.debug("Sensor response: %s" % response)
        moduletype = response.split(",")[1]
        firmware = response.split(",")[2]
        topic = pretopic + "/" + moduletype + "/" + str(address) + "/status"
        client.publish(topic + "/MODULETYPE",moduletype)
        time.sleep(mqttpause)
        client.publish(topic + "/FIRMWARE",firmware)
        time.sleep(mqttpause)
    except:
        log.error("An error occurred Query 'I'.")
        return
    try:
        log.debug("Sending Query 'name,?' to Sensor %s" % str(address))
        response = device.query("name,?")
        log.debug("Sensor response: %s" % response)
        name = response.split(",")[1]
        client.publish(topic + "/NAME",name)
        time.sleep(mqttpause)
    except:
        log.error("An error occurred Query 'name,?'.")
    try:
        log.debug("Sending Query 'T,?' to Sensor %s" % str(address))
        response = device.query("T,?")
        log.debug("Sensor response: %s" % response)
        comptemp = response.split(",")[1]
        client.publish(topic + "/COMPENSATETEMP",comptemp)
        time.sleep(mqttpause)
    except:
        log.error("An error occurred Query 'T,?'.")
    try:
        log.debug("Sending Query 'Status' to Sensor %s" % str(address))
        response = device.query("Status")
        log.debug("Sensor response: %s" % response)
        rebootreason = response.split(",")[1]
        voltage = response.split(",")[2]
        client.publish(topic + "/VOLTAGE",voltage)
        time.sleep(mqttpause)
        client.publish(topic + "/LASTREBOOTREASON",rebootreason)
        time.sleep(mqttpause)
    except:
        log.error("An error occurred Query 'Status'.")
    try:
        log.debug("Sending Query 'Slope,?' to Sensor %s" % str(address))
        response = device.query("slope,?")
        log.debug("Sensor response: %s" % response)
        slopeacid = response.split(",")[1]
        slopebase = response.split(",")[2]
        slopezero = response.split(",")[3]
        client.publish(topic + "/SLOPEACID",slopeacid)
        time.sleep(mqttpause)
        client.publish(topic + "/SLOPEBASE",slopebase)
        time.sleep(mqttpause)
        client.publish(topic + "/SLOPEZERO",slopezero)
        time.sleep(mqttpause)
    except:
        log.error("An error occurred Query 'Slope,?'.")
    try:
        log.debug("Sending Query 'pHext,?' to Sensor %s" % str(address))
        response = device.query("pHext,?")
        log.debug("Sensor response: %s" % response)
        phext = response.split(",")[1]
        client.publish(topic + "/PHEXT",phext)
        time.sleep(mqttpause)
    except:
        log.error("An error occurred Query 'pHext,?'.")
    #if response.startswith("Success"):
    #    try:
    #        floatVal = float(response.split(",")[1])
    #        print("OK [" + str(floatVal) + "]")
    #        return floatVal
    #    except:
    #        return 0.0
    #else:

# Standard loglevel
loglevel="ERROR"

# Get full command-line arguments
# https://stackabuse.com/command-line-arguments-in-python/
full_cmd_arguments = sys.argv
argument_list = full_cmd_arguments[1:]
short_options = "vl:"
long_options = ["verbose","loglevel="]
try:
    arguments, values = getopt.getopt(argument_list, short_options, long_options)
except getopt.error as err:
    print (str(err))
    sys.exit(2)
for current_argument, current_value in arguments:
    if current_argument in ("-v", "--verbose"):
        loglevel="DEBUG"
    elif current_argument in ("-l", "--loglevel"):
        loglevel=current_value

# Logging with standard LoxBerry log format
numeric_loglevel = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_loglevel, int):
    raise ValueError('Invalid log level: %s' % loglevel)
logfile=datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]+"_acsensors.log"
logging.basicConfig(filename=logfile,level=numeric_loglevel,format='%(asctime)s.%(msecs)03d <%(levelname)s> %(message)s',datefmt='%H:%M:%S')
log = logging.getLogger("acsensors.py")

# Logging Starting message
log.setLevel(logging.INFO)
log.info("Starting Logfile for acsensors.py. The Loglevel is %s" % loglevel.upper())
log.setLevel(numeric_loglevel)

# Read MQTT config
try:
    with open('mqtt.json') as f:
        mqttconfig = json.load(f)
except:
    log.critical("Cannot find mqtt configuration")
    exit()

# Conncect to broker
client = mqtt.Client()
client.connected_flag=False
client.on_connect = on_connect

if mqttconfig['username'] and mqttconfig['password']:
    log.info("Using MQTT Username and password.")
    client.username_pw_set(username = mqttconfig['username'],password = mqttconfig['password'])

log.info("Connecting to Broker %s on port %s." % (mqttconfig['server'], str(mqttconfig['port'])))
client.connect(mqttconfig['server'], port = int(mqttconfig['port']))
pretopic = mqttconfig['topic']
mqttpause = 0.2

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

device = AtlasI2C()
getstatus(99)

print (device.query("R") )

# End MQTT connection
client.loop_stop()
log.info("MQTT: Disconnecting from Broker.")
client.disconnect()


