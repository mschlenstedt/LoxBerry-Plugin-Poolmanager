<script>

$(function() {
	
	if (document.getElementById("servicestatus")) {
		interval = window.setInterval(function(){ servicestatus(); }, 5000);
	}
	if (document.getElementById("calibration_overview") || document.getElementById("calibration")) {
		intervalm = window.setInterval(function(){ measurements(); }, 1000);
	}
	servicestatus();
	getconfig();

});

// SERVICE STATE

function servicestatus(update) {

	if (update) {
		$("#servicestatus").attr("style", "background:#dfdfdf").html("<TMPL_VAR "COMMON.HINT_UPDATING">");
		$("#servicestatusicon").html("<img src='./images/unknown_20.png'>");
	}

	$.ajax( { 
			url:  'ajax.cgi',
			type: 'POST',
			data: { 
				action: 'servicestatus'
			}
		} )
	.fail(function( data ) {
		console.log( "Servicestatus Fail", data );
		$("#servicestatus").attr("style", "background:#dfdfdf; color:red").html("<TMPL_VAR "COMMON.HINT_FAILED">");
		$("#servicestatusicon").html("<img src='./images/unknown_20.png'>");
	})
	.done(function( data ) {
		console.log( "Servicestatus Success", data );
		if (data.pid) {
			$("#servicestatus").attr("style", "background:#6dac20; color:black").html("<TMPL_VAR "COMMON.HINT_RUNNING"> <span class='small'>PID: " + data.pid + "</span>");
			$("#servicestatusicon").html("<img src='./images/check_20.png'>");
		} else {
			$("#servicestatus").attr("style", "background:#FF6339; color:black").html("<TMPL_VAR "COMMON.HINT_STOPPED">");
			$("#servicestatusicon").html("<img src='./images/error_20.png'>");
		}
	})
	.always(function( data ) {
		console.log( "Servicestatus Finished", data );
	});
}

// SERVICE RESTART

function servicerestart() {

	clearInterval(interval);
	$("#servicestatus").attr("style", "color:blue").html("<TMPL_VAR "COMMON.HINT_EXECUTING">");
	$("#servicestatusicon").html("<img src='./images/unknown_20.png'>");
	$.ajax( { 
			url:  'ajax.cgi',
			type: 'POST',
			data: { 
				action: 'servicerestart'
			}
		} )
	.fail(function( data ) {
		console.log( "Servicerestart Fail", data );
	})
	.done(function( data ) {
		console.log( "Servicerestart Success", data );
		if (data == "0") {
			servicestatus(1);
		} else {
			$("#servicestatus").attr("style", "background:#dfdfdf; color:red").html("<TMPL_VAR "COMMON.HINT_FAILED">");
		}
		interval = window.setInterval(function(){ servicestatus(); }, 5000);
	})
	.always(function( data ) {
		console.log( "Servicerestart Finished", data );
	});
}

// SERVICE STOP

function servicestop() {

	clearInterval(interval);
	$("#servicestatus").attr("style", "color:blue").html("<TMPL_VAR "COMMON.HINT_EXECUTING">");
	$("#servicestatusicon").html("<img src='./images/unknown_20.png'>");
	$.ajax( { 
			url:  'ajax.cgi',
			type: 'POST',
			data: { 
				action: 'servicestop'
			}
		} )
	.fail(function( data ) {
		console.log( "Servicestop Fail", data );
	})
	.done(function( data ) {
		console.log( "Servicestop Success", data );
		if (data == "0") {
			servicestatus(1);
		} else {
			$("#servicestatus").attr("style", "background:#dfdfdf; color:red").html("<TMPL_VAR "COMMON.HINT_FAILED">");
		}
		interval = window.setInterval(function(){ servicestatus(); }, 5000);
	})
	.always(function( data ) {
		console.log( "Servicestop Finished", data );
	});
}

function measurements() {

	$.ajax( { 
			url:  'measurements.json',
			type: 'GET'
		} )
	.fail(function( data ) {
		console.log( "Measurements Fail", data );
	})
	.done(function( data ) {
		console.log( "Measurements Success", data );
		for (var key in data) {
			if (document.getElementById('value'+key)) {
				document.getElementById('value'+key).innerHTML = data[key]['value1']
			}
		}
	})
	.always(function( data ) {
		console.log( "Measurements Finished", data );
	});
}

// ADD SENSOR: Popup

function popup_add_sensor() {

	// Set defaults
	$("#form_add_sensor")[0].reset();
	$("#edit_sensor").val('');
	$("#savinghint_sensor").html('&nbsp;');
	// Open Popup
	$( "#popup_add_sensor" ).popup( "open" )

}

// EDIT SENSOR: Popup

function popup_edit_sensor(sensorname) {

	// Ajax request
	$.ajax({ 
		url:  'ajax.cgi',
		type: 'POST',
		data: {
			action: 'getconfig'
		}
	})
	.fail(function( data ) {
		console.log( "edit_sensor Fail", data );
		return;
	})
	.done(function( data ) {
		console.log( "edit_sensor Success", data );

		sensors = data.sensors;
		if ( data.error || jQuery.isEmptyObject(sensors)) {
			sensors = undefined;
			return;
		}
		$.each( sensors, function( intDevId, item){
			if (item.name == sensorname) {
				$("#name_sensor").val(item.name);
				$("#type_sensor").val(item.type).selectmenu('refresh',true);
				$("#address_sensor").val(item.address);
				if ( item.calibrate == "1" ) {
					$("#cal_sensor").prop('checked', true).checkboxradio('refresh');
				} else {
					$("#cal_sensor").prop('checked', false).checkboxradio('refresh');
				}
				$("#callow_sensor").val(item.cal_low);
				$("#calmid_sensor").val(item.cal_mid);
				$("#calhigh_sensor").val(item.cal_high);
				if ( item.lcd == "1" ) {
					$("#lcd_sensor").prop('checked', true).checkboxradio('refresh');
				} else {
					$("#lcd_sensor").prop('checked', false).checkboxradio('refresh');
				}
				$("#lcdvalue_sensor").val(item.lcd_value).selectmenu('refresh',true);
				$("#lcdunit_sensor").val(item.lcd_unit);
				$("#edit_sensor").val(item.name);
				// Open Popup
				$("#savinghint_sensor_").html('&nbsp;');
				$("#popup_add_sensor").popup( "open" );
			}
		});
	})
	.always(function( data ) {
		console.log( "edit_sensor Finished" );
	})

}

