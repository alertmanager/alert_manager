
require.config({
    paths: {
        NotificationSchemeEditorView: "../app/alert_manager/views/NotificationSchemeEditorView"
    }
});

require([
         "jquery",
         "underscore",
         "backbone",
         "NotificationSchemeEditorView",
         "splunkjs/mvc/simplexml/ready!"
     ], function($, _, Backbone, NotificationSchemeEditorView)
     {
         var NotificationSchemeEditorView = new NotificationSchemeEditorView({
        	 'el': $("#notification_schemes_editor"),
             'app': 'alert_manager',
             'collection' : 'notification_schemes',             
        	 'lister' : 'notification_schemes',
        	 'list_link_title': 'Back to Notification Scheme List',
        	 'list_link': 'notification_schemes'
         });
         
         NotificationSchemeEditorView.render();
     }
);
