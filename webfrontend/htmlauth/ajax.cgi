#!/usr/bin/perl
use warnings;
use strict;
use LoxBerry::System;
use LoxBerry::Log;
use CGI;
use JSON;
use Data::Dumper;

my $error;
my $response;
my $cgi = CGI->new;
my $q = $cgi->Vars;

print STDERR Dumper $q;

my $log = LoxBerry::Log->new (
    name => 'AJAX',
	stderr => 1,
	loglevel => 7
);

LOGSTART "Request $q->{action}";


if( $q->{action} eq "servicerestart" ) {
	system ("$lbpbindir/watchdog.pl --action=restart --verbose=1 > /dev/null 2>&1");
	$response = $?;
}

if( $q->{action} eq "servicestatus" ) {
	my $status;
	my $count = `pgrep -c -f "python3 -m mqtt_io /dev/shm/mqttio.yaml"`;
	if ($count >= "2") {
		$status = `pgrep -o -f "python3 -m mqtt_io /dev/shm/mqttio.yaml"`;
	}
	my %response = (
		pid => $status,
	);
	chomp (%response);
	$response = encode_json( \%response );
}

if( $q->{action} eq "getconfig" ) {
	if ( -e "$lbpconfigdir/mqttio.json" ) {
		$response = LoxBerry::System::read_file("$lbpconfigdir/mqttio.json");
		if( !$response ) {
			$response = "{ }";
		}
	}
	else {
		$response = "{ }";
	}
}

if( $q->{action} eq "gpiomodule" ) {

	# Check if all required parameters are defined
	if (!defined $q->{'name'} || $q->{'name'} eq "") {
		$error = "Name cannot be empty";
	}
	if (!defined $q->{'module'} || $q->{'module'} eq "") {
		$error = "Module cannot be empty";
	}

	# Load config
	require LoxBerry::JSON;
	my $cfgfile = "$lbpconfigdir/mqttio.json";
	my $jsonobj = LoxBerry::JSON->new();
	my $cfg = $jsonobj->open(filename => $cfgfile);
	# Check if name already exists
	if ( !$q->{'edit'} && $q->{'name'} ) {
		my @searchresult = $jsonobj->find( $cfg->{'gpio_modules'}, "\$_->{'name'} eq \"" . $q->{'name'} . "\"" );
		#my $elemKey = $searchresult[0];
		if (scalar(@searchresult) > 0) {
			$error = "Name '" . $q->{'name'} . "' already exists. Names must be unique.";
		}
	}
	
	# Edit existing  module
	if (!$error && $q->{'edit'}) {
		my @searchresult = $jsonobj->find( $cfg->{'gpio_modules'}, "\$_->{'name'} eq \"" . $q->{'edit'} . "\"" );
		my $elemKey = $searchresult[0];
		splice @{ $cfg->{'gpio_modules'} }, $elemKey, 1 if (defined($elemKey));
		# Edit all digital outputs and inputs
		my @searchresult = $jsonobj->find( $cfg->{'digital_outputs'}, "\$_->{'module'} eq \"" . $q->{'edit'} . "\"" );
		foreach $elemKey (@searchresult) {
			$cfg->{'digital_outputs'}->[$elemKey]->{'module'} = $q->{'name'};
		}
	}
	
	# Add new/eddited module
	if (!$error) {
		# Required
		my %module = (
			name => $q->{'name'},
			module => $q->{'module'},
		);
		# Optional
		$module{'i2c_bus_num'} = $q->{'i2c_bus_num'} if ($q->{'i2c_bus_num'});
		$module{'chipaddr'} = $q->{'chipaddr'} if ($q->{'chipaddr'});
		# Save
		push @{$cfg->{'gpio_modules'}}, \%module;
		$jsonobj->write();
	}
	$response = encode_json( $cfg );
	
}

if( $q->{action} eq "deletegpiomodule" ) {

	# Check if all required parameters are defined
	if (!defined $q->{'name'} || $q->{'name'} eq "") {
		$error = "Name cannot be empty";
	}

	# Load config
	require LoxBerry::JSON;
	my $cfgfile = "$lbpconfigdir/mqttio.json";
	my $jsonobj = LoxBerry::JSON->new();
	my $cfg = $jsonobj->open(filename => $cfgfile);
	# Delete existing  module
	my @searchresult = $jsonobj->find( $cfg->{'gpio_modules'}, "\$_->{'name'} eq \"" . $q->{'name'} . "\"" );
	my $elemKey = $searchresult[0];
	splice @{ $cfg->{'gpio_modules'} }, $elemKey, 1 if (defined($elemKey));
	# Delete all digital outputs and inputs
	@searchresult = $jsonobj->find( $cfg->{'digital_outputs'}, "\$_->{'module'} eq \"" . $q->{'name'} . "\"" );
	for my $elemKey (reverse sort @searchresult) {
		splice @{ $cfg->{'digital_outputs'} }, $elemKey, 1 if (defined($elemKey));
	}
	@searchresult = $jsonobj->find( $cfg->{'digital_inputs'}, "\$_->{'module'} eq \"" . $q->{'name'} . "\"" );
	for my $elemKey (reverse sort @searchresult) {
		splice @{ $cfg->{'digital_inputs'} }, $elemKey, 1 if (defined($elemKey));
	}
	$jsonobj->write();
	$response = encode_json( $cfg );
	
}