// ADD/EDIT SENSOR (save to config)

function add_sensor() {

	$("#savinghint_sensor").attr("style", "color:blue").html("<TMPL_VAR "COMMON.HINT_SAVING">");
	if ( $("#cal_sensor").is(":checked") ) {
		calsensor = "1";
	} else {
		calsensor = "0";
	}
	if ( $("#lcd_sensor").is(":checked") ) {
		lcdsensor = "1";
	} else {
		lcdsensor = "0";
	}
	$.ajax( { 
			url:  'ajax.cgi',
			type: 'POST',
			data: { 
				action: 'addsensor',
				name: $("#name_sensor").val(),
				type: $("#type_sensor").val(),
				address: $("#address_sensor").val(),
				cal: calsensor,
				callow: $("#callow_sensor").val(),
				calmid: $("#calmid_sensor").val(),
				calhigh: $("#calhigh_sensor").val(),
				lcd: lcdsensor,
				lcdunit: $("#lcdunit_sensor").val(),
				lcdvalue: $("#lcdvalue_sensor").val(),
				edit: $("#edit_sensor").val(),
			}
		} )
	.fail(function( data ) {
		console.log( "add_sensor Fail", data );
		var jsonresp = JSON.parse(data.responseText);
		$("#savinghint_sensor").attr("style", "color:red").html("<TMPL_VAR "COMMON.HINT_SAVING_FAILED">" + " Error: " + jsonresp.error + " (Statuscode: " + data.status + ").");
	})
	.done(function( data ) {
		console.log( "add_sensor Done", data );
		if (data.error) {
			$("#savinghint_sensor").attr("style", "color:red").html("<TMPL_VAR "COMMON.HINT_SAVING_FAILED">" + " Error: " + data.error + ").");
		} else {
			$("#savinghint_sensor").attr("style", "color:green").html("<TMPL_VAR "COMMON.HINT_SAVING_SUCCESS">" + ".");
			getconfig();
			// Close Popup
			$("#popup_add_sensor").popup( "close" );
			// Clean Popup
			$( "#form_add_sensor" )[0].reset();
			$("#savinghint_sensor").html('&nbsp;');
		}
	})
	.always(function( data ) {
		console.log( "add_sensor Finished", data );
	});

}

// DELETE SENSOR: Popup

function popup_delete_sensor(sensorname) {

	$("#deletesensorhint").html('&nbsp;');
	$("#deletesensorname").html(sensorname);
	$( "#popup_delete_sensor" ).popup( "open" )

}

// DELETE SENSOR (save to config)

function delete_sensor() {

	$("#deletesensorhint").attr("style", "color:blue").html("<TMPL_VAR "COMMON.HINT_DELETING">");
	$.ajax( { 
			url:  'ajax.cgi',
			type: 'POST',
			data: { 
				action: 'deletesensor',
				name: $("#deletesensorname").html(),
			}
		} )
	.fail(function( data ) {
		console.log( "delete_sensor Fail", data );
		var jsonresp = JSON.parse(data.responseText);
		$("#deletesensorhint").attr("style", "color:red").html("<TMPL_VAR "COMMON.HINT_DELETING_FAILED">" + " Error: " + jsonresp.error + " (Statuscode: " + data.status + ").");
	})
	.done(function( data ) {
		console.log( "delete_sensor Done", data );
		if (data.error) {
			$("#deletesensorhint").attr("style", "color:red").html("<TMPL_VAR "COMMON.HINT_DELETING_FAILED">" + " Error: " + data.error + ").");
		} else {
			$("#deletesensorhint").attr("style", "color:green").html("<TMPL_VAR "COMMON.HINT_SAVING_SUCCESS">" + ".");
			getconfig();
			// Close Popup
			$("#popup_delete_sensor").popup( "close" );
			$("#deletesensorhint").html("&nbsp;");
		}
	})
	.always(function( data ) {
		console.log( "add_sensor Finished", data );
	});

}

// ADD ACTOR: Popup

function popup_add_actor() {

	// Set defaults
	$("#form_add_actor")[0].reset();
	$("#edit_actor").val('');
	$("#savinghint_actor").html('&nbsp;');
	// Open Popup
	$( "#popup_add_actor" ).popup( "open" )

}

// EDIT ACTOR: Popup

