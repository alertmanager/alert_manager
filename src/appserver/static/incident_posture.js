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
    'app/alert_manager/views/single_trend',
    'splunkjs/mvc/simplexml/element/single',
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

    // Tracker num used to create unique id names for display elements/tableview objects/searchmanager objects
    var tracker_num = 0

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


    var IconRenderer = TableView.BaseCellRenderer.extend({
        canRender: function(cell) {
            // Only use the cell renderer for the specific field
            return (cell.field==="dosearch" || cell.field==="doedit" || cell.field == "owner" || cell.field == "doquickassign" || cell.field == "doexternalworkflowaction");
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
                } else if (cell.field=="doquickassign") {
                    var icon = 'user';
                } else if (cell.field=="doexternalworkflowaction") {
                    var icon = 'external';
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

            this._detailsSearchManager = new SearchManager({
                id: 'incident_details_exp_manager',
                preview: false
            });

            this._historySearchManager = new SearchManager({
                id: 'incident_history_exp_manager',
                preview: false
            });
        },
        canRender: function(rowData) {
            return true;
        },
        setup: function($container,rowData) {

            incident_id = _(rowData.cells).find(function (cell) {
               return cell.field === 'incident_id';
            });

            job_id = _(rowData.cells).find(function (cell) {
               return cell.field === 'job_id';
            });

            result_id = _(rowData.cells).find(function (cell) {
               return cell.field === 'result_id';
            });

            alert_time = _(rowData.cells).find(function (cell) {
               return cell.field === 'alert_time';
            });

            impact = _(rowData.cells).find(function (cell) {
               return cell.field === 'impact';
            });

            urgency = _(rowData.cells).find(function (cell) {
               return cell.field === 'urgency';
            });

            alert = _(rowData.cells).find(function (cell) {
               return cell.field === 'alert';
            });

            app = _(rowData.cells).find(function (cell) {
               return cell.field === 'app';
            });

            display_fields = _(rowData.cells).find(function (cell) {
               return cell.field === 'display_fields';
            });

            console.log("alert_time", alert_time.value);
            console.log("incident_id", incident_id.value);
            console.log("display_fields", display_fields.value);

            //
            // Details starts here
            //

            $("<h3 />").text('Details').appendTo($container);

            var contEl = $('<div />').attr('id','incident_details_exp_container');
            contEl.append($('<div />').css('float', 'left').text('incident_id=').append($('<span />').attr('id','incident_id_exp_container').addClass('incidentid').text(incident_id.value)));
            contEl.append($('<div />').css('float', 'left').text('impact=').append($('<span />').addClass('incident_details_exp').addClass('exp-impact').addClass(impact.value).text(impact.value)));
            contEl.append($('<div />').text('urgency=').append($('<span />').addClass('incident_details_exp').addClass('exp-urgency').addClass(urgency.value).text(urgency.value)));
            contEl.appendTo($container)

            // John Landers: Added a loading bar for when the search load takes too long
            $("<div/>").text('Loading...').attr('id', 'loading-bar-details').appendTo($container);

            // John Landers: Made the definition of display fields optional. Requries an additional incident_details(1) macro be created
            if (display_fields.value != null && display_fields.value != "" && display_fields.value != " ") {
                var search_string = '| `incident_details('+incident_id.value +', "'+ display_fields.value +'")`'
            } else {
                var search_string = '| `incident_details('+incident_id.value +')`'
            }

            console.log("search_string:", search_string)
            console.log("alert_time:",alert_time.value)
            console.log("earliest:",parseInt(alert_time.value)-600)
            console.log("latest:", parseInt(alert_time.value)+600)

            // John Landers: Modified search times all around to handle variation in alert_time verse index_time
            // this is important if you switch result loading from KV store to indexed data
            $("<br />").appendTo($container);

            this._detailsSearchManager.set({
                search: search_string,
                earliest_time: parseInt(alert_time.value)-600,
                latest_time: parseInt(alert_time.value)+600,
                autostart: false
            });

            this._detailsSearchManager.startSearch();

            this._detailsTableView = new TableView({
                id: 'incident_details_exp_'+incident_id.value+'_'+Date.now(),
                managerid: 'incident_details_exp_manager',
                'drilldown': 'none',
                'wrap': true,
                'displayRowNumbers': true,
                'pageSize': '50',
                //'el': $("#incident_details_exp")
            });

            this._detailsSearchManager.on("search:start", function(state, job){
                console.log("Detail Search starting...")
            });

            $container.append(this._detailsTableView.render().el);

            //
            // History starts here
            //

            $('<br />').appendTo($container);
            $("<h3>").text('History').appendTo($container);
            $("<div/>").text('Loading...').attr('id', 'loading-bar-history').appendTo($container);

            history_search_string = '| `incident_history('+ incident_id.value +')`'

            this._historySearchManager.set({
                search: history_search_string,
                earliest_time: parseInt(alert_time.value)-600,
                latest_time: 'now',
                autostart: false

            });

            this._historySearchManager.startSearch();

            this._historyTableView = new TableView({
                id: 'incident_history_exp_'+incident_id.value+'_'+Date.now(),
                managerid: 'incident_history_exp_manager',
                'drilldown': 'none',
                'wrap': true,
                'displayRowNumbers': true,
                'pageSize': '50',
                //'el': $("#incident_history_exp")
            });

            var url = splunkUtil.make_url('/splunkd/__raw/services/helpers?action=get_savedsearch_description&savedsearch_name='+alert.value+'&app='+app.value);
            var desc = "";
            $.get( url,function(data) {
                desc = data;
                if (desc != "") {
                    $("<br />").appendTo($container);
                    $("<h3 />").text('Alert Description').appendTo($container);
                    $("<div />").attr('id','incident_details_description').addClass('incident_details_description').appendTo($container);
                    $("<br />").appendTo($container);
                    $("#incident_details_description").html(data);
                }
            });

            $container.append(this._historyTableView.render().el);
        },
        render: function($container, rowData) {

            this._detailsSearchManager.on("search:done", function(state, job){
                $("#loading-bar-details").hide();
            });


            this._historySearchManager.on("search:done", function(state, job){
                $("#loading-bar-history").hide();
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

            var search_url="search?q="+drilldown_search+"&earliest="+drilldown_search_earliest+"&latest="+drilldown_search_latest;
            var url = splunkUtil.make_url('/app/' + drilldown_app + '/' + search_url);

            window.open(url,'_search');

        }
        else if (data.field=="doquickassign") {
            var incident_id =   $(this).parent().find("td.incident_id").get(0).textContent;
            var urgency = $(this).parent().find("td.urgency").get(0).textContent;
            var status = "assigned";
            var comment = "Assigning for review"
            var owner=Splunk.util.getConfigValue("USERNAME");

            console.log("Username: ", owner)
            var update_entry = { 'incident_id': incident_id, 'owner': owner, 'urgency': urgency, 'status': status, 'comment': comment };
            console.log("entry", update_entry);
            //debugger;
            data = JSON.stringify(update_entry);
            var post_data = {
                contents    : data
            };

            var url = splunkUtil.make_url('/custom/alert_manager/incident_workflow/save');
            console.log("url", url);

            $.ajax( url,
                {
                    uri:  url,
                    type: 'POST',
                    data: post_data,

                    success: function(jqXHR, textStatus){
                        // Reload the table
                        mvc.Components.get("recent_alerts").startSearch();
                        console.log("success");
                    },

                    // Handle cases where the file could not be found or the user did not have permissions
                    complete: function(jqXHR, textStatus){
                        console.log("complete");
                    },

                    error: function(jqXHR,textStatus,errorThrown) {
                        console.log("Error");
                    }
                }
            );
        }
        else if (data.field=="doedit"){
            console.log("doedit catched");
            // Incident settings
            var incident_id =   $(this).parent().find("td.incident_id").get(0).textContent;
            var owner =    $(this).parent().find("td.owner").get(0).textContent;
            var urgency = $(this).parent().find("td.urgency").get(0).textContent;
            var status =   $(this).parent().find("td.status").get(0).textContent;

            var status_ready = false;
            var owner_ready = false;

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
'            <label for="urgency" class="control-label">Urgency:</label>' +
'            <div class="controls"><select name="urgency" id="urgency" disabled="disabled"></select></div>' +
'          </div>' +
'          <p class="control-heading">Incident Workflow</p>'+
'          <div class="control-group shared-controls-controlgroup">' +
'            <label for="owner" class="control-label">Owner:</label>' +
'            <div class="controls"><select name="owner" id="owner" disabled="disabled"></select></div>' +
'          </div>' +
'          <div class="control-group shared-controls-controlgroup">' +
'            <label for="status" class="control-label">Status:</label>' +
'            <div class="controls"><select name="status" id="status" disabled="disabled"></select></div>' +
'          </div>' +
'          <div class="control-group shared-controls-controlgroup">' +
'            <label for="comment" class="control-label">Comment:</label>' +
'            <div class="controls"><textarea type="text" name="comment" id="comment" class=""></textarea></div>' +
'          </div>' +
'        </div>' +
'      </div>' +
'      <div class="modal-footer">' +
'        <button type="button" class="btn cancel modal-btn-cancel pull-left" data-dismiss="modal">Cancel</button>' +
'        <button type="button" class="btn btn-primary" id="modal-save" disabled>Save</button>' +
'      </div>' +
'    </div>' +
'</div>';
            $('body').prepend(edit_panel);

            // Get list of users and prepare dropdown
            $("#owner").select2();
            var owner_url = splunkUtil.make_url('/splunkd/__raw/services/helpers?action=get_users');
            var owner_xhr = $.get( owner_url, function(data) {

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
                owner_ready = true;
                //$("body").trigger({type: "ready_change" });
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

            // John Landers: Modified how the alert status list is handled; now pulls from KV store
            var status_url = splunkUtil.make_url('/splunkd/__raw/services/helpers?action=get_status');
            var status_xhr = $.get( status_url, function(data) {
               if (status == "auto_assigned") { status = "assigned"; }

               _.each(data, function(val, text) {
                    if (val['status'] == status) {
                        $('#status').append( $('<option></option>').attr("selected", "selected").val(val['status']).html(val['status_description']) )
                    } else {
                        $('#status').append( $('<option></option>').val(val['status']).html(val['status_description']) )
                    }
                    $("#status").prop("disabled", false);
                });

            }, "json");

            // Wait for owner and status to be ready
            $.when(status_xhr, owner_xhr).done(function() {
              console.log("status and owner are ready");
              $('#modal-save').prop('disabled', false);
            });

            // Change status when new owner is selected
            $('#owner').on("change", function() {
                console.log("chagne event fired on #owner");
                if($( this ).val() == "unassigned") {
                    $('#status').val('new');
                } else {
                    $('#status').val('assigned');
                }
            });

            // Finally show modal
            $('#edit_panel').modal('show');
        }

        else if (data.field=="doexternalworkflowaction"){
            console.log("doexternalworkflowaction catched");
            // Incident settings
            var incident_id = $(this).parent().find("td.incident_id").get(0).textContent;

            var actions_ready = false;

            var externalworkflowaction_panel='' +
'<div class="modal fade modal-wide shared-alertcontrols-dialogs-externalworkflowactiondialog in" id="externalworkflowaction_panel">' +
'    <div class="modal-content">' +
'      <div class="modal-header">' +
'        <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>' +
'        <h4 class="modal-title" id="exampleModalLabel">Execute External Workflow Action</h4>' +
'      </div>' +
'      <div class="modal-body modal-body-scrolling">' +
'        <div class="form form-horizontal form-complex" style="display: block;">' +
'          <div class="control-group shared-controls-controlgroup">' +
'            <label for="incident_id" class="control-label">Incident:</label>' +
'            <div class="controls controls-block"><div class="control shared-controls-labelcontrol" id="workflow_incident_id"><span class="input-label-incident_id">' + incident_id + '</span></div></div>' +
'          </div>' +
'          <div class="control-group shared-controls-controlgroup">' +
'            <label for="message-text" class="control-label">Select Action:</label>' +
'            <div class="controls"><select name="externalworkflowaction" id="externalworkflowaction" disabled="disabled"></select></div>' +
'          </div>' +
'          <div class="control-group shared-controls-controlgroup">' +
'            <label for="message-text" class="control-label">Command:</label>' +
'            <div class="controls"><textarea type="text" name="externalworkflowaction_command" id="externalworkflowaction_command" class=""></textarea></div>' +
'          </div>' +
'        </div>' +
'      </div>' +
'      <div class="modal-footer">' +
'        <button type="button" class="btn cancel modal-btn-cancel pull-left" data-dismiss="modal">Cancel</button>' +
'        <button type="button" class="btn btn-primary" id="modal-execute" disabled>Execute</button>' +
'      </div>' +
'    </div>' +
'</div>';

            $('body').prepend(externalworkflowaction_panel);

            $('#externalworkflowaction').append('<option value="-">-</option>');


            $("#externalworkflowaction").select2();
            var externalworkflowaction_url = splunkUtil.make_url('/splunkd/__raw/services/helpers?action=get_externalworkflowaction_settings');
            var externalworkflowaction_xhr = $.get( externalworkflowaction_url, function(data) {

               _.each(data, function(val, text) {
                    $('#externalworkflowaction').append( $('<option></option>').val(val['title']).html(val['label']) );
                    $("#externalworkflowaction").prop("disabled", false)
                });

                actions_ready = true;

            }, "json");


            // Wait for externalworkflowaction to be ready
            $.when(actions_ready).done(function() {
                console.log("externalworkflowaction is ready");
                $('#modal-execute').prop('disabled', false);
            });

	          $('#externalworkflowaction_command').prop('readonly',true);
            $('#externalworkflowaction').on('change', function() {
               console.log("change event fired on #externalworkflowaction");
               var incident_id = $("#workflow_incident_id > span").html();
               console.log("Incident ID: ", incident_id);

               value = $("#externalworkflowaction").val()
               label = $("#externalworkflowaction option:selected").text();
               console.log("#externalworkflowaction val:", value);
               console.log("#externalworkflowaction label:", label);
               if (label!="-"){
                 console.log("Getting workflowaction command...");
                 var externalworkflowaction_command_url = splunkUtil.make_url('/splunkd/__raw/services/helpers?action=get_externalworkflowaction_command&incident_id='+incident_id+'&externalworkflowaction='+value);
                 $.get( externalworkflowaction_command_url, function(data, status) {
                   console.log("Retrieved command:", data);
                   $('#externalworkflowaction_command').val(data);
                 }, "text");
               }

            });

            // Finally show modal
            $('#externalworkflowaction_panel').modal('show');
        }
    });


    $(document).on("click", "#modal-save", function(event){
        // save data here
        var incident_id = $("#incident_id > span").html();
        var owner  = $("#owner").val();
        var urgency  = $("#urgency").val();
        var status  = $("#status").val();
        var comment  = $("#comment").val();

        // John Landers: Added comment == "" to make comments required
        // simcen: Changed back to not require comment
        if(incident_id == "" || owner == "" || urgency == "" || status == "") {
            alert("Please choose a value for all required fields!");
            return false;
        }

        var update_entry = { 'incident_id': incident_id, 'owner': owner, 'urgency': urgency, 'status': status, 'comment': comment };
        console.log("entry", update_entry);
        //debugger;
        data = JSON.stringify(update_entry);
        var post_data = {
            contents    : data
        };

        var url = splunkUtil.make_url('/custom/alert_manager/incident_workflow/save');
        console.log("url", url);

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

                    console.log("success");
                },

                // Handle cases where the file could not be found or the user did not have permissions
                complete: function(jqXHR, textStatus){
                    console.log("complete");
                },

                error: function(jqXHR,textStatus,errorThrown) {
                    console.log("Error");
                }
            }
        );

    });



    $(document).on("click", "#modal-execute", function(event){
        var incident_id = $("#workflow_incident_id > span").html();
        var command  = $("#externalworkflowaction_command").val();

        if(command == "") {
            alert("Please choose a value for all required fields!");
            return false;
        }

	      manager = new SearchManager({
					id: 'externalworkflowaction_' + incident_id +'_' + Date.now(),
                                        preview: false,
                                        autostart: false,
                                        search: command,
                                        earliest_time: '-1m',
                                        latest_time: 'now'
                                    });
        manager.startSearch();
	      manager = null;

	      var log_event_url = splunkUtil.make_url('/splunkd/__raw/services/helpers');
          var post_data = {
              action     : 'write_log_entry',
              log_action : 'comment',
              origin      : 'externalworkflowaction',
              incident_id: incident_id,
              comment    : label + ' workflowaction executed'

          };
	      $.post( log_event_url, post_data, function(data, status) { return "Executed"; }, "text");


        $('#externalworkflowaction_panel').modal('hide');
        $('#externalworkflowaction_panel').remove();
    });

});
