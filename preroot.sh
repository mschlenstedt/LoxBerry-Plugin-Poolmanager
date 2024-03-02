#!/bin/bash

ARGV0=$0 # Zero argument is shell command
ARGV1=$1 # First argument is temp folder during install
ARGV2=$2 # Second argument is Plugin-Name for scipts etc.
ARGV3=$3 # Third argument is Plugin installation folder
ARGV4=$4 # Forth argument is Plugin version
ARGV5=$5 # Fifth argument is Base folder of LoxBerry

echo "<INFO> Adding LoxBerry User to i2c group"
usermod -a -G i2c loxberry

echo "<INFO> Installing Adafruit LCD Display library"
yes | python3 -m pip install adafruit-circuitpython-charlcd
INSTALLED=$(python3 -m pip list --format=columns | grep -i "adafruit-circuitpython-charlcd" | grep -v grep | wc -l)
if [ ${INSTALLED} -ne "0" ]; then
	echo "<OK>  Adafruit LCD Display library installed successfully."
else
	echo "<FAIL>  Adafruit LCD Display library could not be installed."
	exit 2;
fi

# Exit with Status 0
exit 0
