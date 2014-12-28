require.config({
    paths: {
        "app": "../app"
    },
    shim: {
        "app/alert_manager/lib/handsontable.full": {
            deps: [],
            exports: "Handsontable"
        },
    }
});


define(function(require, exports, module) {
    
    var _ = require('underscore');
    var $ = require('jquery');
    var mvc = require('splunkjs/mvc');
    var SimpleSplunkView = require('splunkjs/mvc/simplesplunkview');
    var Handsontable = require('app/alert_manager/lib/handsontable.full');
    var splunkUtil = require('splunk.util');

    require("css!../lib/handsontable.full.css");

    var UserSettingsView = SimpleSplunkView.extend({
        className: "usersettingsview",

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

            var id = _.uniqueId("handsontable");
            $('<div />').attr('id', id).height(this.settings.get('height')).width(this.settings.get('width')).appendTo(this.$el);
            $('<div />').attr('id', 'handson_container').appendTo("#"+id);

            //debugger;
            headers = [ { col: "_key", tooltip: false }, 
                        { col: "user", tooltip: false },
                        { col: "email", tooltip: false },
                        { col: "send_email", tooltip: false },
                        { col: "type", tooltip: false} ];
            $("#handson_container").handsontable({
                data: data,
                minSpareRows: 1,
                columns: [
                    {
                        data: "_key",
                        readOnly: true
                    },
                    {
                        data: "user",
                    },
                    {
                        data: "email",
                    },
                    {
                        data: "send_email",
                        type: "checkbox",
                    },
                    {
                        data: "type",
                        readOnly: true
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
                    if (this.instance.getData()[row]["type"] === 'builtin') {
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
                    var data = $("#handson_container").data('handsontable').getData();
                    console.log("_key", data[row]['_key']);
                    console.debug("data[row]['type']", data[row]['type']);
                    if(data[row]['type'] && data[row]['type'] == "builtin") {
                        this.del_key_container = false;
                        return false;
                    } else {
                        if(!data[row]['_key'] && !data[row]['user'] && !data[row]['email']) {
                            this.del_key_container = false;
                            return true;
                        } else {
                            if(confirm('Are you sure to remove user "' + data[row]['user'] + '"?')) {
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

                    var url = splunkUtil.make_url('/custom/alert_manager/user_settings/delete');
                    console.debug("url", url);

                    $.ajax( url,
                            {
                                uri:  url,
                                type: 'POST',
                                data: post_data,
                                
                               
                                success: function(jqXHR, textStatus){
                                    this.del_key_container = '';
                                    // Reload the table
                                    mvc.Components.get("user_settings_search").startSearch()
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
            console.debug("id", id);


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
                    user: val.user, 
                    email: val.email,
                    send_email: parseInt(val.send_email) ? true : false,
                    type: val.type
                };
            }).each(function(line) {
                myData.push(line);        
            });

            return myData;
        },

    });
    return UserSettingsView;
});
