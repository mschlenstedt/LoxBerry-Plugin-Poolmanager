#!/usr/bin/perl
use warnings;
use strict;
use LoxBerry::System;
use CGI;
use JSON;
#use LoxBerry::Log;
#use Data::Dumper;

my $error;
my $response;
my $cgi = CGI->new;
my $q = $cgi->Vars;

#print STDERR Dumper $q;

#my $log = LoxBerry::Log->new (
#    name => 'AJAX',
#	stderr => 1,
#	loglevel => 7
#);

#LOGSTART "Request $q->{action}";

if( $q->{action} eq "servicerestart" ) {
	# We have to start in background mode because watchdog uses fork
	system ("$lbpbindir/watchdog.pl --action=restart --verbose=0 > /dev/null 2>&1 &");
	my $resp = $?;
	sleep(1);
	my $status = LoxBerry::System::lock(lockfile => 'poolmanager-watchdog', wait => 600); # Wait until watchdog is ready...
	$response = $resp;
}

if( $q->{action} eq "servicestop" ) {
	system ("$lbpbindir/watchdog.pl --action=stop --verbose=1 > /dev/null 2>&1");
	$response = $?;
}

if( $q->{action} eq "servicestatus" ) {
	my $status;
	my $count = `pgrep -c -f "python3 $lbpbindir/atlasi2c-gateway.py"`;
	if ($count >= "2") {
		$status = `pgrep -o -f "python3 $lbpbindir/atlasi2c-gateway.py"`;
	}
	my %response = (
		pid => $status,
	);
	chomp (%response);
	$response = encode_json( \%response );
}

if( $q->{action} eq "getconfig" ) {
	# From https://gist.github.com/theimpostor/79d4d37876aa990edd2ebc0e1d9391b5
	require Hash::Merge;
	Hash::Merge->import("merge");
	my $merged = {};
	my $json = JSON->new->utf8;
	if ( -e "$lbpconfigdir/plugin.json" ) {
		$merged = merge( $merged, $json->decode( LoxBerry::System::read_file("$lbpconfigdir/plugin.json") ) );
	}
	if ( -e "$lbpdatadir/calibration.json" ) {
		$merged = merge( $merged, $json->decode( LoxBerry::System::read_file("$lbpdatadir/calibration.json") ) );
	}
	if( !$merged ) {
		$response = "{ }";
	} else {
		$response = $json->encode( $merged );
	}
}

if( $q->{action} eq "getvalues" ) {
	if ( -e "/dev/shm/poolmanager-measurements.json" ) {
		$response = LoxBerry::System::read_file("/dev/shm/poolmanager-measurements.json");
		if( !$response ) {
			$response = "{ }";
		}
	}
	else {
		$response = "{ }";
	}
}

if( $q->{action} eq "addsensor" ) {

	# Check if all required parameters are defined
	if (!defined $q->{'name'} || $q->{'name'} eq "") {
		$error = "Name cannot be empty";
	}
	if (!defined $q->{'type'} || $q->{'type'} eq "") {
		$error = "Type cannot be empty";
	}
	if (!defined $q->{'address'} || $q->{'address'} eq "") {
		$error = "Address cannot be empty";
	}

	# Load config
	require LoxBerry::JSON;
	my $cfgfile = "$lbpconfigdir/plugin.json";
	my $jsonobj = LoxBerry::JSON->new();
	my $cfg = $jsonobj->open(filename => $cfgfile);
	# Check if name already exists
	if ( !$q->{'edit'} && $q->{'name'} ) {
		my @searchresult = $jsonobj->find( $cfg->{'sensors'}, "\$_->{'name'} eq \"" . $q->{'name'} . "\"" );
		#my $elemKey = $searchresult[0];
		if (scalar(@searchresult) > 0) {
			$error = "Name '" . $q->{'name'} . "' already exists. Names must be unique.";
		}
	}
	# Edit existing output
	if (!$error && $q->{'edit'}) {
		my @searchresult = $jsonobj->find( $cfg->{'sensors'}, "\$_->{'name'} eq \"" . $q->{'edit'} . "\"" );
		my $elemKey = $searchresult[0];
		splice @{ $cfg->{'sensors'} }, $elemKey, 1 if (defined($elemKey));
	}
	# Add new/edited output
	if (!$error) {
		# Required
		my %sensor = (
			name => $q->{'name'},
			type => $q->{'type'},
			address => $q->{'address'}
		);
		# Optional
		$sensor{'calibrate'} = $q->{'cal'} > 0 ? $q->{'cal'} : "0";
		$sensor{'cal_low'} = $q->{'callow'} ne "" ? $q->{'callow'} : "";
		$sensor{'cal_mid'} = $q->{'calmid'} ne "" ? $q->{'calmid'} : "";
		$sensor{'cal_high'} = $q->{'calhigh'} ne "" ? $q->{'calhigh'} : "";
		$sensor{'lcd'} = $q->{'lcd'} > 0 ? $q->{'lcd'} : "0";
		$sensor{'lcd_unit'} = $q->{'lcdunit'} ne "" ? $q->{'lcdunit'} : "";
		$sensor{'lcd_value'} = $q->{'lcdvalue'} ne "" ? $q->{'lcdvalue'} : "VALUE1";

		# Save
		push @{$cfg->{'sensors'}}, \%sensor;
		$jsonobj->write();
	}
	$response = encode_json( $cfg );
	
}

