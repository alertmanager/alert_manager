require.config({
    paths: {
        datatables: "../app/alert_manager/contrib/DataTables/js/jquery.dataTables",
        bootstrapDataTables: "../app/alert_manager/contrib/DataTables/js/dataTables.bootstrap",
        text: "../app/alert_manager/contrib/text",
    },
    shim: {
        'bootstrapDataTables': {
            deps: ['datatables']
        }
    }
});

define(['underscore',
        'splunkjs/mvc',
        'jquery',
        'splunkjs/mvc/simplesplunkview',
        'text!../app/alert_manager/templates/NotificationSchemeList.html',
        "datatables",
        "bootstrapDataTables",
    	'bootstrap.modal',
    	'bootstrap.tab',
        "css!../app/alert_manager/contrib/DataTables/css/jquery.dataTables.css",
        "css!../app/alert_manager/contrib/DataTables/css/dataTables.bootstrap.css",
        "css!../app/alert_manager/SplunkDataTables.css"],
function(_, mvc, $, SimpleSplunkView, NotificationSchemesListTemplate, dataTables) {
	
    // Define the custom view class
    var NotificationSchemeListerView = SimpleSplunkView.extend({
        className: "NotificationSchemeListerView",

        events: {
            "click .edit_notification_scheme": "editNotificationScheme",
            "click .add_notification_scheme": "addNotificationScheme",
            "click .save_notification_scheme": "doEditNotificationScheme",
            "click .remove_notification_scheme": "removeNotificationScheme",
            "shown .notification-scheme-edit-modal" : "focusView",
            /*"click .edit_lookup_managed": "editManagedLookup",
            "click .add_lookup_managed": "addManagedLookup",
            "click .save-managed-lookup" : "doEditLookup",
            "change #lookup-transform-list" : "onSelectTransform",
            "change #lookup-file-list" : "onSelectLookup",
            "shown .lookup-edit-modal" : "focusView",
            "keypress #lookup-transform" : "manuallyEdited",
            "keypress #lookup-label" : "manuallyEdited",
            "keypress #lookup-description" : "manuallyEdited"*/
        },

        defaults: {
            collection_owner: "nobody",
            include_filter: null,
            list_link: null,
            list_link_title: "Back to list",
            allow_editing_collection: true
        },

        initialize: function() {
            this.options = _.extend({}, this.defaults, this.options);

            this.list_link = this.options.list_link;
            this.list_link_title= this.options.list_link_title;
            this.editor = this.options.editor;
            this.include_filter = this.options.include_filter;
            this.allow_editing_collection = this.options.allow_editing_collection;

            this.collection_owner = this.options.collection_owner;
            this.app = this.options.app;
            this.collection = this.options.collection;

            this.notification_schemes = null;
            this.unfiltered_notification_schemes = null;

        },

        /**
         * Fixes an issue where clicking an input loses focus instantly due to a problem in Bootstrap.
         * 
         * http://stackoverflow.com/questions/11634809/twitter-bootstrap-focus-on-textarea-inside-a-modal-on-click
         */
        focusView: function(){
            $('#notification-scheme-displayname', this.$el).focus();
        },

        showEditNotificationSchemeModal: function(key){
            
            // Get the managed lookup info
            var notification_scheme = this.getNotificationScheme(key);
            
            // Populate the form
            this.populateFormWithManagedLookup(notification_scheme);
            
            // Show the modal
            //$('.new-entry', this.$el).hide();
            $('.notification-scheme-edit-modal', this.$el).modal();
        },

        editNotificationScheme: function(event){
            var key = $(event.target).data('key');
            
            this.showEditNotificationSchemeModal(key);
        },

        populateFormWithManagedLookup: function(notification_scheme, only_if_blank){
            
            if( typeof only_if_blank === 'undefined' ){
                only_if_blank = false;
            }
                        
            if( $('#notification-scheme-displayname', this.$el).val().length === 0 || !only_if_blank){
                $('#notification-scheme-displayname', this.$el).val(notification_scheme.displayName);
            }
            
            if( $('#notification-scheme-schemename', this.$el).val().length === 0 || !only_if_blank){
                $('#notification-scheme-schemename', this.$el).val(notification_scheme.schemeName);
            }
                        
            $('#notification-scheme-key', this.$el).val(notification_scheme._key);
            
            this.populated_form_automatically = true;
        },

        addNotificationScheme: function(event){
            
            // Clear the form
            this.clearForm();
            
            // Show the modal
            //$('.new-entry', this.$el).show();
            $('.notification-scheme-edit-modal', this.$el).modal();
        },

        clearForm: function(){
            $('#notification-scheme-displayName', this.$el).val("");
            $('#notification-scheme-schemeName', this.$el).val("");
            $('#notification-scheme-key', this.$el).val("");
        },

        doEditNotificationScheme: function(){
            
            // See if the input is valid
            /*if( !this.validate() ){
                return false;
            }*/
            
            // Get the key of the item being edited
            var key = $('#notification-scheme-key', this.$el).val(); // This will be empty for new items
            
            // Determine if this is a new entry
            var is_new = false;
            
            if(key === ""){
                is_new = true;
            }
            
           
            // Get the managed lookup info (if not new)
            var notification_scheme = {};
            
            if(!is_new){
                notification_scheme = this.getNotificationScheme(key);
            }
            
            // Update the attributes
            notification_scheme.displayName = $('#notification-scheme-displayname', this.$el).val();
            notification_scheme.schemeName = $('#notification-scheme-schemename', this.$el).val();
            
            this.doUpdateToNotificationScheme(notification_scheme, key);
            return true;
        },

        /*toggleSuppressionRule: function(event){
            var key = $(event.target).data('key');
            var disabled = $(event.target).data('disabled');
            
            suppression_rule = this.getSuppressionRule(key);
            suppression_rule.disabled = disabled;
            this.doUpdateToSuppressionRule(suppression_rule, key);
        },*/


        removeNotificationScheme: function (event) {           
            var key = $(event.target).data('key');
            notification_scheme = this.getNotificationScheme(key);

            if (confirm('Are you sure you want to delete: "'+ notification_scheme.displayName+'"?')) {

                var uri = null;
                
                // If a key was provided, filter down to it
                if(key === undefined || key === "" || key === null){
                    alert("Unknown error. Please try again.");
                    return false;
                }
                else{
                    uri = Splunk.util.make_url("/splunkd/__raw/servicesNS/" + this.collection_owner + "/" + this.app + "/storage/collections/data/" + this.collection + "/" + key + "?output_mode=json");
                }

                jQuery.ajax({
                    url: uri,
                    type: 'DELETE',
                    async: false,
                    contentType: "application/json",
                    error: function(jqXHR, textStatus, errorThrown ){
                        if( jqXHR.status === 403 ){
                            alert("You do not have permission to update notification schemes.");
                        }
                        else{
                            alert("The suppression rule could not be modified: \n\n" + errorThrown);
                        }
                    },
                    success: function() {
                        this.renderNotificationSchemesList();
                    }.bind(this)
                });
                
                return true;         
            } else {
                return false;
            }
        },

        doUpdateToNotificationScheme: function(notification_scheme, key){
            
            var uri = null;
            
            // If a key was provided, filter down to it
            if(key === undefined || key === "" || key === null){
                uri = Splunk.util.make_url("/splunkd/__raw/servicesNS/" + this.collection_owner + "/" + this.app + "/storage/collections/data/" + this.collection + "?output_mode=json");
            }
            else{
                uri = Splunk.util.make_url("/splunkd/__raw/servicesNS/" + this.collection_owner + "/" + this.app + "/storage/collections/data/" + this.collection + "/" + key + "?output_mode=json");
            }
            
            jQuery.ajax({
                url: uri,
                type: 'POST',
                async: false,
                contentType: "application/json",
                data: JSON.stringify(notification_scheme),
                error: function(jqXHR, textStatus, errorThrown ){
                    if( jqXHR.status === 403 ){
                        alert("You do not have permission to update notification schemes.");
                    }
                    else{
                        alert("The notification scheme could not be modified: \n\n" + errorThrown);
                    }
                },
                success: function() {
                    this.renderNotificationSchemesList();
                    $('.notification-scheme-edit-modal', this.$el).modal('hide');
                }.bind(this)
            });
            
            return true;
        },

        getNotificationSchemes: function(force_reload){

            // Default the arguments
            if(typeof force_reload === "undefined"){
                force_reload = false;
            }
            
            // Return the existing list if we can
            if(this.notification_schemes !== null && !force_reload){
                return this.notification_schemes;
            }
            
            this.notification_schemes = this.getNotificationScheme("");
            console.log("notification_schemes", this.notification_schemes);
            return this.notification_schemes;

        },

        getNotificationScheme: function(key){
            
            var uri = Splunk.util.make_url("/splunkd/__raw/servicesNS/" + this.collection_owner + "/" + this.app + "/storage/collections/data/" + this.collection + "/" + key + "?output_mode=json");
            var notification_schemes = null;
            
            jQuery.ajax({
                url:     uri,
                type:    'GET',
                async:   false,
                success: function(results) {
                    
                    // Use the include filter function to prune items that should not be included (if necessary)
                    if( key === "" && this.include_filter !== null ){
                        notification_schemes = [];
                        
                        // Store the unfiltered list of lookups
                        this.unfiltered_notification_schemes = results;
                        
                        for( var c = 0; c < results.length; c++){
                            if( this.include_filter(results[c]) ){
                                notification_schemes.push(results[c]);
                            }
                        }
                    }
                    
                    // Just pass the lookups if no filter is necessary.
                    else{
                        notification_schemes = results;
                    }
                }.bind(this)
            });
            
            return notification_schemes;
        },

        renderNotificationSchemesList: function(){
            var notification_schemes = this.getNotificationSchemes(true);

            //var insufficient_permissions = !this.hasCapability('edit_lookups');
            var insufficient_permissions = false;

            // Template from el
            var lookup_list_template = $('#notification-scheme-list-template', this.$el).text();

            $('#table-container', this.$el).html( _.template(lookup_list_template,{ 
                notification_schemes: notification_schemes,
                editor: this.editor,
                list_link: this.list_link,
                list_link_title: this.list_link_title,
                insufficient_permissions: insufficient_permissions,
                allow_editing_collection: this.allow_editing_collection
            }));


            var columnMetaData = [
                                  null,                   // Display Name
                                  null,                   // Scheme Name
                                  null,                   // Notifications
                                  { "bSortable": false }  // Actions
                                ];
            
            if(insufficient_permissions){
                columnMetaData = [
                                      null,                   // Display Name
                                      null,                   // Scheme Name
                                      null,                   // Notifications
                                    ];
            }

            $('#table', this.$el).dataTable( {
                "iDisplayLength": 25,
                "bLengthChange": false,
                "bStateSave": true,
                "aaSorting": [[ 0, "asc" ]],
                "aoColumns": columnMetaData
              } );
            
            // Make the tabs into tabs
            $('#tabs', this.$el).tab();

        },

        render: function() {
            this.$el.html(NotificationSchemesListTemplate);
            this.renderNotificationSchemesList();
        },

    });
    return NotificationSchemeListerView;
});        