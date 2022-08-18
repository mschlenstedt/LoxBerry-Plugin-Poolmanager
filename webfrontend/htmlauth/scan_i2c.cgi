#!/usr/bin/perl

# Copyright 2018-2020 Michael Schlenstedt, michael@loxberry.de
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
use LoxBerry::System;
use LoxBerry::Web;
use warnings;
use strict;

##########################################################################
# Main program
##########################################################################

my $version = LoxBerry::System::pluginversion();

my $maintemplate = HTML::Template->new(
		filename => "$lbptemplatedir/scan_i2c.html",
		global_vars => 1,
		loop_context_vars => 1,
		die_on_bad_params=> 0,
		# associate => $cfg,
		%htmltemplate_options,
		# debug => 1,
		);
	
%L = LoxBerry::System::readlanguage($maintemplate, "language.ini");

# Prrepare Template
LoxBerry::Web::lbheader($L{'COMMON.LABEL_PLUGINTITLE'} . " V$version", "nopanels", "");

my @html;
my $buslist = "";
my $busses = 0;
for (my $i=0; $i < 10; $i++) {
	if ( -e "/dev/i2c-$i" ) {
		$buslist .= $busses eq "0" ? "i2c-$i" : ", i2c-$i";
		$busses++;
		my %html;
		my ($rc, $output) = execute( command => "i2cdetect -y $i" );
		if ($rc eq "0") {
			$html{'BUS'} = $i;
			$html{'OUTPUT'} = $output;
		}
		push (@html, \%html);
	}
}

$maintemplate->param( BUSLIST => $buslist );
$maintemplate->param( BUSSCANS => \@html );

# Output Template
print $maintemplate->output();
exit;
