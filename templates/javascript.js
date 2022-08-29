<script>

$(function() {
	
	if (document.getElementById("servicestatus")) {
		interval = window.setInterval(function(){ servicestatus(); }, 5000);
	}
	if (document.getElementById("calibration_overview")) {
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

		// Settings

		$("#statuscycle_settings").val(data.statuscycle);
		$("#valuescycle_settings").val(data.valuecycle);
		$("#topic_settings").val(data.topic);

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
				if (document.getElementById("calibration_overview")) {
				        calibration_overview.innerHTML += "<div><h2 class='boxtitle ui-title'><span style='vertical-align:middle'>\
						<img src='./images/input_title_32.png'></span>&nbsp;"+item.name+"</h2><div class='box'>\
						<div class='boxrow'><div class='boxitem'><span class='large bold' id='value"+item.address+"'></span>\
						&nbsp;<span class='tiny'>"+item.lcd_unit+"</span></div></div></div></div>"
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
				if (document.getElementById("calibration_overview")) {
			        	calibration_overview.innerHTML += "<div><h2 class='boxtitle ui-title'><span style='vertical-align:middle'>\
						<img src='./images/output_title_32.png'></span>&nbsp;"+item.name+"</h2><div class='box'><div class='boxrow'>\
						<div class='boxitem'><span class='large bold' id='value"+item.address+"'></span>&nbsp;\
						<span class='tiny''>"+item.lcd_unit+"</span></div></div></div></div>"
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

</script>