function popup_edit_actor(actorname) {

	// Ajax request
	$.ajax({ 
		url:  'ajax.cgi',
		type: 'POST',
		data: {
			action: 'getconfig'
		}
	})
	.fail(function( data ) {
		console.log( "edit_actor Fail", data );
		return;
	})
	.done(function( data ) {
		console.log( "edit_actor Success", data );

		actors = data.actors;
		if ( data.error || jQuery.isEmptyObject(actors)) {
			actors = undefined;
			return;
		}
		$.each( actors, function( intDevId, item){
			if (item.name == actorname) {
				$("#name_actor").val(item.name);
				$("#type_actor").val(item.type).selectmenu('refresh',true);
				$("#address_actor").val(item.address);
				if ( item.calibrate == "1" ) {
					$("#cal_actor").prop('checked', true).checkboxradio('refresh');
				} else {
					$("#cal_actor").prop('checked', false).checkboxradio('refresh');
				}
				$("#callow_actor").val(item.cal_low);
				$("#calmid_actor").val(item.cal_mid);
				$("#calhigh_actor").val(item.cal_high);
				if ( item.lcd == "1" ) {
					$("#lcd_actor").prop('checked', true).checkboxradio('refresh');
				} else {
					$("#lcd_actor").prop('checked', false).checkboxradio('refresh');
				}
				$("#lcdvalue_actor").val(item.lcd_value).selectmenu('refresh',true);
				$("#lcdunit_actor").val(item.lcd_unit);
				$("#edit_actor").val(item.name);
				// Open Popup
				$("#savinghint_actor_").html('&nbsp;');
				$("#popup_add_actor").popup( "open" );
			}
		});
	})
	.always(function( data ) {
		console.log( "edit_actor Finished" );
	})

}

// ADD/EDIT ACTOR (save to config)

function add_actor() {

	$("#savinghint_actor").attr("style", "color:blue").html("<TMPL_VAR "COMMON.HINT_SAVING">");
	if ( $("#cal_actor").is(":checked") ) {
		calactor = "1";
	} else {
		calactor = "0";
	}
	if ( $("#lcd_actor").is(":checked") ) {
		lcdactor = "1";
	} else {
		lcdactor = "0";
	}
	$.ajax( { 
			url:  'ajax.cgi',
			type: 'POST',
			data: { 
				action: 'addactor',
				name: $("#name_actor").val(),
				type: $("#type_actor").val(),
				address: $("#address_actor").val(),
				cal: calactor,
				callow: $("#callow_actor").val(),
				calmid: $("#calmid_actor").val(),
				calhigh: $("#calhigh_actor").val(),
				lcd: lcdactor,
				lcdunit: $("#lcdunit_actor").val(),
				lcdvalue: $("#lcdvalue_actor").val(),
				edit: $("#edit_actor").val(),
			}
		} )
	.fail(function( data ) {
		console.log( "add_actor Fail", data );
		var jsonresp = JSON.parse(data.responseText);
		$("#savinghint_actor").attr("style", "color:red").html("<TMPL_VAR "COMMON.HINT_SAVING_FAILED">" + " Error: " + jsonresp.error + " (Statuscode: " + data.status + ").");
	})
	.done(function( data ) {
		console.log( "add_actor Done", data );
		if (data.error) {
			$("#savinghint_actor").attr("style", "color:red").html("<TMPL_VAR "COMMON.HINT_SAVING_FAILED">" + " Error: " + data.error + ").");
		} else {
			$("#savinghint_actor").attr("style", "color:green").html("<TMPL_VAR "COMMON.HINT_SAVING_SUCCESS">" + ".");
			getconfig();
			// Close Popup
			$("#popup_add_actor").popup( "close" );
			// Clean Popup
			$( "#form_add_actor" )[0].reset();
			$("#savinghint_actor").html('&nbsp;');
		}
	})
	.always(function( data ) {
		console.log( "add_actor Finished", data );
	});

}

// DELETE ACTOR: Popup

function popup_delete_actor(actorname) {

	$("#deleteactorhint").html('&nbsp;');
	$("#deleteactorname").html(actorname);
	$( "#popup_delete_actor" ).popup( "open" )

}

// DELETE ACTOR (save to config)

function delete_actor() {

	$("#deleteactorhint").attr("style", "color:blue").html("<TMPL_VAR "COMMON.HINT_DELETING">");
	$.ajax( { 
			url:  'ajax.cgi',
			type: 'POST',
			data: { 
				action: 'deleteactor',
				name: $("#deleteactorname").html(),
			}
		} )
	.fail(function( data ) {
		console.log( "delete_actor Fail", data );
		var jsonresp = JSON.parse(data.responseText);
		$("#deleteactorhint").attr("style", "color:red").html("<TMPL_VAR "COMMON.HINT_DELETING_FAILED">" + " Error: " + jsonresp.error + " (Statuscode: " + data.status + ").");
	})
	.done(function( data ) {
		console.log( "delete_actor Done", data );
		if (data.error) {
			$("#deleteactorhint").attr("style", "color:red").html("<TMPL_VAR "COMMON.HINT_DELETING_FAILED">" + " Error: " + data.error + ").");
		} else {
			$("#deleteactorhint").attr("style", "color:green").html("<TMPL_VAR "COMMON.HINT_SAVING_SUCCESS">" + ".");
			getconfig();
			// Close Popup
			$("#popup_delete_actor").popup( "close" );
			$("#deleteactorhint").html("&nbsp;");
		}
	})
	.always(function( data ) {
		console.log( "add_actor Finished", data );
	});

}

// Save SETTINGS (save to config)

function save_settings() {

	$("#savinghint_settings").attr("style", "color:blue").html("<TMPL_VAR "COMMON.HINT_SAVING">");
	$.ajax( { 
			url:  'ajax.cgi',
			type: 'POST',
			data: { 
				action: 'savesettings',
				topic: $("#topic_settings").val(),
				valuecycle: $("#valuescycle_settings").val(),
				statuscycle: $("#statuscycle_settings").val(),
			}
		} )
	.fail(function( data ) {
		console.log( "save_settings Fail", data );
		var jsonresp = JSON.parse(data.responseText);
		$("#savinghint_settings").attr("style", "color:red").html("<TMPL_VAR "COMMON.HINT_SAVING_FAILED">" + " Error: " + jsonresp.error + " (Statuscode: " + data.status + ").");
	})
	.done(function( data ) {
		console.log( "save_settings Done", data );
		if (data.error) {
			$("#savinghint_settings").attr("style", "color:red").html("<TMPL_VAR "COMMON.HINT_SAVING_FAILED">" + " Error: " + data.error + ").");
		} else {
			$("#savinghint_settings").attr("style", "color:green").html("<TMPL_VAR "COMMON.HINT_SAVING_SUCCESS">" + ".");
			getconfig();
		}
	})
	.always(function( data ) {
		console.log( "save_settings Finished", data );
	});

}

