
require.config({
    paths: {
        SuppressionRuleEditorView: "../app/alert_manager/views/SuppressionRuleEditorView"
    }
});

require([
         "jquery",
         "underscore",
         "backbone",
         "SuppressionRuleEditorView",
         "splunkjs/mvc/simplexml/ready!",
         "select2/select2"
     ], function($, _, Backbone, SuppressionRuleEditorView, Select)
     {
         var SuppressionRuleEditorView = new SuppressionRuleEditorView({
        	 'el': $("#suppression_rules_editor"),
             'app': 'alert_manager',
             'collection' : 'suppression_rules',             
        	 'lister' : 'suppression_rules',
        	 'list_link_title': 'Back to Suppression Rule List',
        	 'list_link': 'suppression_rules'
         });
         
         SuppressionRuleEditorView.render();
     }
);