if( $q->{action} eq "deletesensor" ) {

	# Check if all required parameters are defined
	if (!defined $q->{'name'} || $q->{'name'} eq "") {
		$error = "Name cannot be empty";
	}

	# Load config
	require LoxBerry::JSON;
	my $cfgfile = "$lbpconfigdir/plugin.json";
	my $jsonobj = LoxBerry::JSON->new();
	my $cfg = $jsonobj->open(filename => $cfgfile);
	# Delete existing output
	my @searchresult = $jsonobj->find( $cfg->{'sensors'}, "\$_->{'name'} eq \"" . $q->{'name'} . "\"" );
	my $elemKey = $searchresult[0];
	splice @{ $cfg->{'sensors'} }, $elemKey, 1 if (defined($elemKey));
	$jsonobj->write();
	$response = encode_json( $cfg );
	
}

if( $q->{action} eq "addactor" ) {

	# Check if all required parameters are defined
	if (!defined $q->{'name'} || $q->{'name'} eq "") {
		$error = "Name cannot be empty";
	}
	if (!defined $q->{'type'} || $q->{'type'} eq "") {
		$error = "Type cannot be empty";
	}
	if (!defined $q->{'address'} || $q->{'address'} eq "") {
		$error = "Address cannot be empty";
	}

	# Load config
	require LoxBerry::JSON;
	my $cfgfile = "$lbpconfigdir/plugin.json";
	my $jsonobj = LoxBerry::JSON->new();
	my $cfg = $jsonobj->open(filename => $cfgfile);
	# Check if name already exists
	if ( !$q->{'edit'} && $q->{'name'} ) {
		my @searchresult = $jsonobj->find( $cfg->{'actors'}, "\$_->{'name'} eq \"" . $q->{'name'} . "\"" );
		#my $elemKey = $searchresult[0];
		if (scalar(@searchresult) > 0) {
			$error = "Name '" . $q->{'name'} . "' already exists. Names must be unique.";
		}
	}
	# Edit existing output
	if (!$error && $q->{'edit'}) {
		my @searchresult = $jsonobj->find( $cfg->{'actors'}, "\$_->{'name'} eq \"" . $q->{'edit'} . "\"" );
		my $elemKey = $searchresult[0];
		splice @{ $cfg->{'actors'} }, $elemKey, 1 if (defined($elemKey));
	}
	# Add new/edited output
	if (!$error) {
		# Required
		my %actor = (
			name => $q->{'name'},
			type => $q->{'type'},
			address => $q->{'address'}
		);
		# Optional
		$actor{'calibrate'} = $q->{'cal'} > 0 ? $q->{'cal'} : "0";
		$actor{'cal_low'} = $q->{'callow'} ne "" ? $q->{'callow'} : "";
		$actor{'cal_mid'} = $q->{'calmid'} ne "" ? $q->{'calmid'} : "";
		$actor{'cal_high'} = $q->{'calhigh'} ne "" ? $q->{'calhigh'} : "";
		$actor{'lcd'} = $q->{'lcd'} > 0 ? $q->{'lcd'} : "0";
		$actor{'lcd_unit'} = $q->{'lcdunit'} ne "" ? $q->{'lcdunit'} : "";
		$actor{'lcd_value'} = $q->{'lcdvalue'} ne "" ? $q->{'lcdvalue'} : "VALUE1";

		# Save
		push @{$cfg->{'actors'}}, \%actor;
		$jsonobj->write();
	}
	$response = encode_json( $cfg );
	
}

if( $q->{action} eq "deleteactor" ) {

	# Check if all required parameters are defined
	if (!defined $q->{'name'} || $q->{'name'} eq "") {
		$error = "Name cannot be empty";
	}

	# Load config
	require LoxBerry::JSON;
	my $cfgfile = "$lbpconfigdir/plugin.json";
	my $jsonobj = LoxBerry::JSON->new();
	my $cfg = $jsonobj->open(filename => $cfgfile);
	# Delete existing output
	my @searchresult = $jsonobj->find( $cfg->{'actors'}, "\$_->{'name'} eq \"" . $q->{'name'} . "\"" );
	my $elemKey = $searchresult[0];
	splice @{ $cfg->{'actors'} }, $elemKey, 1 if (defined($elemKey));
	$jsonobj->write();
	$response = encode_json( $cfg );
	
}