// Save LCD-DISPLAY (save to config)

function save_lcd() {

	$("#savinghint_lcd").attr("style", "color:blue").html("<TMPL_VAR "COMMON.HINT_SAVING">");
	if ( $("#active_lcd").is(":checked") ) {
		activelcd = "1";
	} else {
		activelcd = "0";
	}
	$.ajax( { 
			url:  'ajax.cgi',
			type: 'POST',
			data: { 
				action: 'savelcd',
				active: activelcd,
				cycletime: $("#cycletime_lcd").val(),
				displaytimeout: $("#displaytimeout_lcd").val(),
				value1name: $("#value1name_lcd").val(),
				value2name: $("#value2name_lcd").val(),
				value3name: $("#value3name_lcd").val(),
				value4name: $("#value4name_lcd").val(),
				value5name: $("#value5name_lcd").val(),
				value1unit: $("#value1unit_lcd").val(),
				value2unit: $("#value2unit_lcd").val(),
				value3unit: $("#value3unit_lcd").val(),
				value4unit: $("#value4unit_lcd").val(),
				value5unit: $("#value5unit_lcd").val(),
			}
		} )
	.fail(function( data ) {
		console.log( "save_lcd Fail", data );
		var jsonresp = JSON.parse(data.responseText);
		$("#savinghint_lcd").attr("style", "color:red").html("<TMPL_VAR "COMMON.HINT_SAVING_FAILED">" + " Error: " + jsonresp.error + " (Statuscode: " + data.status + ").");
	})
	.done(function( data ) {
		console.log( "save_lcd Done", data );
		if (data.error) {
			$("#savinghint_lcd").attr("style", "color:red").html("<TMPL_VAR "COMMON.HINT_SAVING_FAILED">" + " Error: " + data.error + ").");
		} else {
			$("#savinghint_lcd").attr("style", "color:green").html("<TMPL_VAR "COMMON.HINT_SAVING_SUCCESS">" + ".");
			getconfig();
		}
	})
	.always(function( data ) {
		console.log( "save_lcd Finished", data );
	});

}

// GET CONFIG

