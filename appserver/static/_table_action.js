require([
    "splunkjs/mvc",
    "splunkjs/mvc/utils",
    "splunkjs/mvc/tokenutils",
    "underscore",
    "jquery",
    "splunkjs/mvc/simplexml",
    "splunkjs/mvc/searchmanager",
    

    'splunkjs/mvc/tableview'    

], 
function(
        mvc,
        utils,
        TokenUtils,
        _,
        $,
        DashboardController,
        SearchManager,
        TableView 
    ) {
    // MY JS
  
	  // Save lookup
    var lookupsearch1 = new SearchManager({
        "id": "lookupsearch1",
        "cancelOnUnload": true,
        "status_buckets": 0,
        "auto_cancel": 90,
        "preview": true
    }, {tokens: true, tokenNamespace: "submitted"});

	 // Load lookup (USERs)
    var lookupsearch2 = new SearchManager({
        "id": "lookupsearch2",
        "cancelOnUnload": true,
        "status_buckets": 0,
        "earliest_time": "-1d",
        "latest_time": "$latest$",
        "search":"| inputlookup users.csv",
        "auto_cancel": 90,
        "preview": true,
        "autostart": false
    }, {tokens: true, tokenNamespace: "submitted"});
    
    var user=[];
    var my_element="element1";
    var my_element_id="#element1";
    var my_detail_id="#alert_details";    

    var submittedTokenModel = mvc.Components.getInstance('submitted', {create: true});
    var defaultTokenModel = mvc.Components.getInstance('default', {create: true});
    
    lookupsearch2.startSearch();
    var myDDResults = lookupsearch2.data("results");
    
    myDDResults.on("data", function() {
            user=[];
            _.each(myDDResults.data().rows, function(column, rowCount) {
                    user.push(String(column[0]));
            });
    });

    var my_owner="";
         
    // Translations from rangemap results to CSS class
    var ICONS = {
        test: 'alert-circle',
        unchecked: 'alert',
        checked: 'check-circle'
    };

    var tr_action_index=0;
    var action_counter=0;

    var DrillDownRenderer = TableView.BaseCellRenderer.extend({
        canRender: function(cell) {
            // Only use the cell renderer for the specific field
            return true;
        },
        render: function($td, cell) {
  				  
            console.dir($td)
            if (cell.field!="action" && cell.field!="Alert_Owner" && cell.field!="description" && cell.field!="sid") 
            { 
              $td.addClass('drilldown_enabled').html(cell.value);
            }
            
        }
    });
              
    var IconRenderer = TableView.BaseCellRenderer.extend({
        canRender: function(cell) {
            // Only use the cell renderer for the specific field
            return cell.field === 'action';
        },
        render: function($td, cell) {
    
            var icon = 'question';
            // Fetch the icon for the value
            if (ICONS.hasOwnProperty(cell.value)) {
                icon = ICONS[cell.value];
            }
            // Create the icon element and add it to the table cell
  			    if (cell.value=="checked") do_action="uncheck"; else do_action="check"; 
            
            var rendercontent='<div style="float:left; max-height:22px; margin:0px;"><i class="icon-<%-icon%> <%- action %>" title="<%- action %>">&nbsp;</i></div>';
  				  
            if (cell.value!="checked") 
            { 
              // rendercontent+='<div class="checkbutton_wrapper"><input type="button" class=".icon-check-circle checkbutton" value="<%- do_action %>" />&nbsp</div>';
              rendercontent+='<div class="checkbutton_wrapper"><i class="icon-check-circle checkbutton">&nbsp</i></div>';
              $td.addClass('highlight_action_unchecked'+(tr_action_index%2) );
            }
            else
            {
              $td.addClass('highlight_action_checked'+(tr_action_index%2));
            }
      			
            $td.addClass('icon').html(_.template(rendercontent, {
                    icon: icon,
                    action: cell.value
                }));
    		    
            
        }
    });

  
    var DescriptionRenderer = TableView.BaseCellRenderer.extend({
        canRender: function(cell) {
            // Only use the cell renderer for the specific field
            return cell.field === 'description';
        },
        render: function($td, cell) {
  			var rendercontent='<div style="float:left; max-height:22px; margin:0px">';
  				if (cell.value==null) 
          {
            rendercontent+='<input type="text" value="<%-Alert_Description%>" />';
            $td.addClass('highlight_action_unchecked'+(tr_action_index%2));
          }
  				else 
          {
            rendercontent+='<%-Alert_Description%>';
            $td.addClass('highlight_action_checked'+(tr_action_index%2));
          }
  				rendercontent+='&nbsp</div>';

            
          $td.addClass('description').html(_.template(rendercontent, {
              Alert_Description: cell.value
          }));
          tr_action_index+=1;
        }
    });
  
    var OwnerRenderer = TableView.BaseCellRenderer.extend({
        canRender: function(cell) {
            // Only use the cell renderer for the specific field
            return cell.field === 'Alert_Owner';
        },
        render: function($td, cell) {
  			  var rendercontent='<div style="float:left; max-height:22px; margin:0px">';
  				// if (cell.value==null) rendercontent+='<input type="text" id="alert_owner_input_'+tr_index+'" value="<%-Alert_Owner%>" />';
  				if (cell.value==null) 
          {
           
            rendercontent+='<div class="dd_input"><select name="users" class="selectuser" size="1" style="max-height:22px; margin:0px;">';

            for (var i = 0; i < user.length; i++) {
              rendercontent+= '<option>'+user[i]+'</option>';
            }

            rendercontent+='</select></div>';

            $td.addClass('highlight_action_unchecked'+(tr_action_index%2));            

          }
  				else 
          { 
            rendercontent+='<%-Alert_Owner%>';
            $td.addClass('highlight_action_checked'+(tr_action_index%2));
          }
  				rendercontent+='&nbsp</div>';

          $td.addClass('owner').html(_.template(rendercontent, {
              Alert_Owner: cell.value
          }));

  			  
        }
        
    });

    var SidRenderer = TableView.BaseCellRenderer.extend({
        canRender: function(cell) {
            // Only use the cell renderer for the specific field
            return cell.field === 'sid';
        },
        render: function($td, cell) {
  			var rendercontent="<%-sid%>";
  			$td.addClass('sid').html(_.template(rendercontent, {
                sid: cell.value
            }));;
        }
    });
  
    mvc.Components.get(my_element).getVisualization(function(tableView){
        // Register custom cell renderer
    	// tableView.table.addCellRenderer(new DrillDownRenderer());
  		tableView.table.addCellRenderer(new SidRenderer());
  		tableView.table.addCellRenderer(new IconRenderer());
    	tableView.table.addCellRenderer(new OwnerRenderer());
    	tableView.table.addCellRenderer(new DescriptionRenderer());

      // Force the table to re-render
      tableView.table.render();

    });

     $(document).on("click", "td", function(e) {
            // Displays a data object in the console
            e.preventDefault();
            // console.dir($(this));

            if ($(this).context.cellIndex>=4) {
              drilldown_sid=($(this).parent().find("td.sid")[0].innerHTML);
              submittedTokenModel.set("drilldown_sid", drilldown_sid);
              
              // $(my_element_id).parent().parent().parent().width("50%");              
              $(my_detail_id).parent().parent().parent().show();

            }
        });
    
    
    // Add Eventhandler input done
  /*
  	$(document).on("change", "input[type='text']", function() {
    			saveFieldChanges(this);
    });

    $(document).on("click", "td", function() {
    			saveFieldChanges(this);
    });
  */  
    // Add Eventhandler Change action
    $(document).on("click", ".checkbutton", function() {
    			saveFieldChanges(this);
          $(this).parent().parent().parent().parent().find(".checkbutton_wrapper").show();    			
    });

    // Show button only when (one) field change
    $(document).on("change", '.dd_input select', function() {
    			// my_owner=this.value;
    			$(this).parent().parent().parent().parent().find(".icon-alert").hide();
          $(this).parent().parent().parent().parent().find(".checkbutton").fadeIn( "fast", function() {
              // Animation complete
              action_counter+=1;
          });
              			
    }); 

/*    
  	$(document).on("change", "input[type='text']", function() {
    			$(this).parent().parent().parent().find(".checkbutton").fadeIn( "fast", function() {
              // Animation complete
          });
    });       
*/

    /*
    $(document).on("mouseenter", '.icon', function() {
    			$(this).find(".checkbutton").fadeIn( "fast", function() {
              // Animation complete
          });
    }); 
    $(document).on("mouseleave", '.icon', function() {
    			$(this).find(".checkbutton").hide();
    });   
    */  

  function saveFieldChanges(that) {
  
  	// Object on td(cell)-> get sid
  	var my_sid=($(that).parent().parent().parent().find("td.sid")[0].innerHTML);

    // Object on td(cell)-> get owner
  	my_owner=($(that).parent().parent().parent().find(".selectuser option:selected" ).text());

    // Object on td(cell)-> get description
  	var my_description=($(that).parent().parent().parent().find("td.description input")[0].value);
  
    // Object on button -> get status
  	var my_status=($(that).parent().context.value);
  	if (my_status=="check") my_status=1; else my_status=0; 

    $(that).parent().parent().parent().find("td.owner").html('<div style="float:left;"><b>'+my_owner+'</b></div>');
    $(that).parent().parent().parent().find("td.description").html('<div style="float:left;"><b>'+my_description+'</b></div>');
    $(that).parent().hide();
    $("#RiskWrapper").show();
        
  	var lookup_search='index=alerts alert_actions=* sid="'+my_sid+'" | lookup searches_alerts.csv sid OUTPUT action_status | eval action_status='+my_status+' | eval owner="'+my_owner+'" | eval description="'+my_description+'" | fields sid, action_status, owner, description | outputlookup append=true searches_alerts.csv ';

    // splunkjs.mvc.Components.getInstance("lookupsearch1")
    lookupsearch1.set({"search": lookup_search});
    
    // Change icons
    lookupsearch1.on('search:done', function(properties) {

      $(that).parent().parent().find("i").removeClass("icon-alert unchecked");
    	$(that).parent().parent().find("i").addClass("icon-check checked");

    });
   
  }
   
  // Restart search when lookup saved
  lookupsearch1.on('search:done', function(properties) {
    action_counter-=1;
    if (action_counter<=0) 
    { 
      splunkjs.mvc.Components.getInstance("search1").startSearch();
      action_counter=0;
    }
    $("#RiskWrapper").hide();      
  });

  var riskwrapper='<div id="RiskWrapper"><div class="modal-backdrop fade in"></div><div class="modal disconnection-warning-modal">Data will be saved ... please wait ...<br /><div class="waiting"></div></div></div>';
  $('body').prepend(riskwrapper);
  
  var closer='<div class="closer icon-x"> close</div>';
  $(my_detail_id).prepend(closer);
  
  $(my_detail_id).on("click", '.closer', function() {
      // console.log ( $(my_detail_id).parent().parent().parent() );
      $(my_detail_id).parent().parent().parent().hide();
      // $(my_element_id).parent().parent().parent().width("100%");
  });  

  $(my_element_id).parent().parent().parent().addClass("fix_panel");
  $(my_detail_id).parent().parent().parent().addClass("float_panel");

});
