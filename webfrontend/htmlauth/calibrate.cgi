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
use CGI;
use warnings;
use strict;

##########################################################################
# Main program
##########################################################################

# Read Form
my $cgi = CGI->new;
my $q = $cgi->Vars;

my $version = LoxBerry::System::pluginversion();

# Template
my $template = LoxBerry::System::read_file("$lbptemplatedir/calibrate.html");
$template .= LoxBerry::System::read_file("$lbptemplatedir/javascript.js"); # Add JS Scripts

my $maintemplate = HTML::Template->new_scalar_ref(
	\$template,
	global_vars => 1,
	loop_context_vars => 1,
	die_on_bad_params => 0,
);

%L = LoxBerry::System::readlanguage($maintemplate, "language.ini");

# Prrepare Template
LoxBerry::Web::lbheader($L{'COMMON.LABEL_PLUGINTITLE'} . " V$version", "nopanels", "");

# Set template vars
$maintemplate->param( ADDRESS => $q->{address} );
$maintemplate->param( CALIBRATE => "1" );

# Output Template
print $maintemplate->output();

exit;
