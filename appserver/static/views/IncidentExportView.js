require.config({
    paths: {
        text: "../app/alert_manager/contrib/text",
        "app": "../app"
    },
});

define(['underscore',
        'splunkjs/mvc',
        'jquery',
        'splunkjs/mvc/simplesplunkview',
        'text!app/alert_manager/templates/IncidentExport.html'],
function(_, mvc, $, SimpleSplunkView, IncidentExportTemplate) {
	
    // Define the custom view class
    var IncidentExportView = SimpleSplunkView.extend({
        className: "IncidentExportView",

        options: {
            data: "preview",  // The data results model from a search
        },
        output_mode: 'json',

        updateView: function(viz, data) {
            console.log("updateView", data);
            console.log("incident_id", this.settings.get('incident_id'));
            this.$el.empty();

            this.$el.html( _.template(IncidentExportTemplate,{ 
                data: data,
                incident_id: this.settings.get('incident_id'),
            })); 
        },

        formatData: function(data) {
            console.log("formatData");
            
            return data;
        },

        createView: function() { 
            console.log("createView");
            return { container: this.$el, } ;
        },



    });
    return IncidentExportView;
});        