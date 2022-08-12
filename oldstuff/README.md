
# Preparing the Raspberry Pi #
### Install the latest Raspberry Pi OS
Follow the instructions on this page to get Raspberry Pi OS running
https://www.raspberrypi.org/downloads/raspberry-pi-os/

### Expand file system
    
Expand file system by following this:
https://www.raspberrypi.org/documentation/configuration/raspi-config.md

### Update and Upgrade Packages 
    
    sudo apt-get update
    sudo apt-get upgrade

# Download sample code.
    
    cd ~
    git clone https://github.com/AtlasScientific/Raspberry-Pi-sample-code.git


# FTDI MODE #

### Installing dependencies for FTDI adaptors ###

- Install libftdi package.

        sudo apt-get install libftdi-dev
    
    
- Install pylibftdi python package.
    
        sudo pip install pylibftdi


- Create SYMLINK of the FTDI adaptors.
    
    The following will allow ordinary users (e.g. ‘pi’ on the RPi) to access to the FTDI device without needing root permissions:
    
    If you are using device with root permission, just skip this step. 
    
    Create udev rule file by typing `sudo nano /etc/udev/rules.d/99-libftdi.rules` and insert below:
    
        SUBSYSTEMS=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6015", GROUP="dialout", MODE="0660", SYMLINK+="FTDISerial_Converter_$attr{serial}"

    Press CTRL+X, Y and hit Enter to save & exit.
    
    Restart `udev` service to apply changes above.
        
        sudo service udev restart


- Modify FTDI python driver
    
    Since our FTDI devices use other USB PID(0x6015), we need to tweak the original FTDI Driver.
    
        sudo nano /usr/local/lib/python2.7/dist-packages/pylibftdi/driver.py
    
    Move down to the line 70 and add `0x6015` at the end of line.

    Original line:
        
        USB_PID_LIST = [0x6001, 0x6010, 0x6011, 0x6014]
        
    Added line:
            
        USB_PID_LIST = [0x6001, 0x6010, 0x6011, 0x6014, 0x6015]        
        
        
- Testing Installation.

    Connect your device, and run the following (as a regular user):
        
        python -m pylibftdi.examples.list_devices
   
    If all goes well, the program should report information about each connected device. 

    If no information is printed, but it is when run with sudo, 
    a possibility is permissions problems - see the section under Linux above regarding udev rules.
    
    You may get result like this:
        
        FTDI:FT230X Basic UART:DA00TN73
    
    FTDI adaptors has its own unique serial number.

    We need this to work with our sensors.

    In the result above, serial number is `DA00TN73`.
    
### Using pylibftdi module for Atlas Sensors. ###
    
Please remember the serial number of your device and run the sample code.
    
    cd ~/Raspberry-Pi-sample-code
    sudo python ftdi.py
    
Input the serial number and you can see the sensor's information and also sensor's LED status as well.
 
For more details on the commands & responses, please refer the Datasheets of Atlas Sensors. 


# I2C MODE #

### Enable I2C bus on the Raspberry Pi ###

Enable I2C bus on the Raspberry Pi by following this:

https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c

You can confirm that the setup worked and sensors are present with the `sudo i2cdetect -y 1` command.

### Test Sensor ###
    
Run the sample code below:
    
    cd ~/Raspberry-Pi-sample-code
    sudo python i2c.py

When the code starts up a list of commands will be shown.

For more details on the commands & responses, please refer to the Datasheets of the Atlas Scientific Sensors.


   
# UART MODE #

### Preventing Raspberry Pi from using the serial port ###

The Broadcom UART appears as `/dev/ttyS0` under Linux on every Pi. The Pi 4 has additional UARTS, see below for instruction on how to use them

There are several minor things in the way if you want to have dedicated control of the primary serial port on a Raspberry Pi.

- Firstly, the kernel will use the port as controlled by kernel command line contained in `/boot/cmdline.txt`. 
    
    The file will look something like this:

        dwc_otg.lpm_enable=0 console=ttyAMA0,115200 kgdboc=ttyAMA0,115200 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline rootwait

    The console keyword outputs messages during boot, and the kgdboc keyword enables kernel debugging. 

    You will need to remove all references to ttyAMA0.
    
    So, for the example above `/boot/cmdline.txt`, should contain:

        dwc_otg.lpm_enable=0 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline rootwait
    
    You must be root to edit this (e.g. use `sudo nano /boot/cmdline.txt`). 

    Be careful doing this, as a faulty command line can prevent the system booting.

- Secondly, after booting, a login prompt appears on the serial port. 
    
    This is controlled by the following lines in `/etc/inittab`:
        
        #Spawn a getty on Raspberry Pi serial line
        T0:23:respawn:/sbin/getty -L ttyAMA0 115200 vt100
    
    You will need to edit this file to comment out the second line, i.e.
    
        #T0:23:respawn:/sbin/getty -L ttyAMA0 115200 vt100
        
- Finally you will need to reboot the Raspberry Pi for the new settings to take effect. 
    
    Once this is done, you can use `/dev/ttyS0` like any normal Linux serial port, and you won't get any unwanted traffic confusing the attached devices.
    
To double-check, use

    cat /proc/cmdline
    
to show the current kernel command line, and
    
    ps aux | grep ttyS0

to search for getty processes using the serial port.


### Ensure PySerial is installed for Python. ###

    sudo pip install pyserial
    
### Run the below Python script:
    
    cd ~/Raspberry-Pi-sample-code
    sudo python uart.py
    
### Alternate UARTS on Pi4:

The raspberry pi 4 has 6 uarts

To demonstrate alternate UART usage, we're going to enable UART 5
Note that other UARTs share their pins with other peripherals, so those peripherals may have to be disabled to use them

UART 5 uses pins 32 (TX) and 33 (RX) on the raspberry pi 40 pin header

Go into the boot configuration 

    sudo nano /boot/config.txt 

and add the lines

    enable_uart=1
    dtoverlay=uart5

then restart the raspberry pi

To use this port in the uart sample code `uart.py` change line 70 to:

    usbport = '/dev/ttyAMA1'
 
Note that it may be a different ttyAMA depending on your setup

