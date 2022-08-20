#!/usr/bin/perl

# Copyright 2019 Michael Schlenstedt, michael@loxberry.de
#                Christian Fenzl, christian@loxberry.de
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


##########################################################################
# Modules
##########################################################################

# use Config::Simple '-strict';
# use CGI::Carp qw(fatalsToBrowser);
use CGI;
use LoxBerry::System;
#use LoxBerry::Web;
use LoxBerry::JSON; # Available with LoxBerry 2.0
#require "$lbpbindir/libs/LoxBerry/JSON.pm";
use LoxBerry::Log;
#use Time::HiRes qw ( sleep );
use warnings;
use strict;
#use Data::Dumper;

##########################################################################
# Variables
##########################################################################

my $log;

# Read Form
my $cgi = CGI->new;
my $q = $cgi->Vars;

my $version = LoxBerry::System::pluginversion();
my $template;
my $templateout;

# Language Phrases
my %L;

##########################################################################
# AJAX
##########################################################################

if( $q->{ajax} ) {
	
	## Handle all ajax requests 
	require JSON;
	# require Time::HiRes;
	my %response;
	ajax_header();

	exit;

##########################################################################
# Normal request (not AJAX)
##########################################################################

} else {
	
	require LoxBerry::Web;
	
	# Default is gpio_settings form
	$q->{form} = "atlas" if !$q->{form};

	if ($q->{form} eq "calibration") {
		my $templatefile = "$lbptemplatedir/calibration_settings.html";
		$template = LoxBerry::System::read_file($templatefile);
		&form_calibration();
	}
	elsif ($q->{form} eq "logs") {
		my $templatefile = "$lbptemplatedir/log_settings.html";
		$template = LoxBerry::System::read_file($templatefile);
		&form_logs();
	}
	elsif ($q->{form} eq "lcd") {
		my $templatefile = "$lbptemplatedir/lcd_settings.html";
		$template = LoxBerry::System::read_file($templatefile);
		&form_lcd();
	}
	elsif ($q->{form} eq "settings") {
		my $templatefile = "$lbptemplatedir/general_settings.html";
		$template = LoxBerry::System::read_file($templatefile);
		&form_settings();
	}
	else {
		my $templatefile = "$lbptemplatedir/atlas_settings.html";
		$template = LoxBerry::System::read_file($templatefile);
		&form_atlas();
       	}
	
}

# Print the form out
&printtemplate();

exit;

##########################################################################
# Form: Atlas
##########################################################################

sub form_atlas
{
	# Prepare template
	&preparetemplate();

	return();
}

##########################################################################
# Form: Calibration
##########################################################################

sub form_calibration
{
	# Prepare template
	&preparetemplate();

	return();
}


##########################################################################
# Form: LCD
##########################################################################

sub form_lcd
{
	# Prepare template
	&preparetemplate();

	return();
}


##########################################################################
# Form: Settings
##########################################################################

sub form_settings
{
	# Prepare template
	&preparetemplate();

	return();
}


##########################################################################
# Form: Log
##########################################################################

sub form_logs
{

	# Prepare template
	&preparetemplate();

	$templateout->param("LOGLIST", LoxBerry::Web::loglist_html());

	return();
}

##########################################################################
# Print Form
##########################################################################

sub preparetemplate
{

	# Add JS Scripts
	my $templatefile = "$lbptemplatedir/javascript.js";
	$template .= LoxBerry::System::read_file($templatefile);

	$templateout = HTML::Template->new_scalar_ref(
		\$template,
		global_vars => 1,
		loop_context_vars => 1,
		die_on_bad_params => 0,
	);

	# Language File
	%L = LoxBerry::System::readlanguage($templateout, "language.ini");
	
	# Navbar
	our %navbar;

	$navbar{10}{Name} = "$L{'COMMON.LABEL_ATLAS'}";
	$navbar{10}{URL} = 'index.cgi?form=atlas';
	$navbar{10}{active} = 1 if $q->{form} eq "atlas";
	
	$navbar{20}{Name} = "$L{'COMMON.LABEL_CALIBRATION'}";
	$navbar{20}{URL} = 'index.cgi?form=calibration';
	$navbar{20}{active} = 1 if $q->{form} eq "calibration";

	$navbar{30}{Name} = "$L{'COMMON.LABEL_LCD'}";
	$navbar{30}{URL} = 'index.cgi?form=lcd';
	$navbar{30}{active} = 1 if $q->{form} eq "lcd";
	
	$navbar{40}{Name} = "$L{'COMMON.LABEL_SETTINGS'}";
	$navbar{40}{URL} = 'index.cgi?form=settings';
	$navbar{40}{active} = 1 if $q->{form} eq "settings";
	
	$navbar{98}{Name} = "$L{'COMMON.LABEL_LOGS'}";
	$navbar{98}{URL} = 'index.cgi?form=logs';
	$navbar{98}{active} = 1 if $q->{form} eq "logs";

	return();
}

sub printtemplate
{

	# Print out Template
	LoxBerry::Web::lbheader($L{'COMMON.LABEL_PLUGINTITLE'} . " V$version", "https://loxwiki.atlassian.net/wiki/spaces/LOXBERRY/pages/1254687237/LoxPoolManager", "");
	# Print your plugins notifications with name daemon.
	print LoxBerry::Log::get_notifications_html($lbpplugindir, 'PoolManager');
	print $templateout->output();
	LoxBerry::Web::lbfooter();
	
	return();

}

######################################################################
# AJAX functions
######################################################################

sub ajax_header
{
	print $cgi->header(
			-type => 'application/json',
			-charset => 'utf-8',
			-status => '200 OK',
	);	
}	
