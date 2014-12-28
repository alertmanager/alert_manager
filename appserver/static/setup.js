
$(function(){
	var check = 0;
	var indexel = "#\\/admin\\/alert_manager\\/settings\\/index_id";
	var index_list = [];

	$("<span />").css('display', 'block').attr("id", "index_check").insertAfter($(indexel));

	
	$.getJSON( "/custom/alert_manager/helpers/get_indexes", function( data ) {
		
		$.each( data, function( key, val ) {
			index_list.push( val );
		});

		var index = $(indexel).val();
		indexCheck(index, index_list);

		console.debug("indexlist", index_list);
	});


	var indexCheck = function($index, $index_list) {
		if ($index == "alerts") {
			if($.inArray($index, $index_list) == -1) {
				check = 0;
				$("#index_check").html('Default index "alerts" doesn\'t exists. Did you install and configure <a href="/app/alert_manager/alert_manager_installation_guide#install-the-technology-add-on-for-alert-manager">TA-alert_manager</a> correctly?');
			} else {
				$("#index_check").text("Default index 'alerts' exists, all set.")
				check = 1;
			}
		} else {
			if($.inArray($index, $index_list) == -1) {
				check = 0;
				$("#index_check").text("Custom index '"+ $index +"' doesn't exists. Please configure it first.");
			} else {
				check = 2;
				$("#index_check").text("Custom index '"+ $index +"' already exists. Are you sure to use this one?")
			}
		}
		$("#index_check").removeClass();
		$("#index_check").addClass("index_check-"+check);
	};


	$(indexel).keyup(function() {
		var index = $( this ).val();
		indexCheck(index, index_list);
	});

	$(".splButton-primary").click(function() {
		var index = $(indexel).val();
		if(check != 1) {
			if(check == 0) {
				if(index == "alerts") {
					alert("The default index '"+index+"' doesn't exists. Check if TA-alert_manager is installed and configured correctly.")
					return false;
				} else {
					alert("The index '"+index+"' doesn't exists. Please create it first.")
					return false;
				}
			} 
			if(check == 2) {
				if(confirm("Are you sure to use the pre-existing custom-index '"+index+"'?")) {
					return true;
				} else {
					return false;
				}
			}

		} else {
			return true;
		}
	});
});
