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

    // Add Attribute Filter description
    var AttributeFilterTooltip = $('#attribute_filter_tooltip');
	AttributeFilterTooltip.addClass("btnModalInfo");
	AttributeFilterTooltip.attr("href", "#");
    AttributeFilterTooltip.attr("title",  "Attribute Filter follows search command syntax, e.g. title=Alert*\" OR title=Alarm*");
	AttributeFilterTooltip.attr("data-toggle", "modal");
	AttributeFilterTooltip.attr("data-target", "#desc3");
    $("label:contains('Attribute Filter:')").after($("#attribute_filter_tooltip"));
    $("label:contains('Attribute Filter:')").attr("style","float:left");
	$('#attribute_filter_tooltip').tooltip();

    // Add Result Filter description
    var ResultFilterTooltip = $('#result_filter_tooltip');
	ResultFilterTooltip.addClass("btnModalInfo");
	ResultFilterTooltip.attr("href", "#");
    ResultFilterTooltip.attr("title",  "Result Filter follows search command syntax, e.g. count>10 OR host=myhost* NOTE: Double-quotes (\") have to be masked with backslashes (\\)");
	ResultFilterTooltip.attr("data-toggle", "modal");
    ResultFilterTooltip.attr("data-target", "#desc3");
    $("label:contains('Result Filter:')").after($("#result_filter_tooltip"));
    $("label:contains('Result Filter:')").attr("style","float:left");
	$('#result_filter_tooltip').tooltip();

    var IconRenderer = TableView.BaseCellRenderer.extend({
        canRender: function(cell) {
            // Only use the cell renderer for the specific field
            return (cell.field==="dosearch" || cell.field==="dobulkedit" || cell.field==="doedit" || cell.field == "owner" || cell.field == "doquickassign" || cell.field == "doexternalworkflowaction");
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
            } else if(cell.field=="dobulkedit") {
                //var incident_id =   $(this).parent().find("td.incident_id").get(0).textContent;
                //console.log("incident_id", cell.parent());
                $td.addClass('bulk_edit_incidents');
                $td.html('<input type="checkbox" class="bulk_edit_incidents" id="bulk_edit_incidents" name="bulk_edit_incidents" value=""></input>')
                $td.on("click", function(e) {
                    e.stopPropagation();
                    $td.trigger("alert_manager_events", {"action": cell.field });
                    $td.trigger("bulkedit_change", {"action": cell.field });
                });
            } else {
                if(cell.field=="dosearch") {
                    var icon = 'search';
                    var tooltip = 'Run Incident Search';
                } else if (cell.field=="doedit") {
                    var icon = 'list';
                    var tooltip = "Edit Incident";
                } else if (cell.field=="doquickassign") {
                    var icon = 'user';
                    var tooltip = "Assign to me";
                } else if (cell.field=="doexternalworkflowaction") {
                    var icon = 'external';
                    var tooltip = "Run External Workflow Action";
                }

                var rendercontent = '<a class="btn-pill" data-toggle="tooltip" data-placement="top" title="<%-tooltip%>"><i class="icon-<%-icon%>"></i><span class="hide-text">Inspect</span></a>';
                //var rendercontent='<div style="float:left; max-height:22px; margin:0px;"><i class="icon-<%-icon%>" >&nbsp;</i></div>';

                $td.addClass('table_inline_icon').html(_.template(rendercontent, {
                    icon: icon,
                    tooltip: tooltip
                }));

                $td.children('[data-toggle="tooltip"]').tooltip();

                $td.on("click", function(e) {
                    console.log("event handler fired");
                    e.stopPropagation();
                    $td.trigger("alert_manager_events", {"action": cell.field });
                });
            }
        }
    });

    var HiddenCellRenderer = TableView.BaseCellRenderer.extend({
        canRender: function(cell) {
            // Only use the cell renderer for the specific field
            return (cell.field==="alert" || cell.field==="incident_id" || cell.field==="job_id" || cell.field==="result_id"
                 || cell.field==="status" || cell.field==="alert_time" || cell.field==="display_fields"
                 || cell.field==="search" || cell.field==="event_search" || cell.field==="earliest"
                 || cell.field==="latest" || cell.field==="impact" || cell.field==="urgency" || cell.field==="app"
                 || cell.field==="alert" || cell.field==="external_reference_id" || cell.field==="duplicate_count"
                 || cell.field==="earliest_alert_time" || cell.field==="first_seen" || cell.field==="group");

        },
        render: function($td, cell) {
            // ADD class to cell -> CSS
            if (cell.field == 'alert') {
                $td.addClass('alert_cell').html(cell.value); 
            } else {
                $td.addClass(cell.field).html(cell.value);
            }
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

            group = _(rowData.cells).find(function (cell) {
                return cell.field === 'group';
             });

            external_reference_id = _(rowData.cells).find(function (cell) {
                return cell.field === 'external_reference_id';
             });

            duplicate_count = _(rowData.cells).find(function (cell) {
                return cell.field === 'duplicate_count';
             });

            earliest_alert_time = _(rowData.cells).find(function (cell) {
                return cell.field === 'earliest_alert_time';
             });

            first_seen = _(rowData.cells).find(function (cell) {
                return cell.field === 'first_seen';
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
            if (group.value != null){
                contEl.append($('<div />').css('float', 'left').text('group=').append($('<span />').addClass('group_exp').addClass('exp-group').addClass(group.value).text(group.value)));
            }
            if (external_reference_id.value != null){
                contEl.append($('<div />').css('float', 'left').text('external_reference_id=').append($('<span />').addClass('incident_details_exp').addClass('exp-external_reference_id').addClass(external_reference_id.value).text(external_reference_id.value)));
            }
            if (duplicate_count.value != null){
                contEl.append($('<div />').css('float', 'left').text('first_seen=').append($('<span />').addClass('incident_details_exp').addClass('exp-first_seen').addClass(first_seen.value).text(first_seen.value)));
                contEl.append($('<div />').css('float', 'left').text('duplicate_count=').append($('<span />').addClass('incident_details_exp').addClass('exp-duplicate_count').addClass(duplicate_count.value).text(duplicate_count.value)));
            }
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

            console.log("earliest_alert_time %s...", earliest_alert_time.value)

            this._historySearchManager.set({
                search: history_search_string,
                earliest_time: earliest_alert_time.value,
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
                'pageSize': '10',
                //'el': $("#incident_history_exp")
            });

            var url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers?action=get_savedsearch_description&savedsearch_name='+alert.value+'&app='+app.value);
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
        tableView.table.addCellRenderer(new HiddenCellRenderer());
        tableView.table.addCellRenderer(new IconRenderer());
        tableView.addRowExpansionRenderer(new IncidentDetailsExpansionRenderer());

        tableView.table.render();

    });

    var rendered = false;
    incidentsOverViewTable.on("rendered", function(obj) {
        //$("th[data-sort-key='dobulkedit']").html('<input type="checkbox" id="bulk_edit_select_all" />');
        if (settings.entry.content.get('incident_list_length') != undefined) {
            if(rendered == false) {
                rendered = true;
                obj.settings.set({ pageSize: settings.entry.content.get('incident_list_length') });
            }
        }
    });

    $(document).on("alert_manager_events", "td, button", function(e, data) {

        // Displays a data object in the console

        console.log("field", data);

        if (data.action=="dobulkedit") {
            var incident_id =   $(this).parent().find("td.incident_id").get(0).textContent;
            $(this).parent().find("td.bulk_edit_incidents").children("input").val(incident_id)
            console.log("this", $(this).parent().find("td.bulk_edit_incidents").children("input").val());
        } else if (data.action=="dobla1") {
            // Drilldown panel (loadjob)
            drilldown_job_id=($(this).parent().find("td.job_id")[0].innerHTML);
            submittedTokens.set("drilldown_job_id", drilldown_job_id);
            $(alert_details).parent().parent().parent().show();
        }
        else if (data.action=="dosearch"){
            // Drilldown search (search view)
            var incident_id =   $(this).parent().find("td.incident_id").get(0).textContent;
            var alert_time=($(this).parent().find("td.alert_time")[0].innerHTML);
            var drilldown_search=($(this).parent().find("td.search")[0].innerHTML);
            var drilldown_search_earliest=($(this).parent().find("td.earliest")[0].innerHTML);
            var drilldown_search_latest=($(this).parent().find("td.latest")[0].innerHTML);
            var drilldown_app=($(this).parent().find("td.app")[0].innerHTML);

            if (drilldown_search_earliest == '1970-01-01T01:00:00.000+01:00') {
                drilldown_search_latest = alert_time;
                drilldown_search_earliest = parseInt(alert_time)-1;
            }
            console.log("alert_time", alert_time);
            console.log("earliest", drilldown_search_earliest);
            console.log("latest", drilldown_search_latest);

            // Set default app to search if cannot be evaluated
            if (drilldown_app == undefined || drilldown_app == "") {
                drilldown_app = "search";
            }

            // Get Search string
            var url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers?action=get_search_string&incident_id='+incident_id);
            var drilldown_search = "";
            $.get( url,function(data) {
                console.log("data", data);
                var drilldown_search = data;
                if (drilldown_search != '') {
                    drilldown_search = drilldown_search.replace("&gt;",">").replace("&lt;","<");
                    drilldown_search = encodeURIComponent(drilldown_search);

                    var search_url="search?q="+drilldown_search+"&earliest="+drilldown_search_earliest+"&latest="+drilldown_search_latest;
                    var url = splunkUtil.make_url('/app/' + drilldown_app + '/' + search_url);

                    window.open(url,'_search');
                } else {
                    alert("Search String is empty, can't drilldown.");
                }
            }).fail(function() {
                alert("Was not able to retrieve search string. Maybe this is an old alert?!");
            });

        }
        else if (data.action=="doquickassign") {
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
            var rest_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers');
            var post_data = {
                action        : 'update_incident',
                incident_data : data,
            };
  	        $.post( rest_url, post_data, function(data, status) {
                mvc.Components.get("recent_alerts").startSearch();
            }, "text");

        }
        else if (data.action=="doedit"){
            console.log("doedit catched");
            if (data.incident_ids != undefined) {
                console.log("Bulk edit call");
                var bulk = true;
                var incident_id = data.incident_ids.join(', <br />');
                var incident_ids_string = data.incident_ids.join(':');
                var owner = '(unchanged)';
                var urgency = '(unchanged)';
                var status = '(unchanged)';
                var modal_title = "Incidents";
                var modal_id = "incident_ids";
            } else {
            // Incident settings
                var bulk = false;
                var incident_id =   $(this).parent().find("td.incident_id").get(0).textContent;
                var incident_ids_string = incident_id;
                var owner =    $(this).parent().find("td.owner").get(0).textContent;
                var urgency = $(this).parent().find("td.urgency").get(0).textContent;
                var status =   $(this).parent().find("td.status").get(0).textContent;
                var modal_title = "Incident";
                var modal_id = "incident_id";
            }
            var status_ready = false;
            var owner_ready = false;

            var edit_panel='' +
'<div class="modal fade modal-wide shared-alertcontrols-dialogs-editdialog in" id="edit_panel">' +
'    <div class="modal-content">' +
'      <div class="modal-header">' +
'        <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>' +
'        <h4 class="modal-title" id="exampleModalLabel">Edit '+ modal_title + '</h4>' +
'      </div>' +
'      <div class="modal-body modal-body-scrolling">' +
'        <div class="form form-horizontal form-complex" style="display: block;">' +
'          <div class="control-group shared-controls-controlgroup">' +
'            <label for="incident_id" class="control-label">'+ modal_title + ':</label>' +
'            <div class="controls controls-block"><input type="hidden" id="incident_ids" value="'+incident_ids_string+'" /><div class="control shared-controls-labelcontrol" id="'+ modal_id + '"><span class="input-label-incident_id">' + incident_id + '</span></div></div>' +
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
            var owner_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers?action=get_users');
            var owner_xhr = $.get( owner_url, function(data) {

                var users = new Array();
                if (bulk) {
                    users.push("(unchanged)");
                }
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

            if (bulk) {
                var all_urgencies = [ "(unchanged)", "low" ,"medium", "high" ]
            } else {
                var all_urgencies = [ "low" ,"medium", "high" ]
            }
            $.each(all_urgencies, function(key, val) {
                if (val == urgency) {
                    $('#urgency').append( $('<option></option>').attr("selected", "selected").val(val).html(val) )
                } else {
                    $('#urgency').append( $('<option></option>').val(val).html(val) )
                }
                $("#urgency").prop("disabled", false);
            }); //

            // John Landers: Modified how the alert status list is handled; now pulls from KV store
            var status_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/alert_status?action=get_alert_status');
            var status_xhr = $.get( status_url, function(data) {
               if (status == "auto_assigned") { status = "assigned"; }

               if (bulk) {
                   $('#status').append( $('<option></option>').attr("selected", "selected").val('(unchanged)').html('(unchanged)') );
               }

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

        else if (data.action=="doexternalworkflowaction"){
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
'            <div class="controls"><select name="externalworkflowactions" id="externalworkflowactions" disabled="disabled"></select></div>' +
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

            $('#externalworkflowactions').append('<option value="-">-</option>');


            $("#externalworkflowactions").select2();
            var externalworkflowaction_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/externalworkflow_actions?action=get_externalworkflow_actions');
            var externalworkflowaction_xhr = $.get( externalworkflowaction_url, function(data) {

               _.each(data, function(val, text) {
                    $('#externalworkflowactions').append( $('<option></option>').val(val['_key']).html(val['label']) );
                    $("#externalworkflowactions").prop("disabled", false)
                });

                actions_ready = true;

            }, "json");


            // Wait for externalworkflowaction to be ready
            $.when(actions_ready).done(function() {
                console.log("externalworkflowaction is ready");
                $('#modal-execute').prop('disabled', false);
            });

            $('#externalworkflowaction_command').prop('readonly',true);

            $('#externalworkflowactions').on('change', function() {
               console.log("change event fired on #externalworkflowaction");
               var incident_id = $("#workflow_incident_id > span").html();
               console.log("Incident ID: ", incident_id);

               value = $("#externalworkflowactions").val()
               label = $("#externalworkflowactions option:selected").text();
               console.log("#externalworkflowaction val:", value);
               console.log("#externalworkflowaction label:", label);
               if (label!="-"){
                 console.log("Getting workflowaction command...");
                 var externalworkflowaction_command_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/externalworkflow_actions?action=get_externalworkflowaction_command&incident_id='+incident_id+'&_key='+value);
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
        //var incident_id = $("#incident_id > span").html();
        var incident_ids = $("#incident_ids").val().split(':');
        var owner  = $("#owner").val();
        var urgency  = $("#urgency").val();
        var status  = $("#status").val();
        var comment  = $("#comment").val();

        // John Landers: Added comment == "" to make comments required
        // simcen: Changed back to not require comment
        if(incident_ids == "" || owner == "" || urgency == "" || status == "") {
            alert("Please choose a value for all required fields!");
            return false;
        }

        var update_entry = { 'incident_ids': incident_ids, 'comment': comment };
        // 'owner': owner, 'urgency': urgency, 'status': status, 'comment': comment
        if (owner != "(unchanged)") {
            update_entry.owner = owner;
        }
        if (urgency != "(unchanged)") {
            update_entry.urgency = urgency;
        }
        if (status != "(unchanged)") {
            update_entry.status = status;
        }

        console.log("entry", update_entry);
        //debugger;
        data = JSON.stringify(update_entry);
        var post_data = {
            contents    : data
        };

        var rest_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers');
        var post_data = {
            action        : 'update_incident',
            incident_data : data,
        };
        $.post( rest_url, post_data, function(data, status) {
            mvc.Components.get("recent_alerts").startSearch();
            mvc.Components.get("base_single_search").startSearch();
            $('#edit_panel').modal('hide');
            $('#edit_panel').remove();
            $("input:checkbox[name=bulk_edit_incidents]").prop('checked',false);
            $('#bulk_edit_container').hide();
        }, "text");


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

	      var log_event_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers');
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


    $("#panel2-fieldset").after($("<div />").attr('id', 'bulk_edit_container').addClass("bulk_edit_container").addClass('panel-element-row'));
    $(document).on("bulkedit_change", function(e, data) {
        //$('#bulk_edit_incidents').change(function(){
        //console.log('changed', $("#bulk_edit_incidents"));
        var incident_ids = $("input:checkbox[name=bulk_edit_incidents]:checked").map(function(){return $(this).val()}).get()
        console.log("incident_ids", incident_ids);

        if (incident_ids.length > 0) {
            var bulkedit_link = _.template('<div style="width: 50%; float: left"><button class="btn btn-primary" id="dobulkeditbtn">Bulk Edit</button> <span style="padding-left: 5px">Selected Incidents: <%-nr_incidents%></span></div><div style="width: 50%; float: left; text-align: right; padding-top: 5px"><span><a href="#" id="bulk_edit_clear">Clear Selection</a; padding-top: 5px></span></div>', {
                nr_incidents: incident_ids.length
            });
            $("#bulk_edit_container").html(bulkedit_link);
            $("#bulk_edit_container").show();
        } else {
            $("#bulk_edit_container").hide();
        }
    });

    $(document).on("click", "#dobulkeditbtn", function(event){
        var incident_ids = $("input:checkbox[name=bulk_edit_incidents]:checked").map(function(){return $(this).val()}).get()
        $(this).trigger("alert_manager_events", { action: "doedit", incident_ids: incident_ids });
    });

    $(document).on("click", "#bulk_edit_clear", function(event){
        $("input:checkbox[name=bulk_edit_incidents]").prop('checked',false);
        $(this).trigger("bulkedit_change");
    });
});
