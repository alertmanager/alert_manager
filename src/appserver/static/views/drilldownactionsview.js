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

    var DrilldownActionsView = SimpleSplunkView.extend({
        className: "drilldownactionssview",

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
                        { col: "name", tooltip: "Name of the Drilldown. Spaces not allowed" },
                        { col: "label", tooltip: "The label of the drilldown"},
                        { col: "url", tooltip: "The drilldown url. Use syntax $field$ for replacements."}];
            $("#handson_container").handsontable({
                data: data,
                columns: [
                    {
                        data: "_key",
                        readOnly: true
                    },
                    {
                        data: "name",
                    },
                    {
                        data: "label",
                    },
                    {
                        data: "url",
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
                    if(confirm('Are you sure to remove settings for drilldown action "' + data[row]['name'] + '"?')) {
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

                    var rest_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/drilldown_actions');
                    var post_data = {
                        action : 'delete_drilldown_action',
                        key    : this.del_key_container
                    };
          	        $.post( rest_url, post_data, function(data, status) {
                        this.del_key_container = '';
                        // Reload the table
                        mvc.Components.get("drilldown_action_search").startSearch()
                    }, "text");


                }
            })
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
                    name: val.name,
                    label: val.label,
                    url: val.url
                };
            }).each(function(line) {
                myData.push(line);
            });

            return myData;
        },

    });
    return DrilldownActionsView;
});
