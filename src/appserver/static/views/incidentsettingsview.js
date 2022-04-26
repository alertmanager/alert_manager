require.config({
    paths: {
        "app": "../app"
    },
    shim: {
        "app/alert_manager/contrib/handsontable-0.12.2/handsontable.full.min": {
            deps: ['css!../handsontable-0.12.2/handsontable.full.min.css'],
            exports: "Handsontable"
        },
    }
});


define(function(require, exports, module) {

    var _ = require('underscore');
    var $ = require('jquery');
    var mvc = require('splunkjs/mvc');
    var SimpleSplunkView = require('splunkjs/mvc/simplesplunkview');
    var Handsontable = require('app/alert_manager/contrib/handsontable-0.12.2/handsontable.full.min');
    var splunkUtil = require('splunk.util');

    //require("css!../lib/handsontable.full.css");

    var IncidentSettingsView = SimpleSplunkView.extend({
        className: "incidentsettingsview",

        del_key_container: '',

        // Set options for the visualization
        options: {
            data: "preview",  // The data results model from a search
        },
        output_mode: 'json',


        createView: function() {
            console.log("createView");
            return { container: this.$el, } ;
        },

        updateView: function(viz, data) {

            console.log("updateView", data);

            this.$el.empty();

            $('<div />').attr('id', 'handson_container').appendTo(this.$el);

            var notification_schemes = new Array();
            var url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/helpers?action=get_notification_schemes');
            $.get( url,function(data) {
                _.each(data, function(el) {
                    notification_schemes.push(el);
                });
            }, "json");
            console.debug("notification_schemes", notification_schemes);


            headers = [ { col: "_key", tooltip: false },
                        { col: "alert", tooltip: false },
                        { col: "category", tooltip: false },
                        { col: "subcategory", tooltip: false },
                        { col: "tags", tooltip: "Space separated list of tags" },
                        { col: "display_fields", tooltip: "Space separated list of fields to display in incident details."},
                        { col: "drilldowns", tooltip: "Space seperated list of drilldown configurations to display in incident details."},
                        { col: "notification_scheme", tooltip: "Select notification scheme to be used for this alert"} ];
            $("#handson_container").handsontable({
                data: data,
                //colHeaders: ["_key", "alert", "category", "subcategory", "tags", "urgency", "run_alert_script", "alert_script", "auto_assign", "auto_assign_owner", "auto_ttl_resolve", "auto_previous_resolve"],
                columns: [
                    {
                        data: "_key",
                        readOnly: true
                    },
                    {
                        data: "alert",
                        readOnly: true
                    },
                    {
                        data: "category",
                    },
                    {
                        data: "subcategory",
                    },
                    {
                        data: "tags",
                    },
                    {
                        data: "display_fields",
                    },
                    {
                        data: "drilldowns",
                    },
                    {
                        data: "notification_scheme",
                        type: "dropdown",
                        source: notification_schemes,
                    }
                ],
                colHeaders: true,
                colHeaders: function (col) {
                    if (headers[col]["tooltip"] != false) {
                        colval = headers[col]["col"] + '<a href="#" data-container="body" class="tooltip-link" data-toggle="tooltip" title="'+ headers[col]["tooltip"] +'">?</a>';
                    }
                    else {
                        colval = headers[col]["col"];
                    }
                    return colval;
                },
                stretchH: 'all',
                contextMenu: ['row_above', 'row_below', 'remove_row', 'undo', 'redo'],
                startRows: 1,
                startCols: 1,
                minSpareRows: 1,
                minSpareCols: 0,
                afterRender: function() {
                    $(function () {
                        $('[data-toggle="tooltip"]').tooltip()
                    })
                },
                beforeRemoveRow: function(row) {
                    var data = $("#handson_container").data('handsontable').getData();
                    if(confirm('Are you sure to remove settings for alert "' + data[row]['alert'] + '"?')) {
                        this.del_key_container = data[row]['_key'];
                        return true;
                    } else {
                        return false;
                    }
                },
                afterRemoveRow: function(row) {
                    console.debug("afterRemoveRow");
                    //var data = $("#handson_container").data('handsontable').getData();
                    console.debug("row", row);
                    //console.debug("data", data);
                    console.debug("key", this.del_key_container);

                    var rest_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/incident_settings');
                    var post_data = {
                        action : 'delete_incident_setting',
                        key    : this.del_key_container
                    };
          	        $.post( rest_url, post_data, function(data, status) {
                        this.del_key_container = '';
                        // Reload the table
                        mvc.Components.get("incident_settings_search").startSearch()
                    }, "text");


                }
            });
            //console.debug("id", id);


          //debugger;
          //id

        },

        // Override this method to format the data for the view
        formatData: function(data) {
            console.log("formatData", data);

            let myData = []
            
            _( data ).chain().map( function ( val ) {
                return {
                    _key: val.key,
                    alert: val.alert,
                    category: val.category,
                    subcategory: val.subcategory,
                    tags: val.tags,
                    display_fields: val.display_fields,
                    drilldowns: val.drilldowns,
                    notification_scheme: val.notification_scheme,
                };
            }).each( function ( line ) {
                myData.push( line );
            });
            console.log(myData);

            return myData;
        },

    });
    return IncidentSettingsView;
});