function getconfig() {

	// Ajax request
	$.ajax({ 
		url:  'ajax.cgi',
		type: 'POST',
		data: {
			action: 'getconfig'
		}
	})
	.fail(function( data ) {
		console.log( "getconfig Fail", data );
	})
	.done(function( data ) {
		console.log( "getconfig Success", data );
		$("#main").css( 'visibility', 'visible' );

		// Calibration

		calibrate = "<TMPL_VAR CALIBRATE>";
		address = "<TMPL_VAR ADDRESS>";

		// Settings

		$("#statuscycle_settings").val(data.statuscycle);
		$("#valuescycle_settings").val(data.valuecycle);
		$("#topic_settings").val(data.topic);

		// LCD Display

		$("#cycletime_lcd").val(data.lcd.cycletime);
		$("#displaytimeout_lcd").val(data.lcd.displaytimeout);
		if ( data.lcd.active == "1" ) {
			$("#active_lcd").prop('checked', true).checkboxradio('refresh');
		}
		ev = data.lcd.external_values;
		$.each( ev, function( intDevId, item){
			$("#" + item.address + "name_lcd").val(item.name);
			$("#" + item.address + "unit_lcd").val(item.lcd_unit);
		})

		// Sensors

		console.log( "Parse Item for Sensors" );
		sensors = data.sensors;
		$('#sensors-list').empty();
		if ( data.error || jQuery.isEmptyObject(sensors)) {
			$('#sensors-list').html("<TMPL_VAR SENSORS.HINT_NO_SENSORS>");
			sensors = undefined;
		} else {
			// Create table
			var table = $('<table style="min-width:200px; width:100%" width="100%" data-role="table" id="sensorstable" data-mode="reflow"\
				class="ui-responsive table-stripe ui-body-b">').appendTo('#sensors-list');
			// Add the header row
			var theader = $('<thead />').appendTo(table);
			var theaderrow = $('<tr class="ui-bar-b"/>').appendTo(theader);
			$('<th style="text-align:left; width:40%; padding:5px;"><TMPL_VAR COMMON.LABEL_NAME><\/th>').appendTo(theaderrow);
			$('<th style="text-align:left; width:10%; padding:5px;"><TMPL_VAR COMMON.LABEL_TYPE><\/th>').appendTo(theaderrow);
			$('<th style="text-align:left; width:30%; padding:5px;"><TMPL_VAR COMMON.LABEL_ADDRESS><\/th>').appendTo(theaderrow);
			$('<th style="text-align:left; width:20%; padding:5px;"><TMPL_VAR COMMON.LABEL_ACTIONS><\/th>').appendTo(theaderrow);
			// Create table body.
			var tbody = $('<tbody />').appendTo(table);
			// Add the data rows to the table body.
			$.each( sensors, function( intDevId, item){
				// Table for Atlas Form
				var row = $('<tr />').appendTo(tbody);
				$('<td style="text-align:left;">'+item.name+'<\/td>').appendTo(row);
				$('<td style="text-align:left;">'+item.type+'<\/td>').appendTo(row);
				$('<td style="text-align:left;">'+item.address+'<\/td>').appendTo(row);
				$('<td />', { html: '\
				<a href="javascript:popup_edit_sensor(\'' + item.name + '\')" id="btneditsensor_'+item.name+'" name="btneditsensor_'+item.name+'" \
				title="<TMPL_VAR COMMON.BUTTON_EDIT> ' + item.name + '"> \
				<img src="./images/settings_20.png" height="20"></img></a> \
				<a href="javascript:popup_delete_sensor(\'' + item.name + '\')" id="btnaskdeletesensor_'+item.name+'"\
				name="btnaskdeletesensor_'+item.name+'" \
				title="<TMPL_VAR COMMON.BUTTON_DELETE> ' + item.name + '"> \
				<img src="./images/cancel_20.png" height="20"></img></a> \
				' }).appendTo(row);
				$(row).trigger("create");
				// Box for Calibration Form
				if ( document.getElementById("calibration_overview") && calibrate != "1") {
				        calibration_overview.innerHTML += "<div><h2 class='boxtitle ui-title'><span style='vertical-align:middle'>\
						<img src='./images/input_title_32.png'></span>&nbsp;"+item.name+"</h2><div class='box'>\
						<div class='boxrow'><div class='boxitem'><span class='large bold' id='value"+item.address+"'></span>\
						&nbsp;<span class='small'>"+item.lcd_unit+"</span></div></div><div class='boxrow'><div class='boxitem'>\
						<a href='#' onclick=\"window.open('./calibrate.cgi?address="+item.address+"', 'NewWindow1','scrollbars=true,toolbar=no,location=no,\
						directories=no,status=no,menubar=no,copyhistory=no,width=800,height=800')\" id='btncalibrate"+item.address+"'\
						class='ui-btn ui-btn-inline ui-mini ui-btn-icon-left ui-icon-eye ui-corner-all'><TMPL_VAR 'ATLAS.BUTTON_CALIBRATE'></a>\
						</div></div>"
					if (item.calibrate != "1") {
						$("#btncalibrate"+item.address).addClass('ui-disabled');
					}
					calibration_overview.innerHTML += "</div></div>"
				}
				// Box for Calibration Process
				if ( document.getElementById("calibration") && calibrate == "1" && item.address == address ) {
					vars_address.innerHTML = "<input type='hidden' id='address' value='" + address + "'>";
					calibration_title.innerHTML = "<h2 class='boxtitle ui-title'><span style='vertical-align:middle'>\
						<img src='./images/input_title_32.png'></span>&nbsp;<TMPL_VAR 'ATLAS.BUTTON_CALIBRATION'>&nbsp;"+item.name+"</h2>"
				        calibration_value.innerHTML = "<div class='boxrow'><div class='boxitem'>\
						<span class='large bold' id='value"+item.address+"'></span>\
						&nbsp;<span class='small'>"+item.lcd_unit+"</span></div></div>"
					if ( data["calibration"][item.type]["1"] && item[data["calibration"][item.type]["1"]["step"]] ) {
						vars_step1.innerHTML = "<input type='hidden' id='step1_enabled' value='1'>\
							<input type='hidden' id='step1_command' value='" + data["calibration"][item.type]["1"]["command"] + "'>\
							<input type='hidden' id='step1_precommand' value='" + data["calibration"][item.type]["1"]["precommand"] + "'>\
							<input type='hidden' id='step1_enter_value' value='" + data["calibration"][item.type]["1"]["enter_value"] + "'>\
							<input type='hidden' id='step1_target' value='" + item[data["calibration"][item.type]["1"]["step"]] + "'>";
						step1_caltarget.innerHTML = "<h2>" + item[data["calibration"][item.type]["1"]["step"]] + " " + item.lcd_unit + "</h2>";
					} else {
						vars_step1.innerHTML = "<input type='hidden' id='step1_enabled' value='0'>\
							<input type='hidden' id='step1_command' value='0'>\
							<input type='hidden' id='step1_precommand' value='0'>\
							<input type='hidden' id='step1_enter_value' value='0'>\
							<input type='hidden' id='step1_target' value='0'>";
					}
					if ( data["calibration"][item.type]["2"] && item[data["calibration"][item.type]["2"]["step"]] ) {
						vars_step2.innerHTML = "<input type='hidden' id='step2_enabled' value='1'>\
							<input type='hidden' id='step2_command' value='" + data["calibration"][item.type]["2"]["command"] + "'>\
							<input type='hidden' id='step2_precommand' value='" + data["calibration"][item.type]["2"]["precommand"] + "'>\
							<input type='hidden' id='step2_enter_value' value='" + data["calibration"][item.type]["2"]["enter_value"] + "'>\
							<input type='hidden' id='step2_target' value='" + item[data["calibration"][item.type]["2"]["step"]] + "'>";
						step2_caltarget.innerHTML = "<h2>" + item[data["calibration"][item.type]["2"]["step"]] + " " + item.lcd_unit + "</h2>";
					} else {
						vars_step2.innerHTML = "<input type='hidden' id='step2_enabled' value='0'>\
							<input type='hidden' id='step2_command' value='0'>\
							<input type='hidden' id='step2_precommand' value='0'>\
							<input type='hidden' id='step2_enter_value' value='0'>\
							<input type='hidden' id='step2_target' value='0'>";
					}
					if ( data["calibration"][item.type]["3"] && item[data["calibration"][item.type]["3"]["step"]] ) {
						vars_step3.innerHTML = "<input type='hidden' id='step3_enabled' value='1'>\
							<input type='hidden' id='step3_command' value='" + data["calibration"][item.type]["3"]["command"] + "'>\
							<input type='hidden' id='step3_precommand' value='" + data["calibration"][item.type]["3"]["precommand"] + "'>\
							<input type='hidden' id='step3_enter_value' value='" + data["calibration"][item.type]["3"]["enter_value"] + "'>\
							<input type='hidden' id='step3_target' value='" + item[data["calibration"][item.type]["3"]["step"]] + "'>";
						step3_caltarget.innerHTML = "<h2>" + item[data["calibration"][item.type]["3"]["step"]] + " " + item.lcd_unit + "</h2>";
					} else {
						vars_step3.innerHTML = "<input type='hidden' id='step3_enabled' value='0'>\
							<input type='hidden' id='step3_command' value='0'>\
							<input type='hidden' id='step3_precommand' value='0'>\
							<input type='hidden' id='step3_enter_value' value='0'>\
							<input type='hidden' id='step3_target' value='0'>";
					}
					if ( $("#step1_enabled").val() == "1" ) {
						$("#calibration_step0").css( 'display', 'block' );
					} else {
						$("#calibration_nodata").css( 'display', 'block' );
					}
				}
			});
		};

		// Actors

		console.log( "Parse Item for Actors" );
		actors = data.actors;
		$('#actors-list').empty();
		if ( data.error || jQuery.isEmptyObject(actors)) {
			$('#actors-list').html("<TMPL_VAR ACTORS.HINT_NO_ACTORS>");
			actors = undefined;
		} else {
			// Create table
			var table = $('<table style="min-width:200px; width:100%" width="100%" data-role="table" id="actorstable" data-mode="reflow"\
				class="ui-responsive table-stripe ui-body-b">').appendTo('#actors-list');
			// Add the header row
			var theader = $('<thead />').appendTo(table);
			var theaderrow = $('<tr class="ui-bar-b"/>').appendTo(theader);
			$('<th style="text-align:left; width:40%; padding:5px;"><TMPL_VAR COMMON.LABEL_NAME><\/th>').appendTo(theaderrow);
			$('<th style="text-align:left; width:10%; padding:5px;"><TMPL_VAR COMMON.LABEL_TYPE><\/th>').appendTo(theaderrow);
			$('<th style="text-align:left; width:30%; padding:5px;"><TMPL_VAR COMMON.LABEL_ADDRESS><\/th>').appendTo(theaderrow);
			$('<th style="text-align:left; width:20%; padding:5px;"><TMPL_VAR COMMON.LABEL_ACTIONS><\/th>').appendTo(theaderrow);
			// Create table body.
			var tbody = $('<tbody />').appendTo(table);
			// Add the data rows to the table body.
			$.each( actors, function( intDevId, item){
				// Table for Atlas Form
				var row = $('<tr />').appendTo(tbody);
				$('<td style="text-align:left;">'+item.name+'<\/td>').appendTo(row);
				$('<td style="text-align:left;">'+item.type+'<\/td>').appendTo(row);
				$('<td style="text-align:left;">'+item.address+'<\/td>').appendTo(row);
				$('<td />', { html: '\
				<a href="javascript:popup_edit_actor(\'' + item.name + '\')" id="btneditactor_'+item.name+'" name="btneditactor_'+item.name+'" \
				title="<TMPL_VAR COMMON.BUTTON_EDIT> ' + item.name + '"> \
				<img src="./images/settings_20.png" height="20"></img></a> \
				<a href="javascript:popup_delete_actor(\'' + item.name + '\')" id="btnaskdeleteactor_'+item.name+'" \
				name="btnaskdeleteactor_'+item.name+'" \
				title="<TMPL_VAR COMMON.BUTTON_DELETE> ' + item.name + '"> \
				<img src="./images/cancel_20.png" height="20"></img></a> \
				' }).appendTo(row);
				$(row).trigger("create");
				// Box for Calibration Form
				if ( document.getElementById("calibration_overview") && calibrate != "1") {
				        calibration_overview.innerHTML += "<div><h2 class='boxtitle ui-title'><span style='vertical-align:middle'>\
						<img src='./images/input_title_32.png'></span>&nbsp;"+item.name+"</h2><div class='box'>\
						<div class='boxrow'><div class='boxitem'><span class='large bold' id='value"+item.address+"'></span>\
						&nbsp;<span class='small'>"+item.lcd_unit+"</span></div></div><div class='boxrow'><div class='boxitem'>\
						<a href='#' onclick=\"window.open('./calibrate.cgi?address="+item.address+"', 'NewWindow1','scrollbars=true,toolbar=no,location=no,\
						directories=no,status=no,menubar=no,copyhistory=no,width=800,height=800')\" id='btncalibrate"+item.address+"'\
						class='ui-btn ui-btn-inline ui-mini ui-btn-icon-left ui-icon-eye ui-corner-all'><TMPL_VAR 'ATLAS.BUTTON_CALIBRATE'></a>\
						</div></div>"
					if (item.calibrate != "1") {
						$("#btncalibrate"+item.address).addClass('ui-disabled');
					}
					calibration_overview.innerHTML += "</div></div>"
				}
				// Box for Calibration Process
				if ( document.getElementById("calibration") && calibrate == "1" && item.address == address ) {
					vars_address.innerHTML = "<input type='hidden' id='address' value='" + address + "'>";
					calibration_title.innerHTML = "<h2 class='boxtitle ui-title'><span style='vertical-align:middle'>\
						<img src='./images/input_title_32.png'></span>&nbsp;<TMPL_VAR 'ATLAS.BUTTON_CALIBRATION'>&nbsp;"+item.name+"</h2>"
				        calibration_value.innerHTML = "<div class='boxrow'><div class='boxitem'>\
						<span class='large bold' id='value"+item.address+"'></span>\
						&nbsp;<span class='small'>"+item.lcd_unit+"</span></div></div>"
					if ( data["calibration"][item.type]["1"] && item[data["calibration"][item.type]["1"]["step"]] ) {
						vars_step1.innerHTML = "<input type='hidden' id='step1_enabled' value='1'>\
							<input type='hidden' id='step1_command' value='" + data["calibration"][item.type]["1"]["command"] + "'>\
							<input type='hidden' id='step1_precommand' value='" + data["calibration"][item.type]["1"]["precommand"] + "'>\
							<input type='hidden' id='step1_enter_value' value='" + data["calibration"][item.type]["1"]["enter_value"] + "'>\
							<input type='hidden' id='step1_target' value='" + item[data["calibration"][item.type]["1"]["step"]] + "'>";
						step1_caltarget.innerHTML = "<h2>" + item[data["calibration"][item.type]["1"]["step"]] + " " + item.lcd_unit + "</h2>";
					} else {
						vars_step1.innerHTML = "<input type='hidden' id='step1_enabled' value='0'>\
							<input type='hidden' id='step1_command' value='0'>\
							<input type='hidden' id='step1_precommand' value='0'>\
							<input type='hidden' id='step1_enter_value' value='0'>\
							<input type='hidden' id='step1_target' value='0'>";
					}
					if ( data["calibration"][item.type]["2"] && item[data["calibration"][item.type]["2"]["step"]] ) {
						vars_step2.innerHTML = "<input type='hidden' id='step2_enabled' value='1'>\
							<input type='hidden' id='step2_command' value='" + data["calibration"][item.type]["2"]["command"] + "'>\
							<input type='hidden' id='step2_precommand' value='" + data["calibration"][item.type]["2"]["precommand"] + "'>\
							<input type='hidden' id='step2_enter_value' value='" + data["calibration"][item.type]["2"]["enter_value"] + "'>\
							<input type='hidden' id='step2_target' value='" + item[data["calibration"][item.type]["2"]["step"]] + "'>";
						step2_caltarget.innerHTML = "<h2>" + item[data["calibration"][item.type]["2"]["step"]] + " " + item.lcd_unit + "</h2>";
					} else {
						vars_step2.innerHTML = "<input type='hidden' id='step2_enabled' value='0'>\
							<input type='hidden' id='step2_command' value='0'>\
							<input type='hidden' id='step2_precommand' value='0'>\
							<input type='hidden' id='step2_enter_value' value='0'>\
							<input type='hidden' id='step2_target' value='0'>";
					}
					if ( data["calibration"][item.type]["3"] && item[data["calibration"][item.type]["3"]["step"]] ) {
						vars_step3.innerHTML = "<input type='hidden' id='step3_enabled' value='1'>\
							<input type='hidden' id='step3_command' value='" + data["calibration"][item.type]["3"]["command"] + "'>\
							<input type='hidden' id='step3_precommand' value='" + data["calibration"][item.type]["3"]["precommand"] + "'>\
							<input type='hidden' id='step3_enter_value' value='" + data["calibration"][item.type]["3"]["enter_value"] + "'>\
							<input type='hidden' id='step3_target' value='" + item[data["calibration"][item.type]["3"]["step"]] + "'>";
						step3_caltarget.innerHTML = "<h2>" + item[data["calibration"][item.type]["3"]["step"]] + " " + item.lcd_unit + "</h2>";
					} else {
						vars_step3.innerHTML = "<input type='hidden' id='step3_enabled' value='0'>\
							<input type='hidden' id='step3_command' value='0'>\
							<input type='hidden' id='step3_precommand' value='0'>\
							<input type='hidden' id='step3_enter_value' value='0'>\
							<input type='hidden' id='step3_target' value='0'>";
					}
					if ( $("#step1_enabled").val() == "1" ) {
						$("#calibration_step0").css( 'display', 'block' );
					} else {
					}
				}
			});
		};
		if (document.getElementById('calibration_overview') && typeof sensors === 'undefined' && typeof actors === 'undefined')  {
		       	calibration_overview.innerHTML = "<center><b><TMPL_VAR ATLAS.HINT_NO_DEVICES></b></center>"
		}

	})
	.always(function( data ) {
		console.log( "getconfig Finished" );
		if (document.getElementById("calibration_overview")) {
			measurements();
		}
	})

}

