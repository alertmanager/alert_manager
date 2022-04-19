require.config({
    paths: {
        SuppressionRuleListerView: "../app/alert_manager/views/SuppressionRuleListerView"
    }
});

require([
         "jquery",
         "underscore",
         "backbone",
         "SuppressionRuleListerView",
         "splunkjs/mvc/simplexml/ready!",
         "select2/select2"
     ], function($, _, Backbone, SuppressionRuleListerView, Select)
     {
         var SuppressionRuleListerView = new SuppressionRuleListerView({
        	 'el': $("#suppression_rules"),
        	 'app': 'alert_manager',
        	 'collection' : 'suppression_rules',
        	 'editor' : 'suppression_rules_edit',
        	 'allow_editing_collection': true
         });
         
         SuppressionRuleListerView.render();
     }
);