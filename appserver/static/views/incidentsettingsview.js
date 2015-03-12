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

            var users = new Array();
            users.push("unassigned");

            var url = splunkUtil.make_url('/custom/alert_manager/helpers/get_users');
            $.get( url,function(data) { 
                _.each(data, function(el) { 
                    users.push(el.name);
                });
            }, "json");


            headers = [ { col: "_key", tooltip: false }, 
                        { col: "alert", tooltip: false },
                        { col: "category", tooltip: false },
                        { col: "subcategory", tooltip: false },
                        { col: "tags", tooltip: "Space separated list of tags" },
                        { col: "urgency", tooltip: "The default urgency for this alert if urgency field is not provided in the results. Used together with impact to calculate the alert's priority" },
                        { col: "display_fields", tooltip: "Space separated list of fields to display in incident details."},
                        { col: "run_alert_script", tooltip: "Run classic Splunk scripted alert script. The Alert Manager will pass all arguments" },
                        { col: "alert_script",  tooltip: "Name of the Splunk alert script" },
                        { col: "auto_assign", tooltip: "Auto-assign new incidents and change status to 'assigned'." },
                        { col: "auto_assign_owner", tooltip: "Username of the user the incident will be assigned to" },
                        { col: "auto_ttl_resolve", tooltip: "Auto-resolve incidents in status 'new' who reached their expiry" },
                        { col: "auto_previous_resolve", tooltip: "Auto-resolve previously created incidents in status 'new'" } ];
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
                        data: "urgency",
                        type: "dropdown",
                        source: ["low", "medium", "high"],
                    },
                    {
                        data: "display_fields",
                    },
                    {
                        data: "run_alert_script",
                        type: "checkbox"
                    },
                    {
                        data: "alert_script",
                    },
                    {
                        data: "auto_assign",
                        type: "checkbox"
                    },
                    {
                        data: "auto_assign_owner",
                        type: "dropdown",
                        source: users,
                    },
                    {
                        data: "auto_ttl_resolve",
                        type: "checkbox"
                    },
                    {
                        data: "auto_previous_resolve",
                        type: "checkbox"
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
                minSpareRows: 0,
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

                    var post_data = {
                        key    : this.del_key_container
                    };

                    var url = splunkUtil.make_url('/custom/alert_manager/incident_settings/delete');
                    console.debug("url", url);

                    $.ajax( url,
                            {
                                uri:  url,
                                type: 'POST',
                                data: post_data,
                                
                               
                                success: function(jqXHR, textStatus){
                                    this.del_key_container = '';
                                    // Reload the table
                                    mvc.Components.get("incident_settings_search").startSearch()
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
                }
            });
            //console.debug("id", id);


          //debugger;
          //id

        },

        // Override this method to format the data for the view
        formatData: function(data) {
            console.log("formatData", data);

            myData = []
             _(data).chain().map(function(val) {
                return {
                    _key: val.key,
                    alert: val.alert, 
                    category: val.category,
                    subcategory: val.subcategory, 
                    tags: val.tags, 
                    urgency: val.urgency, 
                    display_fields: val.display_fields, 
                    run_alert_script: parseInt(val.run_alert_script) ? true : false,
                    alert_script: val.alert_script,
                    auto_assign: parseInt(val.auto_assign) ? true : false,
                    auto_assign_owner: val.auto_assign_owner,
                    auto_ttl_resolve: parseInt(val.auto_ttl_resolve) ? true : false,
                    auto_previous_resolve: parseInt(val.auto_previous_resolve) ? true : false
                };
            }).each(function(line) {
                myData.push(line);        
            });

            return myData;
        },

    });
    return IncidentSettingsView;
});