// CALIBRATION STEPS

function calibrate_step0() {

		$("#calibration_step0").css( 'display', 'none' );
		$("#calibration_step1").css( 'display', 'none' );
		$("#calibration_step2").css( 'display', 'none' );
		$("#calibration_step3").css( 'display', 'none' );
		$("#calibration_step4").css( 'display', 'none' );
		$("#calibration_step5").css( 'display', 'none' );
		$("#calibration_step1_enter").css( 'display', 'none' );
		$("#calibration_step2_enter").css( 'display', 'none' );
		$("#calibration_step3_enter").css( 'display', 'none' );
		// Start Calibration Mode here
		sendcommand("plugin:calibrate");
		if ( $("#step1_enabled").val() == "1" ) {
			$("#calibration_step1").css( 'display', 'block' );
		} else {
			calibrate_step1()
		}

}

function calibrate_step1() {

		$("#calibration_step0").css( 'display', 'none' );
		$("#calibration_step1").css( 'display', 'none' );
		$("#calibration_step2").css( 'display', 'none' );
		$("#calibration_step3").css( 'display', 'none' );
		$("#calibration_step4").css( 'display', 'none' );
		$("#calibration_step5").css( 'display', 'none' );
		$("#calibration_step1_enter").css( 'display', 'none' );
		$("#calibration_step2_enter").css( 'display', 'none' );
		$("#calibration_step3_enter").css( 'display', 'none' );
		if ( $("#step1_enabled").val() == "1" ) {
			if ( $("#step1_enter_value").val() == "1" ) {
				if ( $("#step1_measured_value").val() == "" ) {
					// Send Precommand here
					command = $("#address").val() + ":" + $("#step1_precommand").val() + "," + $("#step1_target").val().replaceAll(",", ".");
					console.log ("Sending PreCommand: " + command);
					sendcommand(command);
					$("#calibration_step1_enter").css( 'display', 'block' );
					return;
				} else {
					// Send Cal command here
					command = $("#address").val() + ":" + $("#step1_command").val() + "," + $("#step1_measured_value").val().replaceAll(",", ".");
					console.log ("Sending Command: " + command);
					sendcommand(command);
				}
			} else {
				// Send Cal command here
				command = $("#address").val() + ":" + $("#step1_command").val() + "," + $("#step1_target").val().replaceAll(",", ".");
				console.log ("Sending Command: " + command);
				sendcommand(command);
			}
		}
		if ( $("#step2_enabled").val() == "1" ) {
			$("#calibration_step2").css( 'display', 'block' );
		} else {
			calibrate_step2()
		}

}

