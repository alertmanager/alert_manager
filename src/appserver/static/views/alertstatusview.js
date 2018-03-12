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

    var AlertStatusView = SimpleSplunkView.extend({
        className: "alertstatusview",

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

            headers = [ { col: "_key", tooltip: false },
                        { col: "builtin", tooltip: false },
                        { col: "internal_only", tooltip: 'Only non-internal status are shown in the UI. Custom alert status are always non-internal.'},
                        { col: "status", tooltip: 'The name of the status. No spaces allowed' },
                        { col: "status_description", tooltip: 'The human-readable name of the status.' } ]
            $("#handson_container").handsontable({
                data: data,
                columns: [
                    {
                        data: "_key",
                        readOnly: true
                    },
                    {
                        data: "builtin",
                        type: "checkbox",
                        checkedTemplate: '1',
                        uncheckedTemplate: '0',
                        readOnly: true
                    },
                    {
                        data: "internal_only",
                        type: "checkbox",
                        checkedTemplate: '1',
                        uncheckedTemplate: '0'
                    },
                    {
                        data: "status"
                    },
                    {
                        data: "status_description"
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
                    if(confirm('Are you sure to remove alert status "' + data[row]['status'] + '"?')) {
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

                    var rest_url = splunkUtil.make_url('/splunkd/__raw/services/alert_status');
                    var post_data = {
                        action : 'delete_alert_status',
                        key    : this.del_key_container
                    };
          	        $.post( rest_url, post_data, function(data, status) {
                        this.del_key_container = '';
                        // Reload the table
                        mvc.Components.get("alert_status_search").startSearch()
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

            myData = []
             _(data).chain().map(function(val) {
                return {
                    _key: val.key,
                    internal_only: val.internal_only,
                    builtin: val.builtin,
                    status: val.status,
                    status_description: val.status_description
                };
            }).each(function(line) {
                myData.push(line);
            });

            return myData;
        },

    });
    return AlertStatusView;
});
