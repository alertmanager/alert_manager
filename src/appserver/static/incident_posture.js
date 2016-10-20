require.config({
    paths: {
        "app": "../app"
    },
    shim: {
        "select2": {
            deps: ['jquery', 'css!../select2/css/select2.min.css'],
            exports: "Select2"
        },
    }
});
require([
    "splunkjs/mvc",
    "splunkjs/mvc/utils",
    "splunkjs/mvc/tokenutils",
    "underscore",
    "jquery",
    'app/alert_manager/contrib/select2/js/select2.min',
    'models/SplunkDBase',
    'splunkjs/mvc/sharedmodels',    
    "splunkjs/mvc/simplexml",
    'splunkjs/mvc/tableview',
    'splunkjs/mvc/chartview',
    'splunkjs/mvc/searchmanager',
    'splunk.util',
    'splunkjs/mvc/simplexml/element/single',    
    'app/alert_manager/views/single_trend',
    'util/moment'   
], function(
        mvc,
        utils,
        TokenUtils,
        _,
        $,
        select2,
        SplunkDModel, 
        sharedModels,        
        DashboardController,
        TableView,
        ChartView,
        SearchManager,
        splunkUtil,
        SingleElement,
        TrendIndicator,
        moment         
    ) {

    // Tokens
    var submittedTokens = mvc.Components.getInstance('submitted', {create: true});
    var defaultTokens   = mvc.Components.getInstance('default', {create: true});

    var CustomConfModel = SplunkDModel.extend({
        urlRoot: 'configs/conf-alert_manager'
    });
    var settings = new CustomConfModel();
    settings.set('id', 'settings');
    var app = sharedModels.get('app');

    settings.fetch({
        data: {
            app: app.get('app'),
            owner: app.get('owner')
        }
    }).done(function(){
        var incident_list_length = settings.entry.content.get('incident_list_length');
        defaultTokens.set('incident_list_length', incident_list_length);
        submittedTokens.set('incident_list_length', incident_list_length);
    });

    var search_recent_alerts = mvc.Components.get('recent_alerts');
    search_recent_alerts.on("search:progress", function(properties) {
        var props = search_recent_alerts.job.properties(); 
        if (props.searchEarliestTime != undefined && props.searchLatestTime != undefined) {
            earliest  = props.searchEarliestTime;
            latest    = props.searchLatestTime;
            interval  = latest - earliest;
            trend_earliest = earliest - interval;
            trend_latest = earliest;

            if((defaultTokens.get('trend_earliest') == undefined || defaultTokens.get('trend_earliest') != trend_earliest) && (defaultTokens.get('trend_latest') == undefined || defaultTokens.get('trend_latest') != latest)) {
                defaultTokens.set('trend_earliest', trend_earliest);
                defaultTokens.set('trend_latest', trend_latest);
                submittedTokens.set(defaultTokens.toJSON());
            }
        }
    });
    
    // Closer
    var alert_details="#alert_details"; 
    var closer='<div class="closer icon-x"> close</div>';
    $(alert_details).prepend(closer);
    $(alert_details).on("click", '.closer', function() {
        $(alert_details).parent().parent().parent().hide();
    });  


    var IconRenderer = TableView.BaseCellRenderer.extend({
        canRender: function(cell) {
            // Only use the cell renderer for the specific field
            return (cell.field==="dosearch" || cell.field==="doedit" || cell.field == "owner");
        },
        render: function($td, cell) {
            if(cell.field=="owner") {
                if(cell.value!="unassigned") {
                    icon = 'user';
                    $td.addClass(cell.field).addClass('icon-inline').html(_.template('<i class="icon-<%-icon%>" style="padding-right: 2px"></i><%- text %>', {
                        icon: icon,
                        text: cell.value
                    }));                
                } else {
                    $td.addClass(cell.field).html(cell.value);
                }
            } else {
                if(cell.field=="dosearch") {
                    var icon = 'search';
                
                } else if (cell.field=="doedit") {
                    var icon = 'list';
                }
                var rendercontent='<div style="float:left; max-height:22px; margin:0px;"><i class="icon-<%-icon%>" >&nbsp;</i></div>';
                    
                $td.addClass('table_inline_icon').html(_.template(rendercontent, {
                    icon: icon
                }));   

                $td.on("click", function(e) {
                    console.log("event handler fired");
                    e.stopPropagation(); 
                    $td.trigger("iconclick", {"field": cell.field });
                });
            }            
        }
    });

    var HiddenCellRenderer = TableView.BaseCellRenderer.extend({
        canRender: function(cell) {
            // Only use the cell renderer for the specific field
            return (cell.field==="alert" || cell.field==="incident_id" || cell.field==="job_id" || cell.field==="result_id" 
                 || cell.field==="status"  || cell.field==="alert_time" || cell.field==="display_fields"
                 || cell.field==="search" || cell.field==="event_search" || cell.field==="earliest" 
                 || cell.field==="latest" || cell.field==="impact" || cell.field==="urgency" || cell.field==="app" || cell.field==="alert");
        },
        render: function($td, cell) {
            // ADD class to cell -> CSS
            $td.addClass(cell.field).html(cell.value);
        }
    });

     // Row Coloring Example with custom, client-side range interpretation
    var ColorRenderer = TableView.BaseCellRenderer.extend({
        canRender: function(cell) {
            // Enable this custom cell renderer for both the active_hist_searches and the active_realtime_searches field
            return _(['priority']).contains(cell.field);
        },
        render: function($td, cell) {
            // Add a class to the cell based on the returned value
            var value = cell.value;
            // Apply interpretation for number of historical searches
            if (cell.field === 'priority') {
                if (value == "informational") {
                    $td.addClass('range-cell').addClass('range-info');
                }
                else if (value == "low") {
                    $td.addClass('range-cell').addClass('range-low');
                }
                else if (value == "medium") {
                    $td.addClass('range-cell').addClass('range-medium');
                }
                else if (value == "high") {
                    $td.addClass('range-cell').addClass('range-high');
                }
                else if (value == "critical") {
                    $td.addClass('range-cell').addClass('range-critical');
                }
		        else if (value == "unknown") {
                    $td.addClass('range-cell').addClass('range-unknown');
                }
            }

            // Update the cell content
            //$td.text(value.toFixed(2)).addClass('numeric');
            $td.text(value);
        }
    });


    var IncidentDetailsExpansionRenderer = TableView.BaseRowExpansionRenderer.extend({
        initialize: function(args) {
            // initialize will run once, so we will set up a search and a chart to be reused.
            this._historySearchManager = new SearchManager({
                id: 'incident_history_exp_manager',
                preview: false
            });
            this._historyTableView = new TableView({
                id: 'incident_history_exp',
                managerid: 'incident_history_exp_manager',
                'drilldown': 'none'
            });

            this._detailsSearchManager = new SearchManager({
                id: 'incident_details_exp_manager',
                preview: false
            });
            this._detailsTableView = new TableView({
                id: 'incident_details_exp',
                managerid: 'incident_details_exp_manager',
                'drilldown': 'none'
            });
        },
        canRender: function(rowData) {
            return true;
        },
        render: function($container, rowData) {

            var incident_id = _(rowData.cells).find(function (cell) {
               return cell.field === 'incident_id';
            });

            var job_id = _(rowData.cells).find(function (cell) {
               return cell.field === 'job_id';
            });

            var result_id = _(rowData.cells).find(function (cell) {
               return cell.field === 'result_id';
            });

            var alert_time = _(rowData.cells).find(function (cell) {
               return cell.field === 'alert_time';
            });

            var impact = _(rowData.cells).find(function (cell) {
               return cell.field === 'impact';
            });

            var urgency = _(rowData.cells).find(function (cell) {
               return cell.field === 'urgency';
            });
            
            var alert = _(rowData.cells).find(function (cell) {
               return cell.field === 'alert';
            });

            var app = _(rowData.cells).find(function (cell) {
               return cell.field === 'app';
            });

            var display_fields = _(rowData.cells).find(function (cell) {
               return cell.field === 'display_fields';
            });

            console.debug("display_fields", display_fields.value);
         
            $("<h3 />").text('Details').appendTo($container);
            var contEl = $('<div />').attr('id','incident_details_exp_container');
            contEl.append($('<div />').css('float', 'left').text('incident_id=').append($('<span />').attr('id','incident_id_exp_container').addClass('incidentid').text(incident_id.value)));
            contEl.append($('<div />').css('float', 'left').text('impact=').append($('<span />').addClass('incident_details_exp').addClass('exp-impact').addClass(impact.value).text(impact.value)));
            contEl.append($('<div />').text('urgency=').append($('<span />').addClass('incident_details_exp').addClass('exp-urgency').addClass(urgency.value).text(urgency.value)));
            contEl.appendTo($container)
            
            if (display_fields.value != null && display_fields.value != "" && display_fields.value != " ") {
                $("<br />").appendTo($container);
                this._detailsSearchManager.set({ 
                    search: '| `incident_details('+incident_id.value +', "'+ display_fields.value +'")`',
                    earliest_time: '-1m',
                    latest_time: 'now'
                }); 
                $container.append(this._detailsTableView.render().el);          
            }
            $("<br />").appendTo($container);  

            var url = splunkUtil.make_url('/custom/alert_manager/helpers/get_savedsearch_description?savedsearch='+alert.value+'&app='+app.value);
            var desc = "";
            $.get( url,function(data) {
                desc = data;
                if (desc != "") {
                    $("<h3 />").text('Alert Description').appendTo($container);
                    $("<div />").attr('id','incident_details_description').addClass('incident_details_description').appendTo($container);
                    $("<br />").appendTo($container);
                    $("#incident_details_description").html(data);
                }
            });

            $("<h3>").text('History').appendTo($container);
            $("<div/>").text('Loading...').attr('id', 'loading-bar').appendTo($container);
            this._historySearchManager.set({ 
                search: '`incident_history('+ incident_id.value +')`',
                earliest_time: alert_time.value,
                latest_time: 'now'
            });  
            $container.append(this._historyTableView.render().el);           
            this._historySearchManager.on("search:done", function(state, job){
                $("#loading-bar").hide();
            });
        }
    });

    incidentsOverViewTable = mvc.Components.get('incident_overview');
    incidentsOverViewTable.getVisualization(function(tableView) {
        // Add custom cell renderer
        tableView.table.addCellRenderer(new ColorRenderer());
        tableView.table.addCellRenderer(new HiddenCellRenderer());
        tableView.table.addCellRenderer(new IconRenderer());
        tableView.addRowExpansionRenderer(new IncidentDetailsExpansionRenderer());

        tableView.table.render();

    });
    
    var rendered = false;
    incidentsOverViewTable.on("rendered", function(obj) { 
        if (settings.entry.content.get('incident_list_length') != undefined) {
            if(rendered == false) {
                rendered = true;
                obj.settings.set({ pageSize: settings.entry.content.get('incident_list_length') });
            }
        }
    });
    
    $(document).on("iconclick", "td", function(e, data) {
        
        // Displays a data object in the console
        
        console.log("field", data);

        if (data.field=="dobla1") {
            // Drilldown panel (loadjob)
            drilldown_job_id=($(this).parent().find("td.job_id")[0].innerHTML);
            submittedTokens.set("drilldown_job_id", drilldown_job_id);
            $(alert_details).parent().parent().parent().show();
        }
        else if (data.field=="dosearch"){
            // Drilldown search (search view)
            var drilldown_search=($(this).parent().find("td.search")[0].innerHTML);
            var drilldown_search_earliest=($(this).parent().find("td.earliest")[0].innerHTML);
            var drilldown_search_latest=($(this).parent().find("td.latest")[0].innerHTML);
            var drilldown_app=($(this).parent().find("td.app")[0].innerHTML);

            // Set default app to search if cannot be evaluated
            if (drilldown_app == undefined || drilldown_app == "") {
                drilldown_app = "search";
            }
            
            drilldown_search = drilldown_search.replace("&gt;",">").replace("&lt;","<");
            drilldown_search = encodeURIComponent(drilldown_search);

            var search_url="search?q=search "+drilldown_search+"&earliest="+drilldown_search_earliest+"&latest="+drilldown_search_latest;
            var url = splunkUtil.make_url('/app/' + drilldown_app + '/' + search_url);

            window.open(url,'_search');

        }
        else if (data.field=="doedit"){
            console.log("doedit catched");
            // Incident settings
            var incident_id =   $(this).parent().find("td.incident_id").get(0).textContent;
            var owner =    $(this).parent().find("td.owner").get(0).textContent;            
            var urgency = $(this).parent().find("td.urgency").get(0).textContent;
            var status =   $(this).parent().find("td.status").get(0).textContent;

            var edit_panel='' +
'<div class="modal fade modal-wide shared-alertcontrols-dialogs-editdialog in" id="edit_panel">' +
'    <div class="modal-content">' +
'      <div class="modal-header">' +
'        <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>' +
'        <h4 class="modal-title" id="exampleModalLabel">Edit Incident</h4>' +
'      </div>' +
'      <div class="modal-body modal-body-scrolling">' +
'        <div class="form form-horizontal form-complex" style="display: block;">' +
'          <div class="control-group shared-controls-controlgroup">' +
'            <label for="incident_id" class="control-label">Incident:</label>' +
'            <div class="controls controls-block"><div class="control shared-controls-labelcontrol" id="incident_id"><span class="input-label-incident_id">' + incident_id + '</span></div></div>' +
'          </div>' +
'          <div class="control-group shared-controls-controlgroup">' +
'            <label for="message-text" class="control-label">Urgency:</label>' +
'            <div class="controls"><select name="urgency" id="urgency" disabled="disabled"></select></div>' +
'          </div>' +
'          <p class="control-heading">Incident Workflow</p>'+
'          <div class="control-group shared-controls-controlgroup">' +
'            <label for="recipient-name" class="control-label">Owner:</label>' +
'            <div class="controls"><select name="owner" id="owner" disabled="disabled"></select></div>' +
'          </div>' +
'          <div class="control-group shared-controls-controlgroup">' +
'            <label for="message-text" class="control-label">Status:</label>' +
'            <div class="controls"><select name="status" id="status" disabled="disabled"></select></div>' +
'          </div>' +
'          <div class="control-group shared-controls-controlgroup">' +
'            <label for="message-text" class="control-label">Comment:</label>' +
'            <div class="controls"><textarea type="text" name="comment" id="comment" class="" placeholder="optional"></textarea></div>' +
'          </div>' +
'        </div>' +
'      </div>' +
'      <div class="modal-footer">' +
'        <button type="button" class="btn cancel modal-btn-cancel pull-left" data-dismiss="modal">Cancel</button>' +
'        <button type="button" class="btn btn-primary" id="modal-save">Save</button>' +
'      </div>' +
'    </div>' +
'</div>';
            $('body').prepend(edit_panel);

            $("#owner").select2();
            var url = splunkUtil.make_url('/custom/alert_manager/helpers/get_users');
            $.get( url,function(data) { 
                
                var users = new Array();
                users.push("unassigned");

                _.each(data, function(el) { 
                    users.push(el.name);
                });

                _.each(users, function(user) { 
                    if (user == owner) {
                        $('#owner').append( $('<option></option>').attr("selected", "selected").val(user).html(user) )
                        $('#owner').select2('data', {id: user, text: user});
                    } else {
                        $('#owner').append( $('<option></option>').val(user).html(user) )
                    }
                });
                $("#owner").prop("disabled", false);  
            }, "json");

            var all_urgencies = [ "low" ,"medium", "high" ]
            $.each(all_urgencies, function(key, val) {
                if (val == urgency) {
                    $('#urgency').append( $('<option></option>').attr("selected", "selected").val(val).html(val) )
                } else {
                    $('#urgency').append( $('<option></option>').val(val).html(val) )
                }
                $("#urgency").prop("disabled", false); 
            }); //

            var all_status = { "new": "New", "assigned":"Assigned", "work_in_progress":"Work in progress", "on_hold": "On hold", "resolved":"Resolved" }
            if (status == "auto_assigned") { status = "assigned"; }
            $.each(all_status, function(val, text) {
                if (val == status) {
                    $('#status').append( $('<option></option>').attr("selected", "selected").val(val).html(text) )
                } else {
                    $('#status').append( $('<option></option>').val(val).html(text) )
                }
                $("#status").prop("disabled", false); 
            }); //

            $('#owner').on("change", function() { 
                if($( this ).val() == "unassigned") {
                    $('#status').val('new');
                } else {
                    $('#status').val('assigned');
                }
            });
            $('#edit_panel').modal('show');
        }
    });
    
    $(document).on("click", "#modal-save", function(event){
        // save data here
        var incident_id = $("#incident_id > span").html();
        var owner  = $("#owner").val();
        var urgency  = $("#urgency").val();
        var status  = $("#status").val();
        var comment  = $("#comment").val();
        
        if(incident_id == "" || owner == "" || urgency == "" || status == "") {
            alert("Please choose a value for all required fields!");
            return false;
        }

        var update_entry = { 'incident_id': incident_id, 'owner': owner, 'urgency': urgency, 'status': status, 'comment': comment };
        console.debug("entry", update_entry);
        //debugger;
        data = JSON.stringify(update_entry);
        var post_data = {
            contents    : data
        };

        var url = splunkUtil.make_url('/custom/alert_manager/incident_workflow/save');
        console.debug("url", url);

        $.ajax( url,
            {
                uri:  url,
                type: 'POST',
                data: post_data,
                
                success: function(jqXHR, textStatus){
                    // Reload the table                        
                    mvc.Components.get("recent_alerts").startSearch();
                    mvc.Components.get("base_single_search").startSearch();
                    $('#edit_panel').modal('hide');
                    $('#edit_panel').remove();
                    console.debug("success");
                },
                
                // Handle cases where the file could not be found or the user did not have permissions
                complete: function(jqXHR, textStatus){
                    console.debug("complete");
                },
                
                error: function(jqXHR,textStatus,errorThrown) {
                    console.log("Error");
                } 
            }
        );

    });


});
