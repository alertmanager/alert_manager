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

    var EmailSettingsView = SimpleSplunkView.extend({
        className: "emailsettingsview",

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

            $('<div />').attr('id', 'handson_container_settings').appendTo(this.$el);

            //debugger;
            var templates = new Array();

            var url = splunkUtil.make_url('/custom/alert_manager/helpers/get_email_templates');
            $.get( url,function(data) { 
                _.each(data, function(el) { 
                    templates.push(el);
                });
            }, "json");
            console.debug("templates", templates);

            headers = [ { col: "_key", tooltip: false }, 
                        { col: "alert", tooltip: false },
                        { col: "notify_user_template", tooltip: "Select template to be used when sending notifications to users on incident assignment (including auto_assign)" } ];
            $("#handson_container_settings").handsontable({
                data: data,
                minSpareRows: 1,
                columns: [
                    {
                        data: "_key",
                        readOnly: true
                    },
                    {
                        data: "alert",
                    },
                    {
                        data: "notify_user_template",
                        type: "dropdown",
                        source: templates
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
                cells: function (row, col, prop) {
                    var cellProperties = {};
                    if (this.instance.getData()[row]["_key"] === 'n/a') {
                        cellProperties.readOnly = true; 
                    }
                    return cellProperties;
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
                    console.debug("row", row);
                    var data = $("#handson_container_settings").data('handsontable').getData();
                    console.log("_key", data[row]['_key']);
                    
                    if(!data[row]['_key'] && !data[row]['alert'] && !data[row]['notify_user_template']) {
                        this.del_key_container = false;
                        return true;
                    } else {
                        if(confirm('Are you sure to remove email settings for alert "' + data[row]['alert'] + '"?')) {
                            if(!data[row]['_key']) {
                                this.del_key_container = false;
                            } else {
                                this.del_key_container = data[row]['_key'];
                            }
                            return true;
                        } else {
                            return false;
                        }
                    }
                    
                },
                afterRemoveRow: function(row) {
                    console.debug("afterRemoveRow");
                    //var data = $("#handson_container").data('handsontable').getData();
                    console.debug("row", row);
                    //console.debug("data", data);
                    console.debug("key", this.del_key_container);
                    if(this.del_key_container == false) {
                        // Removal of empty row - nothing to do
                        return true;
                    }

                    var post_data = {
                        key    : this.del_key_container
                    };

                    var url = splunkUtil.make_url('/custom/alert_manager/email_settings/delete_settings');
                    console.debug("url", url);

                    $.ajax( url,
                            {
                                uri:  url,
                                type: 'POST',
                                data: post_data,
                                
                               
                                success: function(jqXHR, textStatus){
                                    this.del_key_container = '';
                                    // Reload the table
                                    mvc.Components.get("email_settings_search").startSearch()
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
                    notify_user_template: val.notify_user_template
                };
            }).each(function(line) {
                myData.push(line);        
            });

            return myData;
        },

    });
    return EmailSettingsView;
});