if( $q->{action} eq "savesettings" ) {

	# Check if all required parameters are defined
	if (!defined $q->{'topic'} || $q->{'topic'} eq "") {
		$q->{'topic'} = "poolmanager";
	}
	if (!defined $q->{'valuecycle'} || $q->{'valuecycle'} eq "") {
		$q->{'valuecycle'} = "5";
	}
	if (!defined $q->{'statuscycle'} || $q->{'statuscycle'} eq "") {
		$q->{'statuscycle'} = "300";
	}

	# Load config
	require LoxBerry::JSON;
	my $cfgfile = "$lbpconfigdir/plugin.json";
	my $jsonobj = LoxBerry::JSON->new();
	my $cfg = $jsonobj->open(filename => $cfgfile);
	
	# Save
	$cfg->{'topic'} = $q->{'topic'};
	$cfg->{'valuecycle'} = $q->{'valuecycle'};
	$cfg->{'statuscycle'} = $q->{'statuscycle'};
	$jsonobj->write();

	$response = encode_json( $cfg );
	
}

if( $q->{action} eq "savelcd" ) {

	# Check if all required parameters are defined
	if (!defined $q->{'cycletime'} || $q->{'cycletime'} eq "") {
		$q->{'cycletime'} = "3";
	}
	if (!defined $q->{'displaytimeout'} || $q->{'displaytimeout'} eq "") {
		$q->{'displaytimeout'} = "180";
	}

	# Load config
	require LoxBerry::JSON;
	my $cfgfile = "$lbpconfigdir/plugin.json";
	my $jsonobj = LoxBerry::JSON->new();
	my $cfg = $jsonobj->open(filename => $cfgfile);
	
	# Save
	if ($cfg->{'lcd'} == "1") { # This is from old configs - reもove old settings for compatibility
		undef($cfg->{'lcd'});
	}
	$cfg->{'lcd'}->{'active'} = $q->{'active'} > 0 ? $q->{'active'} : "0";;
	$cfg->{'lcd'}->{'cycletime'} = $q->{'cycletime'};
	$cfg->{'lcd'}->{'displaytimeout'} = $q->{'displaytimeout'};
	$cfg->{'lcd'}->{'external_values'} = [];
	for (my $i = 0; $i <= 4; $i++) {
		my $v = $i + 1;
		my %ev = (
			address => "value$v",
			name => $q->{'value' . $v . 'name'},
			lcd_unit => $q->{'value' . $v . 'unit'},
		);
		push @{$cfg->{'lcd'}->{'external_values'}}, \%ev;
	}
	$jsonobj->write();

	$response = encode_json( $cfg );
	
}

if( $q->{action} eq "sendcommand" ) {

	if (!defined $q->{'command'} || $q->{'command'} eq "") {
		$error = "Command cannot be empty";
	}

	if (!$error) {
		require LoxBerry::JSON;
		require LoxBerry::IO;
		my $cfgfile = "$lbpconfigdir/plugin.json";
		my $jsonobj = LoxBerry::JSON->new();
		my $cfg = $jsonobj->open(filename => $cfgfile);

		$cfg->{'topic'} = "poolmanager" if !$cfg->{'topic'};
		my $return = LoxBerry::IO::mqtt_publish( $cfg->{'topic'} . "/set/command", $q->{'command'} );
		my %response = (
			message => $return,
		);
		chomp (%response);
		$response = encode_json( \%response );
	}

}

#####################################
# Manage Response and error
#####################################

if( defined $response and !defined $error ) {
	print "Status: 200 OK\r\n";
	print "Content-type: application/json; charset=utf-8\r\n\r\n";
	print $response;
	#LOGOK "Parameters ok - responding with HTTP 200";
}
elsif ( defined $error and $error ne "" ) {
	print "Status: 500 Internal Server Error\r\n";
	print "Content-type: application/json; charset=utf-8\r\n\r\n";
	print to_json( { error => $error } );
	#LOGCRIT "$error - responding with HTTP 500";
}
else {
	print "Status: 501 Not implemented\r\n";
	print "Content-type: application/json; charset=utf-8\r\n\r\n";
	$error = "Action ".$q->{action}." unknown";
	#LOGCRIT "Method not implemented - responding with HTTP 501";
	print to_json( { error => $error } );
}

END {
	#LOGEND if($log);
}