if( $q->{action} eq "digitaloutput" ) {

	# Check if all required parameters are defined
	if (!defined $q->{'name'} || $q->{'name'} eq "") {
		$error = "Name cannot be empty";
	}
	if (!defined $q->{'module'} || $q->{'module'} eq "") {
		$error = "Module cannot be empty";
	}
	if (!defined $q->{'pin'} || $q->{'pin'} eq "") {
		$error = "Pin cannot be empty";
	}

	# Load config
	require LoxBerry::JSON;
	my $cfgfile = "$lbpconfigdir/mqttio.json";
	my $jsonobj = LoxBerry::JSON->new();
	my $cfg = $jsonobj->open(filename => $cfgfile);
	# Check if name already exists
	if ( !$q->{'edit'} && $q->{'name'} ) {
		my @searchresult = $jsonobj->find( $cfg->{'digital_outputs'}, "\$_->{'name'} eq \"" . $q->{'name'} . "\"" );
		#my $elemKey = $searchresult[0];
		if (scalar(@searchresult) > 0) {
			$error = "Name '" . $q->{'name'} . "' already exists. Names must be unique.";
		}
	}
	# Edit existing output
	if (!$error && $q->{'edit'}) {
		my @searchresult = $jsonobj->find( $cfg->{'digital_outputs'}, "\$_->{'name'} eq \"" . $q->{'edit'} . "\"" );
		my $elemKey = $searchresult[0];
		splice @{ $cfg->{'digital_outputs'} }, $elemKey, 1 if (defined($elemKey));
	}
	# Add new/edited output
	if (!$error) {
		# Required
		my %digitaloutput = (
			name => $q->{'name'},
			module => $q->{'module'},
			pin => $q->{'pin'},
			retain => 'true',
			publish_initial => 'true',
		);
		# Optional
		$digitaloutput{'timed_ms'} = $q->{'timed_ms'} if ($q->{'timed_ms'} > 0);
		$digitaloutput{'initial'} = $q->{'initial'} if ($q->{'initial'});
		$digitaloutput{'payload_on'} = $q->{'payload_on'} ne "ON" ? $q->{'payload_on'} : "ON";
		$digitaloutput{'payload_off'} = $q->{'payload_off'} ne "OFF" ? $q->{'payload_off'} : "OFF";
		$digitaloutput{'inverted'} = $q->{'inverted'};

		# Save
		push @{$cfg->{'digital_outputs'}}, \%digitaloutput;
		$jsonobj->write();
	}
	$response = encode_json( $cfg );
	
}

if( $q->{action} eq "deletedigitaloutput" ) {

	# Check if all required parameters are defined
	if (!defined $q->{'name'} || $q->{'name'} eq "") {
		$error = "Name cannot be empty";
	}

	# Load config
	require LoxBerry::JSON;
	my $cfgfile = "$lbpconfigdir/mqttio.json";
	my $jsonobj = LoxBerry::JSON->new();
	my $cfg = $jsonobj->open(filename => $cfgfile);
	# Delete existing output
	my @searchresult = $jsonobj->find( $cfg->{'digital_outputs'}, "\$_->{'name'} eq \"" . $q->{'name'} . "\"" );
	my $elemKey = $searchresult[0];
	splice @{ $cfg->{'digital_outputs'} }, $elemKey, 1 if (defined($elemKey));
	$jsonobj->write();
	$response = encode_json( $cfg );
	
}











#####################################
# Manage Response and error
#####################################

if( defined $response and !defined $error ) {
	print "Status: 200 OK\r\n";
	print "Content-type: application/json; charset=utf-8\r\n\r\n";
	print $response;
	LOGOK "Parameters ok - responding with HTTP 200";
}
elsif ( defined $error and $error ne "" ) {
	print "Status: 500 Internal Server Error\r\n";
	print "Content-type: application/json; charset=utf-8\r\n\r\n";
	print to_json( { error => $error } );
	LOGCRIT "$error - responding with HTTP 500";
}
else {
	print "Status: 501 Not implemented\r\n";
	print "Content-type: application/json; charset=utf-8\r\n\r\n";
	$error = "Action ".$q->{action}." unknown";
	LOGCRIT "Method not implemented - responding with HTTP 501";
	print to_json( { error => $error } );
}

END {
	LOGEND if($log);
}