function calibrate_step2() {

		$("#calibration_step0").css( 'display', 'none' );
		$("#calibration_step1").css( 'display', 'none' );
		$("#calibration_step2").css( 'display', 'none' );
		$("#calibration_step3").css( 'display', 'none' );
		$("#calibration_step4").css( 'display', 'none' );
		$("#calibration_step5").css( 'display', 'none' );
		$("#calibration_step1_enter").css( 'display', 'none' );
		$("#calibration_step2_enter").css( 'display', 'none' );
		$("#calibration_step3_enter").css( 'display', 'none' );
		if ( $("#step2_enabled").val() == "1" ) {
			if ( $("#step2_enter_value").val() == "1" ) {
				if ( $("#step2_measured_value").val() == "" ) {
					// Send Precommand here
					command = $("#address").val() + ":" + $("#step2_precommand").val() + "," + $("#step2_target").val().replaceAll(",", ".");
					console.log ("Sending PreCommand: " + command);
					sendcommand(command);
					$("#calibration_step2_enter").css( 'display', 'block' );
					return;
				} else {
					// Send Cal command here
					command = $("#address").val() + ":" + $("#step2_command").val() + "," + $("#step2_measured_value").val().replaceAll(",", ".");
					console.log ("Sending Command: " + command);
					sendcommand(command);
				}
			} else {
				// Send Cal command here
				command = $("#address").val() + ":" + $("#step2_command").val() + "," + $("#step2_target").val().replaceAll(",", ".");
				console.log ("Sending Command: " + command);
				sendcommand(command);
			}
		}
		if ( $("#step3_enabled").val() == "1" ) {
			$("#calibration_step3").css( 'display', 'block' );
		} else {
			calibrate_step3()
		}

}

