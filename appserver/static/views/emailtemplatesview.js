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

    var EmailTemplatesView = SimpleSplunkView.extend({
        className: "emailtemplatesview",

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

            $('<div />').attr('id', 'handson_container_templates').appendTo(this.$el);

            //debugger;
            var template_files = new Array();

            var url = splunkUtil.make_url('/custom/alert_manager/helpers/get_email_template_files');
            $.get( url,function(data) { 
                _.each(data, function(el) { 
                    template_files.push(el);
                });
            }, "json");
            console.debug("template_files", template_files);

            tl_headers = [ { col: "_key", tooltip: false }, 
                        { col: "template_name", tooltip: "Set a name for the e-mail template configuration. This reference will be used to refer in the Apps' Global Settings and E-Mail settings (see above)." },
                        { col: "template_file", tooltip: "Select the template's file name located in the App's default/templates or local/templates folder. Refresh this page when the templates doesn't appear." },
                        { col: "content_type", tooltip: false, },
                        { col: "subject", tooltip: false },
                        { col: "attachments", tooltip: "Blank separated list of static attachments" } ];

            $("#handson_container_templates").handsontable({
                data: data,
                columns: [
                    {
                        data: "_key",
                        readOnly: true
                    },
                    {
                        data: "template_name",
                    },
                    {
                        data: "template_file",
                        type: "dropdown",
                        source: template_files,
                    },
                    {
                        data: "content_type",
                        type: "dropdown",
                        source: ["plain_text", "html"],
                    },
                    {
                        data: "subject"
                    },
                    {
                        data: "attachments"
                    }
                ],
                colHeaders: true,
                colHeaders: function (col) {
                    colval = tl_headers[col]["col"];

                    if (tl_headers[col]["tooltip"] != undefined) {
                        if (tl_headers[col]["tooltip"] != false) {
                            colval = tl_headers[col]["col"] + '<a href="#" data-container="body" class="tooltip-link" data-toggle="tooltip" title="'+ tl_headers[col]["tooltip"] +'">?</a>';
                        }
                    }
                    
                    return colval;
                },
                cells: function (row, col, prop) {
                    var cellProperties = {};
                    if (this.instance.getData()[row]["_key"] === 'n/a') {
                        //cellProperties.readOnly = true; 
                    }
                    return cellProperties;
                },
                stretchH: 'all',
                contextMenu: ['row_above', 'row_below', 'remove_row', 'undo', 'redo'],
                startRows: 2,
                startCols: 1,
                minSpareRows: 1,
                minSpareCols: 0,
                afterRender: function() {
                    $(function () {
                        $('[data-toggle="tooltip"]').tooltip()
                    })
                },
                beforeRemoveRow: function(row) {
                    console.debug("row", row);
                    var data = $("#handson_container_templates").data('handsontable').getData();
                    console.log("_key", data[row]['_key']);
                    
                    if(!data[row]['_key'] && !data[row]['template_name'] && !data[row]['template_file']) {
                        this.del_key_container = false;
                        return true;
                    } else {
                        if(confirm('Are you sure to remove email template "' + data[row]['template_name'] + '"?')) {
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

                    var url = splunkUtil.make_url('/custom/alert_manager/email_templates/delete_template');
                    console.debug("url", url);

                    $.ajax( url,
                            {
                                uri:  url,
                                type: 'POST',
                                data: post_data,
                                
                               
                                success: function(jqXHR, textStatus){
                                    this.del_key_container = '';
                                    // Reload the table
                                    mvc.Components.get("email_templates_search").startSearch()
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
                    template_name: val.template_name, 
                    template_file: val.template_file,
                    content_type: val.content_type,
                    subject: val.subject,
                    attachments: val.attachments
                };
            }).each(function(line) {
                myData.push(line);        
            });

            return myData;
        },

    });
    return EmailTemplatesView;
});
