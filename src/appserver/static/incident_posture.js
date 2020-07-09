require.config({
    paths: {
        "app": "../app"
    }
});

require([
    "splunkjs/mvc",
    "splunkjs/mvc/utils",
    "splunkjs/mvc/tokenutils",
    "underscore",
    "jquery",
    'models/SplunkDBase',
    'splunkjs/mvc/sharedmodels',
    "splunkjs/mvc/simplexml",
    'splunkjs/mvc/tableview',
    'splunkjs/mvc/chartview',
    'splunkjs/mvc/searchmanager',
    'splunk.util',
    'util/moment'
], function(
        mvc,
        utils,
        TokenUtils,
        _,
        $,
        SplunkDModel,
        sharedModels,
        DashboardController,
        TableView,
        ChartView,
        SearchManager,
        splunkUtil,
        moment
    ) {

    /****** Incident menu ********/
    $('body').append(`<div class="incident-menu-arrow" data-popdown-role="arrow"></div>
                <div id="incident-menu-container" class="incident-menu-container">
                <h3 class="incident-menu-header">Incident Actions</h3>
                <ul class="incident-menu">
                    <li><a href="#" class="incident-menu-item" data-event-action="doexternalworkflowaction">Execute External Workflow Action</a></li>
                    <li><a href="#" class="incident-menu-item" data-event-action="domanualnotification">Manual Notification</a></li>
                </ul>
                </div>`);

    $('#incident-menu-container .incident-menu-item').on("click", function (e) {
        //console.log("++++ menu action clicked +++++");
        //console.log(e.target)
        var action = $(this).data('event-action');
        if (action != "") {
            // console.log("trigger event now:" + action)
            $(this).trigger("alert_manager_events", { "action": action });
        }
        else {
            console.log(new Error("No incident action defined"));
        }
    })
    
    $(".incident-menu-container").on("mouseleave", function (e) {
        e.stopPropagation();
        //console.log("+++++ close incident menu +++++");
        $(".incident-menu-container").hide();
        $(".incident-menu-arrow").hide();
    });
    /************/

    // Tokens
    var submittedTokens = mvc.Components.getInstance('submitted', {create: true});
    var defaultTokens   = mvc.Components.getInstance('default', {create: true});

    // Container to support incident selection over multiple pages
    var selected_incidents = [];
    var all_incidents = [];

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

    // Create New Incidents
    $('<button />').addClass('btn').addClass('btn-primary').attr('id', 'create_new_incident_button').attr('data-toggle', 'modal').attr('data-target', '#create_new_incident_modal').text('New Incident').appendTo($('div.dashboard-header-editmenu > span'));

    $('#create_new_incident_button').click(function() {
        $('#create_new_incident_modal').remove();
        var create_new_incident_modal = '' +
        '<div class="modal fade" id="create_new_incident_modal" tabindex="-1" role="dialog" aria-labelledby="create_new_incident_modal" aria-hidden="true">' +
        '  <div class="modal-content">' +
        '    <div class="modal-header">' +
        '      <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>' +
        '      <h4 class="modal-title">Create New Incident</h4>' +
        '    </div>' +
        '    <div class="form form-horizontal form-complex" style="display: block;">' +
        '      <div class="control-group shared-controls-controlgroup">' +
        '        <label for="title" class="control-label">Title:</label>' +
        '        <div class="controls"><input type="text" name="title" id="title" class=""></input></div>' +
        '      </div>' +
        '      <div class="control-group shared-controls-controlgroup">' +
        '        <label for="category" class="control-label">Category:</label>' +
        '        <div class="controls"><input type="text" name="category" id="category" class=""></input></div>' +
        '      </div>' +
        '      <div class="control-group shared-controls-controlgroup">' +
        '        <label for="subcategory" class="control-label">Subcategory:</label>' +
        '        <div class="controls"><input type="text" name="subcategory" id="subcategory" class=""></input></div>' +
        '      </div>' +
        '      <div class="control-group shared-controls-controlgroup">' +
        '        <label for="tags" class="control-label">Tags:</label>' +
        '        <div class="controls"><input type="text" name="tags" id="tags" class=""></input></div>' +
        '      </div>' +
        '      <div class="control-group shared-controls-controlgroup">' +
        '        <label for="urgency" class="control-label">Urgency:</label>' +
        '        <div class="controls"><select name="urgency" id="urgency" disabled="disabled"></select></div>' +
        '      </div>' +
        '      <div class="control-group shared-controls-controlgroup">' +
        '        <label for="impact" class="control-label">Impact:</label>' +
        '        <div class="controls"><select name="impact" id="impact" disabled="disabled"></select></div>' +
        '      </div>' +
        '      <div class="control-group shared-controls-controlgroup">' +
        '         <label for="owner" class="control-label">Owner:</label>' +
        '         <div class="controls"><select name="owner" id="owner" disabled="disabled"></select></div>' +
        '      </div>' +
        '          <div class="control-group shared-controls-controlgroup">' +
        '            <label for="incident_group" class="control-label">Incident Group:</label>' +
        '            <div class="controls"><input type="hidden" name="incident_group" id="incident_group" disabled="disabled"></input></div>' +
        '          </div>' +
        '      <div class="control-group shared-controls-controlgroup">' +
        '        <label for="fields" class="control-label">Fields:</label>' +
        '        <div class="controls"><textarea type="text" name="fields" id="fields" class=""></textarea></div>' +
        '      </div>' +
        '      <p class="control-heading">Drilldown Settings (Optional):</p>'+
        '      <div class="control-group shared-controls-controlgroup">' +
        '        <label for="event_search" class="control-label">Incident Search:</label>' +
        '        <div class="controls"><textarea type="text" name="event_search" id="event_search" class=""></textarea></div>' +
        '      </div>' +
        '      <div class="control-group shared-controls-controlgroup">' +
        '        <label for="earliest_time" class="control-label">Incident Earliest Time:</label>' +
        '        <div class="controls"><input type="text" name="earliest_time" id="earliest_time" class=""></input></div>' +
        '      </div>' +
        '      <div class="control-group shared-controls-controlgroup">' +
        '        <label for="latest_time" class="control-label">Incident Latest Time:</label>' +
        '        <div class="controls"><input type="text" name="latest_time" id="latest_time" class=""></input></div>' +
        '      </div>' +
        '      <div class="modal-footer">' +
        '        <button type="button" class="btn cancel modal-btn-cancel pull-left" data-dismiss="modal">Cancel</button>' +
        '        <button type="button" class="btn btn-primary" id="modal-create-new-incident" disabled>Create</button>' +
        '      </div>' +
        '    </div>' +
        '</div>';

        $('body').prepend(create_new_incident_modal);
        
        $("#owner").select2();
        var owner_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers?action=get_users');
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
        });

        var all_impacts = [ "low" ,"medium", "high" ]

        $.each(all_impacts, function(key, val) {
            if (val == impact) {
                $('#impact').append( $('<option></option>').attr("selected", "selected").val(val).html(val) )
            } else {
                $('#impact').append( $('<option></option>').val(val).html(val) )
            }
            $("#impact").prop("disabled", false);
        });

        // Get list of incident_groups and prepare dropdown
        var incident_groups_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers?action=get_incident_groups');
        var incident_groups_xhr = $.get(incident_groups_url, function(data) {

            var incident_groups = [];
            incident_groups.push( {  'id': 'none', 'text': '(ungrouped)' });

            _.each(data, function(el) {
                incident_groups.push( {  'id': el._key, 'text': el.group });
            });

            $('#incident_group').select2({
                data: incident_groups,
                placeholder: 'Select existing or type to add group',
                allowClear: true,
                createSearchChoice: function(term) {
                    return {
                        id: -1,
                        text: term + ' (new)'
                    }
                }
            });

            $("#incident_group").prop("disabled", false);
        }, "json");


        $("label:contains('Fields:')").after($('<sup />').append($('<a />').text('?').addClass("btnModalInfo").addClass("btnModalInfo").attr('id', 'fields_tooltip').attr("href", "#").attr("title",  "key1=\"value1\"\nkey2=\"value2\"\nkeyN=\"valueN\"").attr("data-toggle", "modal").attr("data-target", "#desc3")));
        $("label:contains('Fields:')").attr("style","float:left");
        $('#fields_tooltip').tooltip();
        $("label:contains('Tags:')").after($('<sup />').append($('<a />').text('?').addClass("btnModalInfo").addClass("btnModalInfo").attr('id', 'tags_tooltip').attr("href", "#").attr("title",  "tag1 tag2 tag3 tagN").attr("data-toggle", "modal").attr("data-target", "#desc3")));
        $("label:contains('Tags:')").attr("style","float:left");
        $('#tags_tooltip').tooltip();
        $("label:contains('Incident Earliest Time:')").after($('<sup />').append($('<a />').text('?').addClass("btnModalInfo").addClass("btnModalInfo").attr('id', 'earliest_time_tooltip').attr("href", "#").attr("title",  "yyyy-mm-ddTHH:MM:SS.sss(+)hh:mm").attr("data-toggle", "modal").attr("data-target", "#desc3")));
        $("label:contains('Incident Earliest Time:')").attr("style","float:left");
        $('#earliest_time_tooltip').tooltip();
        $("label:contains('Incident Latest Time:')").after($('<sup />').append($('<a />').text('?').addClass("btnModalInfo").addClass("btnModalInfo").attr('id', 'latest_time_tooltip').attr("href", "#").attr("title",  "yyyy-mm-ddTHH:MM:SS.sss(+-)hh:mm").attr("data-toggle", "modal").attr("data-target", "#desc3")));
        $("label:contains('Incident Latest Time:')").attr("style","float:left");
        $('#latest_time_tooltip').tooltip();

        // Wait for owner and status to be ready
        $.when(owner_xhr, incident_groups_xhr).done(function() {
            console.log("owner is ready");
            $('#modal-create-new-incident').prop('disabled', false);
          });
    });
        
    // Add Filter description
    $("label:contains('Filter:')").after($('<sup />').append($('<a />').text('?').addClass("btnModalInfo").addClass("btnModalInfo").attr('id', 'filter_tooltip').attr("href", "#").attr("title",  "Filter syntax e.g.: app=search, count>10, host=myhost* AND count<10").attr("data-toggle", "modal").attr("data-target", "#desc3")));
    $("label:contains('Filter:')").attr("style","float:left");
	$('#filter_tooltip').tooltip();

    var IconRenderer = TableView.BaseCellRenderer.extend({
        canRender: function(cell) {
            // Only use the cell renderer for the specific field
            return (cell.field === "dosearch" || cell.field === "dobulkedit" || cell.field === "doedit" || cell.field === "owner" || cell.field === "doquickassign" || cell.field === "doaction" );
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
                $td.addClass('bulk_edit_incidents');
                if (_.contains(selected_incidents, cell.value)) {
                    $td.html('<input type="checkbox" class="bulk_edit_incidents" id="bulk_edit_incidents" name="bulk_edit_incidents" value="'+ cell.value +'" checked="checked"></input>')
                } else {
                    $td.html('<input type="checkbox" class="bulk_edit_incidents" id="bulk_edit_incidents" name="bulk_edit_incidents" value="'+ cell.value +'"></input>')
                }
                $td.on("click", function(e) {
                    e.stopPropagation();
                    $td.trigger("alert_manager_events", {"action": cell.field });
                });

            } else if(cell.field=="doaction") {
                var icon = 'lightning';
                var tooltip = "Incident actions";

                var rendercontent = '<a class="btn-pill" data-toggle="tooltip" data-placement="top" title="<%-tooltip%>"><i class="icon-<%-icon%>"></i><span class="hide-text">Inspect</span></a>';
                //var rendercontent='<div style="float:left; max-height:22px; margin:0px;"><i class="icon-<%-icon%>" >&nbsp;</i></div>';

                $td.addClass('table_inline_icon').html(_.template(rendercontent, {
                    icon: icon,
                    tooltip: tooltip
                }));
                //$td.children('[data-toggle="tooltip"]').tooltip();
            
                // console.log("+++++ render Incident actions +++++" );
                
                $td.children('[class="btn-pill"]').on("mouseover", function (e) {
                    e.stopPropagation();
                    // console.log("+++++ open incident action menu +++++");
                    
                    var incidentId = $(this).parent().parent().find("td.incident_id").get(0).textContent;

                    //console.log(incidentId);

                    var listItems = $(".incident-menu li");
                    listItems.each(function (idx, li) {
                        var incident = $(li);
                        //console.log(incident)
                        incident.children('a').attr('data-incidentId', incidentId);

                    });

                    $(".incident-menu-container").offset({ left: $td.children('[class="btn-pill"]').offset().left - Math.abs(($(".incident-menu-container").width() / 2) - 16), top: $td.children('[class="btn-pill"]').offset().top + $td.children('[class="btn-pill"]').height() }); 
                    $(".incident-menu-arrow").offset({ left: $(".incident-menu-container").offset().left + Math.abs(($(".incident-menu-container").width() / 2) - 16), top: ($td.children('[class="btn-pill"]').offset().top - 8) + $td.children('[class="btn-pill"]').height() } ); 
                    $(".incident-menu-container").show();
                    $(".incident-menu-arrow").show();

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
                 || cell.field==="earliest_alert_time" || cell.field==="first_seen" || cell.field==="group" || cell.field==="group_id");

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

            drilldownSearchManager = new SearchManager({
                id: 'incident_drilldown_exp_manager',
                preview: false
            });

            historySearchManager = new SearchManager({
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
                contEl.append($('<div />').css('float', 'left').text('group=').append($('<span />').addClass('group_exp').addClass('exp-group').addClass(group).text(group.value)));
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

            

            history_search_string = '`incident_history('+ incident_id.value +')`'

            console.log("earliest_alert_time %s...", earliest_alert_time.value)

            historySearchManager.set({
                search: history_search_string,
                earliest_time: earliest_alert_time.value,
                latest_time: 'now',
                autostart: false

            });

            historySearchManager.startSearch();

            historyTableView = new TableView({
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


            //
            // Additional Drilldowns starts here
            //

            $('<br />').appendTo($container);
            $("<h3>").text('Drilldowns').appendTo($container);

            var has_drilldown_actions = false

            var has_drilldown_settings_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/drilldown_actions?action=has_drilldown_actions&alert='+alert.value);
            var has_drilldown_settings_xhr = $.get( has_drilldown_settings_url, function(data) {

            console.log("data", data);

            if (data=="True") {
                console.log("has_drilldown_actions: True")
                has_drilldown_actions = true

            } else {
                console.log("has_drilldown_actions: False")
                has_drilldown_actions = false
            }
            
            });
            
            drilldown_search_string = '| loaddrilldowns incident_id='+incident_id.value+' | rename label AS Target'

            drilldownSearchManager.set({
                search: drilldown_search_string,
                earliest_time: '-1m',
                latest_time: 'now',
                autostart: false
            });

            drilldownTableView = new TableView({
                id: 'incident_drilldown_exp_'+incident_id.value+'_'+Date.now(),
                managerid: 'incident_drilldown_exp_manager',
                'drilldown': 'row',
                'wrap': true,
                'displayRowNumbers': true,
                'pageSize': '10',
                'fields': 'Target',
                drilldownRedirect: false,
                //'el': $("#incident_drilldown_exp")
            });

               drilldownTableView.on("click", function(e) {
                // Bypass the default behavior
                e.preventDefault()

                // Displays a data object in the console
                row = e.data

                window.open(row["row.url"])
            });

            // Wait for has_incident_settings_xhr ready
            $.when(has_drilldown_settings_xhr).done(function() {
                console.log("has_drilldown_settings_xhr ready");
                console.log("has_drilldown_actions: ", has_drilldown_actions)

                if (has_drilldown_actions === true) {

                    console.log("has_drilldown_actions value: true");

                    drilldownSearchManager.startSearch()
                    $container.append(drilldownTableView.render().el)
                }    

                else {
                    $("<div/>").text('No Drilldown Actions configured').appendTo($container);   
                }

                // Postpone rendering of History to after Drilldowns
                $('<br />').appendTo($container);
                $("<h3>").text('History').appendTo($container);
                $("<div/>").text('Loading...').attr('id', 'loading-bar-history').appendTo($container);

                $container.append(historyTableView.render().el);

            });

            
        },
        render: function($container, rowData) {

            this._detailsSearchManager.on("search:done", function(state, job){
                $("#loading-bar-details").hide();
            });

            drilldownSearchManager.on("search:done", function(state, job){
                $("#loading-bar-details").hide();
            });

            historySearchManager.on("search:done", function(state, job){
                $("#loading-bar-history").hide();
            });

        }
    });

    $(document).on("alert_manager_events", "td, a", function(e, data) {

        // Displays a data object in the console

        console.log("alert_manager_events handler fired", data);

        if (data.action=="dobulkedit") {
            var incident_id =   $(this).parent().find("td.incident_id").get(0).textContent;
            //$(this).parent().find("td.bulk_edit_incidents").children("input").val(incident_id)
            console.log("incident_id", $(this).parent().find("td.bulk_edit_incidents").children("input").val());
            if ($(this).parent().find("td.bulk_edit_incidents").children("input").is(':checked')) {
                // Add incident_id to selected_incidents
                selected_incidents.push(incident_id);
            } else {
                selected_incidents = _.without(selected_incidents, incident_id);
            }
            console.log("selected_incidents", selected_incidents);
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
                var nr_incidents = data.incident_ids.length;
                var incident_id = data.incident_ids.join(', <br />');
                var incident_ids_string = data.incident_ids.join(':');
                var owner = '(unchanged)';
                var urgency = '(unchanged)';
                var status = '(unchanged)';
                var group_id = 'unchanged';
                var modal_title = "Incidents";
                var modal_id = "incident_ids";
            } else {
            // Incident settings
                var bulk = false;
                var nr_incidents = 1;
                var incident_id =   $(this).parent().find("td.incident_id").get(0).textContent;
                var incident_ids_string = incident_id;
                var owner =    $(this).parent().find("td.owner").get(0).textContent;
                var urgency = $(this).parent().find("td.urgency").get(0).textContent;
                var status =   $(this).parent().find("td.status").get(0).textContent;
                var group_id =   $(this).parent().find("td.group_id").get(0).textContent;
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
'        <div id="info_message" class="hide alert alert-info" style="display: block;">' +
'          <i class="icon-alert"></i><span id="info_text">You are editing '+ nr_incidents +' incident</span>' +
'        </div>' +
'        <input type="hidden" id="incident_ids" value="'+incident_ids_string+'" />' +
'        <div class="form form-horizontal form-complex" style="display: block;" autocomplete="off">' +
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
'            <label for="incident_group" class="control-label">Incident Group:</label>' +
'            <div class="controls"><input type="hidden"" name="incident_group" id="incident_group" disabled="disabled"></select></div>' +
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

            // Get list of incident_groups and prepare dropdown
            var incident_groups_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers?action=get_incident_groups');
            var incident_groups_xhr = $.get(incident_groups_url, function(data) {

                var incident_groups = [];

                if (bulk) {
                    incident_groups.push( {  'id': 'unchanged', 'text': '(unchanged)' });
                }
                incident_groups.push( {  'id': 'none', 'text': '(ungrouped)' });

                _.each(data, function(el) {
                    incident_groups.push( {  'id': el._key, 'text': el.group });
                });

                $('#incident_group').select2({
                    data: incident_groups,
                    placeholder: 'Select existing or type to add group',
                    allowClear: true,
                    createSearchChoice: function(term) {
                        return {
                            id: -1,
                            text: term + ' (new)'
                        }
                    }
                });

                if (bulk) {
                    $('#incident_group').val('unchanged').trigger("change");
                } else {
                    if (group_id != "unknown") {
                        console.log("default select group:", group_id);
                        $('#incident_group').val(group_id).trigger("change");
                    }
                }

                $("#incident_group").prop("disabled", false);
            }, "json");

            // Wait for owner and status to be ready
            $.when(status_xhr, owner_xhr, incident_groups_xhr).done(function() {
              console.log("status and owner are ready");
              $('#modal-save').prop('disabled', false);
            });

            // Change status when new owner is selected
            $('#owner').on("change", function() {
                console.log("change event fired on #owner");
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

            var incident_id = $(this).attr("data-incidentId");
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
'            <label for="message-text" class="control-label">Comment:</label>' +
'            <div class="controls"><textarea type="text" name="externalworkflowaction_comment" id="externalworkflowaction_comment" class=""></textarea></div>' +
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
               comment = $("#externalworkflowaction_comment").val();

               console.log("#externalworkflowaction val:", value);
               console.log("#externalworkflowaction label:", label);
               if (label!="-"){
                 console.log("Getting workflowaction command...");
                 var externalworkflowaction_command_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/externalworkflow_actions?action=get_externalworkflowaction_command&incident_id='+incident_id+'&_key='+value+'&comment='+comment);
                 $.get( externalworkflowaction_command_url, function(data, status) {
                   console.log("Retrieved command:", data);
                   $('#externalworkflowaction_command').val(data);
                 }, "text");
               }
            });

            $('#externalworkflowaction_comment').on('change keyup paste input', function() {
                console.log("change event fired on #externalworkflowaction_comment");

                comment = $("#externalworkflowaction_comment").val();

                console.log("#externalworkflowaction_comment:", comment);
                if (comment != "" && label!="-") {
                    console.log("Getting workflowaction command...");
                    var externalworkflowaction_command_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/externalworkflow_actions?action=get_externalworkflowaction_command&incident_id='+incident_id+'&_key='+value+'&comment='+comment);
                    $.get( externalworkflowaction_command_url, function(data, status) {
                      console.log("Retrieved command:", data);
                      $('#externalworkflowaction_command').val(data);
                    }, "text");
                  }

             });

            // Finally show modal
            $('#externalworkflowaction_panel').modal('show');
        }
        else if (data.action=="domanualnotification"){
            console.log("domanualnotification catched");

            var incident_id = $(this).attr("data-incidentId");

            var events_ready = false;

            var manualnotification_panel='' +
'<div class="modal fade modal-wide shared-alertcontrols-dialogs-manualnotificationdialog in" id="manualnotification_panel">' +
'    <div class="modal-content">' +
'      <div class="modal-header">' +
'        <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>' +
'        <h4 class="modal-title" id="exampleModalLabel">Manual Notification</h4>' +
'      </div>' +
'      <div class="modal-body modal-body-scrolling">' +
'        <div class="form form-horizontal form-complex" style="display: block;">' +
'          <div class="control-group shared-controls-controlgroup">' +
'            <label for="incident_id" class="control-label">Incident:</label>' +
'            <div class="controls controls-block"><div class="control shared-controls-labelcontrol" id="notify_incident_id"><span class="input-label-incident_id">' + incident_id + '</span></div></div>' +
'          </div>' +
'          <div class="control-group shared-controls-controlgroup">' +
'            <label for="message-text" class="control-label">Select Event:</label>' +
'            <div class="controls"><select name="manualnotification_event" id="manualnotification_event" disabled="disabled"></select></div>' +
'          </div>' +
'          <div class="control-group shared-controls-controlgroup">' +
'            <label for="message-text" class="control-label">Overwrite Mail Recipients:</label>' +
'            <div class="controls"><input type="checkbox" name="manualnotification_recipients_overwrite" id="manualnotification_recipients_overwrite" class=""></input></div>' +
'          </div>' +
'          <div class="control-group shared-controls-controlgroup">' +
'            <label for="message-text" class="control-label">Mail Recipients:</label>' +
'            <div class="controls"><textarea type="text" rows="3" name="manualnotification_recipients" id="manualnotification_recipients" class=""></textarea></div>' +
'          </div>' +
'          <div class="control-group shared-controls-controlgroup">' +
'            <label for="message-text" class="control-label">Optional Message:</label>' +
'            <div class="controls"><textarea type="text" name="manualnotification_message" id="manualnotification_message" class=""></textarea></div>' +
'          </div>' +
'        </div>' +
'      </div>' +
'      <div class="modal-footer">' +
'        <button type="button" class="btn cancel modal-btn-cancel pull-left" data-dismiss="modal">Cancel</button>' +
'        <button type="button" class="btn btn-primary" id="modal-notify" disabled>Notify</button>' +
'      </div>' +
'    </div>' +
'</div>';

            $('body').prepend(manualnotification_panel);
            $('#manualnotification_event').append( $('<option></option>').val("-").html("-") );
            $('#manualnotification_recipients').prop('readonly',true);
            $("#manualnotification_event").select2();

            var manualnotification_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers');
            var post_data = {
                action        : 'get_notification_scheme_events',
                incident_id : incident_id,
            };

            var manualnotification_xhr = $.post( manualnotification_url, post_data, function(data, status) {
                console.log("Events data", data);
                _.each(data, function(val, text) {
                    $('#manualnotification_event').append( $('<option></option>').val(val['event']).html(val['event']) );
                    $("#manualnotification_event").prop("disabled", false);
                });

                events_ready = true;

            }, "json");

            // Wait for manualnotification to be ready
            $.when(events_ready).done(function() {
                console.log("manualnotification is ready");
                $('#modal-notify').prop('disabled', false);
            });

            $('#manualnotification_event').on('change', function() {
                console.log("change event fired on #manualnotification_event");
               
                var recipients ="";
                var recipients_list ="";

                var manualnotification_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers');
                
                var post_data = {
                    action        : 'get_notification_scheme_events',
                    incident_id : incident_id,
                };

                var manualnotification_xhr = $.post( manualnotification_url, post_data, function(data, status) {
               
                    _.each(data, function(val, text) {
                        if (val['event'] == $("#manualnotification_event").val() ) {
                            recipients_list = val['recipients']
                        }
                    });
                    
                    $(manualnotification_recipients).val(recipients_list)

                }, "json");  

            });

            $('#manualnotification_recipients_overwrite').on('change', function() { 
                if ($("#manualnotification_recipients_overwrite").prop("checked") == true ) {
                    $('#manualnotification_recipients').prop('readonly',false);
                }
                else {
                    current_selection = $("#manualnotification_event").val();
                    $("#manualnotification_event").val(current_selection).trigger('change')
                    $('#manualnotification_recipients').prop('readonly',true);
                }

            });

            // Finally show modal
            $('#manualnotification_panel').modal('show');
        }
        else if (data.action == "doaction") {
            console.log("+++++ open Action menu +++++")
        }

    });

    $(document).on("click", "#modal-save", function(event){
        $('#modal-save').prop('disabled', true);
        // save data here
        //var incident_id = $("#incident_id > span").html();
        var incident_ids = $("#incident_ids").val().split(':');
        var owner  = $("#owner").val();
        var urgency  = $("#urgency").val();
        var status  = $("#status").val();
        var group  = $("#incident_group").select2("data");
        var comment  = $("#comment").val();

        // John Landers: Added comment == "" to make comments required
        // simcen: Changed back to not require comment
        if(incident_ids == "" || owner == "" || urgency == "" || status == "") {
            alert("Please choose a value for all required fields!");
            return false;
        }

        var update_entry = { 'incident_ids': incident_ids, 'comment': comment };
        // 'owner': owner, 'urgency': urgency, 'status': status, 'group_id': group_id, comment': comment
        if (owner != "(unchanged)") {
            update_entry.owner = owner;
        }
        if (urgency != "(unchanged)") {
            update_entry.urgency = urgency;
        }
        if (status != "(unchanged)") {
            update_entry.status = status;
        }
        if (group != null && group.id != null && group.id != "(unchanged)" && group.id != "unchanged" && group.id != "none" && group.id != "") {
            if(group.id == -1) {
                var group_name = group.text.replace(' (new)', '');

                var create_incident_group_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers');
                var post_data = {
                    action     : 'create_incident_group',
                    group      : group_name
                };

                var create_incident_group_xhr = $.post( create_incident_group_url, post_data, function(data, status) {
                    console.log("create new group data", data);
                    update_entry.group_id = data.group_id;
                }, "json");

            } else {
                var create_incident_group_xhr = true;
                update_entry.group_id = group.id;
            }
        } else {
            if (group == null || group.id == "" || group.id == "none") {
                update_entry.group_id = "";
            }
            var create_incident_group_xhr = true;
        }

        $.when(create_incident_group_xhr).done(function() {
            console.log("entry", update_entry);

            var update_incident_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers');
            var data = JSON.stringify(update_entry);
            var post_data = {
                action        : 'update_incident',
                incident_data : data,
            };

            $.post( update_incident_url, post_data, function(data, status) {
                mvc.Components.get("recent_alerts").startSearch();
                mvc.Components.get("base_single_search").startSearch();
                $('#edit_panel').modal('hide');
                $('#edit_panel').remove();
                $("input:checkbox[name=bulk_edit_incidents]").prop('checked',false);
                selected_incidents = [];
            }, "text");
        });



    });

    $(document).on("click", "#modal-execute", function(event){
        var incident_id = $("#workflow_incident_id > span").html();
        
        var command  = $("#externalworkflowaction_command").val();
        var comment  = $("#externalworkflowaction_comment").val();

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

        
        manager.on('search:done', function(properties) {

            console.log("External Workflowaction Done:", properties);
                
            // Create log entry for command

            var log_event_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers');
            var post_data = {
                action     : 'write_log_entry',
                log_action : 'comment',
                origin      : 'externalworkflowaction',
                incident_id: incident_id,
                comment    : label + ' workflowaction executed: ' + command

            };
            $.post( log_event_url, post_data, function(data, status) { return "Executed"; }, "text");

            // Create log entry for comment
            if (comment != "") {
                var log_event_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers');
                var post_data = {
                    action     : 'write_log_entry',
                    log_action : 'comment',
                    origin      : 'externalworkflowaction',
                    incident_id: incident_id,
                    comment    : label + ' workflowaction comment: ' + comment

                };
                $.post( log_event_url, post_data, function(data, status) { return "Executed"; }, "text");
            }

        }); 

        manager.on('search:fail', function(properties) {
            alert("External Workflowaction Failure: See log files details")
            console.log("External Workflowaction Failed:", properties);
        }); 

        manager.on('search:error', function(properties) {
            alert("External Workflowaction Error: See log files for details")
            console.log("External Workflowaction Error:", properties);
        }); 

        manager.on('search:start', function(properties) {
            console.log("External Workflowaction Start:", properties);
        }); 

        manager.on('search:progress', function(properties) {
            console.log("External Workflowaction Progress:", properties);
        }); 

        manager.startSearch();
                          
        manager = null;

        $('#modal-execute').prop('disabled', true);

        setTimeout(function(){
            $('#externalworkflowaction_panel').modal('hide');
            $('#externalworkflowaction_panel').remove();
            mvc.Components.get("recent_alerts").startSearch();
        }, 2000);

    });

    $(document).on("click", "#modal-notify", function(event){

        var incident_id = $("#notify_incident_id > span").html();
        var event  = $("#manualnotification_event").val();
        var recipients  = $("#manualnotification_recipients").val();
        var message  = $("#manualnotification_message").val();
        var recipients_overwrite = $("#manualnotification_recipients_overwrite").prop("checked");

        var manual_notification_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers');
        var post_data = {
            action     : 'send_manual_notification',
            event : event,
            incident_id: incident_id,
            notification_message: message,
            recipients: recipients,
            recipients_overwrite: recipients_overwrite
        };

        $.post( manual_notification_url, post_data, function(data, status) { 
            $('#manualnotification_panel').modal('hide');
            $('#manualnotification_panel').remove();
            return "Notified"; }, "text");

        // Create log entry for notification

        var log_event_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers');
        var post_data = {
            action     : 'write_log_entry',
            log_action : 'comment',
            origin      : 'manualnotification',
            incident_id: incident_id,
            comment    : ' Manual notification executed: ' + event + ' recipients="' + recipients +'" notification_message="' + message + '"'
        };

        $.post( log_event_url, post_data, function(data, status) { return "Executed"; }, "text");

    });

    $(document).on("click", "#modal-create-new-incident", function(event){

        var title  = $("#title").val();
        var category  = $("#category").val();
        var subcategory  = $("#subcategory").val();
        var tags  = $("#tags").val();
        var urgency  = $("#urgency").val();
        var impact  = $("#impact").val();
        var owner  = $("#owner").val();
        var group  = $("#incident_group").select2("data");
        var event_search = $("#event_search").val();
        var earliest_time = $("#earliest_time").val();
        var latest_time = $("#latest_time").val();
        var fields  = $("#fields").val();

        if(title == "") {
            alert("Please choose a value for all required fields!");
            return false;
        }

	    var log_event_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers');
        var new_incident_entry = {
            action     : 'create_new_incident',
            title : title,
            category: category,
            subcategory: subcategory,
            tags: tags,
            urgency: urgency,
            impact: impact,
            owner: owner,
            event_search: event_search,
            earliest_time: earliest_time,
            latest_time: latest_time,
            fields: fields,
            origin     : 'create_new_incident',

        };

        if (group != null && group.id != null && group.id != "(unchanged)" && group.id != "unchanged" && group.id != "none" && group.id != "") {
            if(group.id == -1) {
                var group_name = group.text.replace(' (new)', '');

                var create_incident_group_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers');
                var post_data = {
                    action     : 'create_incident_group',
                    group      : group_name
                };

                var create_incident_group_xhr = $.post( create_incident_group_url, post_data, function(data, status) {
                    console.log("create new group data", data);
                    new_incident_entry.group_id = data.group_id;
                }, "json");

            } else {
                var create_incident_group_xhr = true;
                new_incident_entry.group_id = group.id;
            }
        } else {
            if (group == null || group.id == "" || group.id == "none") {
                new_incident_entry.group_id = "";
            }
            var create_incident_group_xhr = true;
        }

        $.when(create_incident_group_xhr).done(function() {
            $.post( log_event_url, new_incident_entry, function(data, status) {
                $('#modal-create-new-incident').prop('disabled', true);
                setTimeout(function(){
                    $('#create_new_incident_modal').modal('hide');
                    $('#create_new_incident_modal').remove();
                    mvc.Components.get("recent_alerts").startSearch();
                }, 2000);
                return "Executed";
            }, "text").fail(function(data, status) {
                alert("Please check your inputs!");
                return false;
             });
        });
    });

    $(document).on("click", "#bulk_edit_selected", function(e){
        e.preventDefault();
        //var incident_ids = $("input:checkbox[name=bulk_edit_incidents]:checked").map(function(){return $(this).val()}).get()
        var incident_ids = selected_incidents;
        if (incident_ids.length > 0) {
            console.log("launching alert_manager_events handler with data", incident_ids);
            $(this).trigger("alert_manager_events", { action: "doedit", incident_ids: incident_ids });
        } else {
            alert("You must select at least one incident.");
        }
    });

    $(document).on("click", "#bulk_edit_all", function(e){
        e.preventDefault();
        var incident_ids = all_incidents;
        if (incident_ids.length > 0) {
            console.log("launching alert_manager_events handler with data", incident_ids);
            $(this).trigger("alert_manager_events", { action: "doedit", incident_ids: incident_ids });
        } else {
            alert("You must select at least one incident.");
        }
    });

    $(document).on("click", "#bulk_edit_clear", function(e){
        e.preventDefault();
        $("input:checkbox[name=bulk_edit_incidents]").prop('checked',false);
        selected_incidents = [];
    });

    $(document).on("click", "#bulk_edit_select_all", function(e){
        e.preventDefault();
        $("input:checkbox[name=bulk_edit_incidents]").prop('checked',true);
        selected_incidents = $("input:checkbox[name=bulk_edit_incidents]:checked").map(function(){return $(this).val()}).get();
    });


    incidentsOverViewTable = mvc.Components.get('incident_overview');
    incidentsOverViewTable.getVisualization(function(tableView) {
        // Add custom cell renderer
        tableView.table.addCellRenderer(new HiddenCellRenderer());
        tableView.table.addCellRenderer(new IconRenderer());
        tableView.addRowExpansionRenderer(new IncidentDetailsExpansionRenderer());

        tableView.table.render();

    });

    search_recent_alerts.on("search:start", function() {
        $("#bulk_edit_container").remove();
    });

    var search_recent_alerts_results = search_recent_alerts.data("results", {count: 0, output_mode: 'json_rows'});
    search_recent_alerts_results.on("data", function() {
        // Add layer with bulk edit links
        //console.log("search_recent_alerts", search_recent_alerts.data("results"),search_recent_alerts_results.data());
     	if(search_recent_alerts_results.data() !== undefined){
		all_incidents = _.map(search_recent_alerts_results.data().rows, function(e){ return e[0]; });
        	//console.log("all recent incidents for: ",search_recent_alerts.data("results").cid,all_incidents)
		$("#bulk_edit_container").remove();
        	$("#panel2-fieldset").after($("<div />").attr('id', 'bulk_edit_container').addClass("bulk_edit_container").addClass('panel-element-row'));
        	var links = _.template('<a href="#" id="bulk_edit_select_all">Select All</a> | <a href="#" id="bulk_edit_selected">Edit Selected</a> | <a href="#" id="bulk_edit_all">Edit All <%-nr_incidents%> Matching Incidents</a> | <a href="#" id="bulk_edit_clear">Reset Selection</a>', { nr_incidents: all_incidents.length });
       		$("#bulk_edit_container").html(links);
        	$("#bulk_edit_container").show();
	}else{
		console.log("no recent alerts found for:",search_recent_alerts.data("results").cid)
	}
    });

    var rendered = false;
    incidentsOverViewTable.on("rendered", function(obj) {
        //console.log("events", $._data($('#incident_overview')[0], "events"));
        if(!rendered) {
            rendered = true;

            if (settings.entry.content.get('incident_list_length') != undefined) {
                obj.settings.set({ pageSize: settings.entry.content.get('incident_list_length') });
            }

        }
    });

});
