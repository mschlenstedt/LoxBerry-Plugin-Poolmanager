#!/usr/bin/perl

use LoxBerry::System;
use LoxBerry::IO;
use LoxBerry::Log;
use LoxBerry::JSON;
use Getopt::Long;
#use warnings;
#use strict;
use Data::Dumper;

# Version of this script
my $version = "0.1.0";

# Globals
my $error;
my $verbose;
my $action;

# Logging
my $log = LoxBerry::Log->new (  name => "watchdog",
	package => 'poolmanager',
	logdir => "$lbplogdir",
	addtime => 1,
);

# Commandline options
GetOptions ('verbose=s' => \$verbose,
            'action=s' => \$action);

# Verbose
if ($verbose) {
        $log->stdout(1);
        $log->loglevel(7);
}

# Language File
my %L = LoxBerry::System::readlanguage("language.ini");

LOGSTART "Starting Watchdog";

# Lock
my $status = LoxBerry::System::lock(lockfile => 'poolmanager-watchdog', wait => 10);
if ($status) {
	LOGCRIT "$status currently running - Quitting.";
	exit (1);
}

# Creating tmp file with failed checks
my $response;
if (!-e "/dev/shm/poolmanager-watchdog-fails.dat") {
	$response = LoxBerry::System::write_file("/dev/shm/poolmanager-watchdog-fails.dat", "0");
}

# Check for installed MQTT Plugin
$mqtt = LoxBerry::IO::mqtt_connectiondetails();
if ( !defined(mqtt) ) {
	my $fails = LoxBerry::System::read_file("/dev/shm/poolmanager-watchdog-fails.dat");
	if ($fails < 9) {
		notify ( $lbpplugindir, "PoolManager", $L{'COMMON.ERROR_MQTTGATEWAY'}, 1);
		my $response = LoxBerry::System::write_file("/dev/shm/poolmanager-watchdog-fails.dat", "10");
	}
}

# Todo
if ( $action eq "start" ) {

	&start();

}

elsif ( $action eq "stop" ) {

	&stop();

}

elsif ( $action eq "restart" ) {

	&restart();

}

elsif ( $action eq "check" ) {

	&check();

}

else {

	LOGERR "No valid action specified. action=start|stop|restart|check is required. Exiting.";
	print "No valid action specified. action=start|stop|restart|check is required. Exiting.\n";
	exit(1);

}

exit (0);


#############################################################################
# Sub routines
#############################################################################

##
## Start
##
sub start
{

	unlink ("/dev/shm/poolmanager-watchdog-stop.dat");

	$log->default;
	my $count = `pgrep -c -f "python3 $lbpbindir/atlasi2c-gateway.py"`;
	chomp ($count);
	$count--; # Perl itself runs pgrep with sh, which also match -f in pgrep
	if ($count > "0") {
		LOGCRIT "Poolmanager already running. Please stop it before starting again. Exiting.";
		exit (1);
	}

	# Logfile
	my $poolmanagerlog = LoxBerry::Log->new (  name => "atlasi2c-gateway",
		package => 'poolmanager',
		logdir => "$lbplogdir",
		addtime => 1,
	);
	if ($verbose) {
		$poolmanagerlog->loglevel(7);
	}
	my $logfile = $poolmanagerlog->filename();

	# Loglevel
	my $loglevel = "INFO";
	$loglevel = "CRITICAL" if ($log->loglevel() <= 2);
	$loglevel = "ERROR" if ($log->loglevel() eq 3);
	$loglevel = "WARNING" if ($log->loglevel() eq 4 || $log->loglevel() eq 5);
	$loglevel = "DEBUG" if ($log->loglevel() eq 6 || $log->loglevel() eq 7);

	LOGINF "Starting PoolManager (atlasi2c-gateway)...";

	$poolmanagerlog->default;
	LOGSTART "Starting PoolManager (atlasi2c-gateway)...";
	my $dbkey = $poolmanagerlog->dbkey;
	system ("python3 $lbpbindir/atlasi2c-gateway.py --logfile=$logfile --loglevel=$loglevel --logdbkey=$dbkey >> $logfile 2>&1 &");
	#system ("python3 $lbpbindir/atlasi2c-gateway.py --logfile=$logfile --loglevel=$loglevel --logdbkey=$dbkey --verbose >> /tmp/templogfile.log 2>&1 &");
	sleep 2;

	my $count = `pgrep -c -f "python3 $lbpbindir/atlasi2c-gateway.py"`;
	chomp ($count);
	$count--; # Perl itself runs pgrep with sh, which also match -f in pgrep
	$log->default;
	if ($count eq "0") {
		LOGCRIT "Could not start PoolManager. Error: $?";
		exit (1)
	} else {
		my $status = `pgrep -o -f "python3 $lbpbindir/atlasi2c-gateway.py"`;
		chomp ($status);
		LOGOK "PoolManager started successfully. Running PID: $status";
	}

	return (0);

}

sub stop
{

	$response = LoxBerry::System::write_file("/dev/shm/poolmanager-watchdog-stop.dat", "1");

	$log->default;
	LOGINF "Stopping PoolManager (atlasi2c-gateway)...";
	system ("pkill -f 'python3 $lbpbindir/atlasi2c-gateway.py' > /dev/null 2>&1");
	sleep 2;

	my $count = `pgrep -c -f "python3 $lbpbindir/atlasi2c-gateway.py"`;
	chomp ($count);
	$count--; # Perl `` itself runs pgrep with sh, which also match -f in pgrep
	if ($count eq "0") {
		LOGOK "PoolManager stopped successfully.";
	} else {
		my $status = `pgrep -o -f "python3 $lbpbindir/atlasi2c-gateway.py"`;
		chomp ($status);
		LOGCRIT "Could not stop PoolManager. Running PID: $status";
		exit (1)
	}

	return(0);

}

sub restart
{

	$log->default;
	LOGINF "Restarting PoolManager...";
	&stop();
	sleep (2);
	&start();

	return(0);

}

sub check
{

	$log->default;
	LOGINF "Checking Status of PoolManager...";
	
	my $count = `pgrep -c -f "python3 $lbpbindir/atlasi2c-gateway.py"`;
	chomp ($count);
	$count--; # Perl `` itself runs pgrep with sh, which also match -f in pgrep
	if ($count eq "0") {
		LOGERR "PoolManager seems not to be running.";
		my $fails = LoxBerry::System::read_file("/dev/shm/poolmanager-watchdog-fails.dat");
		chomp ($fails);
		$fails++;
		my $response = LoxBerry::System::write_file("/dev/shm/poolmanager-watchdog-fails.dat", "$fails");
		if ($fails > 9) {
			LOGERR "Too many failures. Will stop watchdogging... Check your configuration and start service manually.";
		} else {
			&restart();
		}
	} else {
		my $status = `pgrep -o -f "python3 $lbpbindir/atlasi2c-gateway.py"`;
		chomp ($status);
		LOGOK "PoolManager is running. Fine. Running PID: $status";
		my $response = LoxBerry::System::write_file("/dev/shm/poolmanager-watchdog-fails.dat", "0");
	}

	return(0);

}
