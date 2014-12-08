require.config({
    paths: {
        "app": "../app"
    },
    shim: {
        "app/alert_manager/handsontable.full": {
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
    var Handsontable = require('app/alert_manager/handsontable.full');
    //require('app/netatmo/amcharts/serial');

    var HandsontableView = SimpleSplunkView.extend({
        className: "handsontableview",

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


            //debugger;
            $("#" + id).handsontable({
                data: data,
                minSpareRows: 1,
                colHeaders: ["search_name", "auto_assign", "auto_assign_user", "auto_ttl_resolve", "auto_previous_resolve"],
                columns: [
                    {
                        data: "search_name",
                        readOnly: true
                    },
                    {
                        data: "auto_assign",
                        type: "checkbox"
                    },
                    {
                        data: "auto_assign_user",
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
                contextMenu: true
            });

            $('<button>Save settings</button>').appendTo(this.$el);
          //debugger;
          //id

        },

        // Override this method to format the data for the view
        formatData: function(data) {
            console.log("formatData", data);

            /*var valueField1 = this.settings.get('valueField1');
            var valueField2 = this.settings.get('valueField2');
            var valueField3 = this.settings.get('valueField3');
            var categoryField = this.settings.get('categoryField');
            var colorField = this.settings.get('colorField');*/

            myData = []

             _(data).chain().map(function(val, key) {
                return {
                    search_name: val['search_name'], 
                    auto_assign: parseInt(val['auto_assign']) ? true : false,
                    auto_assign_user: val['auto_assign_user'],
                    auto_ttl_resolve: parseInt(val['auto_ttl_resolve']) ? true : false,
                    auto_previous_resolve: parseInt(val['auto_previous_resolve']) ? true : false
                };
             }).each(function(line) {
                myData.push(line);
             });

            return myData;
        },

    });
    return HandsontableView;
});