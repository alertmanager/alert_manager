require.config({
    paths: {
        NotificationSchemeListerView: "../app/alert_manager/views/NotificationSchemeListerView"
    }
});

require([
         "jquery",
         "underscore",
         "backbone",
         "NotificationSchemeListerView",
         "splunkjs/mvc/simplexml/ready!"
     ], function($, _, Backbone, NotificationSchemeListerView)
     {
         var NotificationSchemeListerView = new NotificationSchemeListerView({
        	 'el': $("#notification_schemes"),
        	 'app': 'alert_manager',
        	 'collection' : 'notification_schemes',
        	 'editor' : 'notification_schemes_edit',
        	 'allow_editing_collection': true
         });
         
         NotificationSchemeListerView.render();
     }
);