function calibrate_step3() {

		$("#calibration_step0").css( 'display', 'none' );
		$("#calibration_step1").css( 'display', 'none' );
		$("#calibration_step2").css( 'display', 'none' );
		$("#calibration_step3").css( 'display', 'none' );
		$("#calibration_step4").css( 'display', 'none' );
		$("#calibration_step5").css( 'display', 'none' );
		$("#calibration_step1_enter").css( 'display', 'none' );
		$("#calibration_step2_enter").css( 'display', 'none' );
		$("#calibration_step3_enter").css( 'display', 'none' );
		$("#calibration_step4").css( 'display', 'block' );
		if ( $("#step3_enabled").val() == "1" ) {
			if ( $("#step3_enter_value").val() == "1" ) {
				if ( $("#step3_measured_value").val() == "" ) {
					// Send Precommand here
					command = $("#address").val() + ":" + $("#step3_precommand").val() + "," + $("#step3_target").val().replaceAll(",", ".");
					console.log ("Sending PreCommand: " + command);
					sendcommand(command);
					$("#calibration_step3_enter").css( 'display', 'block' );
					return;
				} else {
					// Send Cal command here
					command = $("#address").val() + ":" + $("#step3_command").val() + "," + $("#step3_measured_value").val().replaceAll(",", ".");
					console.log ("Sending Command: " + command);
					sendcommand(command);
				}
			} else {
				// Send Cal command here
				command = $("#address").val() + ":" + $("#step3_command").val() + "," + $("#step3_target").val().replaceAll(",", ".");
				console.log ("Sending Command: " + command);
				sendcommand(command);
			}
		}

}

function calibrate_step4() {

		// Stop Calibration Mode here
		sendcommand("plugin:start");
		$("#calibration_step0").css( 'display', 'none' );
		$("#calibration_step1").css( 'display', 'none' );
		$("#calibration_step2").css( 'display', 'none' );
		$("#calibration_step3").css( 'display', 'none' );
		$("#calibration_step4").css( 'display', 'none' );
		$("#calibration_step5").css( 'display', 'none' );
		$("#calibration_step1_enter").css( 'display', 'none' );
		$("#calibration_step2_enter").css( 'display', 'none' );
		$("#calibration_step3_enter").css( 'display', 'none' );

		// End Message
		$("#calibration_value").css( 'display', 'none' );
		$("#calibration_value_box").css( 'display', 'none' );
		$("#calibration_step5").css( 'display', 'block' );

}

function sendcommand( accommand ) {

	$.ajax( { 
			url:  'ajax.cgi',
			type: 'POST',
			data: { 
				action: 'sendcommand',
				command: accommand
			}
		} )
	.fail(function( data ) {
		console.log( "SSendcommand Fail", data );
	})
	.done(function( data ) {
		console.log( "Sendcommand Success", data );
	})
	.always(function( data ) {
		console.log( "Sendcommand Finished", data );
		return (data)
	});

}

</script>
