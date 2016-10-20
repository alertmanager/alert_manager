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
        'text!../app/alert_manager/templates/SuppressionRuleList.html',
        "datatables",
        "bootstrapDataTables",
    	'bootstrap.modal',
    	'bootstrap.tab',
        "css!../app/alert_manager/contrib/DataTables/css/jquery.dataTables.css",
        "css!../app/alert_manager/contrib/DataTables/css/dataTables.bootstrap.css",
        "css!../app/alert_manager/SplunkDataTables.css"],
function(_, mvc, $, SimpleSplunkView, SuppressionRulesListTemplate, dataTables) {
	
    // Define the custom view class
    var SuppressionRulesListerView = SimpleSplunkView.extend({
        className: "SuppressionRulesListerView",

        events: {
            "click .edit_suppression_rule": "editSuppressionRule",
            "click .add_suppression_rule": "addSuppressionRule",
            "click .save_suppression_rule": "doEditSuppressionRule",
            "click .enable_suppression_rule": "toggleSuppressionRule",
            "click .disable_suppression_rule": "toggleSuppressionRule",
            "click .remove_suppression_rule": "removeSuppresionRule",
            "shown .suppression-rule-edit-modal" : "focusView",
            /*"click .edit_lookup_managed": "editManagedLookup",
            "click .add_lookup_managed": "addManagedLookup",
            "click .save-managed-lookup" : "doEditLookup",
            "change #lookup-transform-list" : "onSelectTransform",
            "change #lookup-file-list" : "onSelectLookup",
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

            this.suppression_rules = null;
            this.unfiltered_suppression_rules = null;

        },

        /**
         * Fixes an issue where clicking an input loses focus instantly due to a problem in Bootstrap.
         * 
         * http://stackoverflow.com/questions/11634809/twitter-bootstrap-focus-on-textarea-inside-a-modal-on-click
         */
        focusView: function(){
            $('#suppression-rule-title', this.$el).focus();
        },


        showEditSuppressionRuleModal: function(key){
            
            // Get the managed lookup info
            var suppression_rule = this.getSuppressionRule(key);
            
            // Populate the form
            this.populateFormWithManagedLookup(suppression_rule);
            
            // Show the modal
            //$('.new-entry', this.$el).hide();
            $('.suppression-rule-edit-modal', this.$el).modal();
        },

        editSuppressionRule: function(event){
            var key = $(event.target).data('key');
            
            this.showEditSuppressionRuleModal(key);
        },

        populateFormWithManagedLookup: function(suppression_rule, only_if_blank){
            
            if( typeof only_if_blank === 'undefined' ){
                only_if_blank = false;
            }
                        
            if( $('#suppression-rule-title', this.$el).val().length === 0 || !only_if_blank){
                $('#suppression-rule-title', this.$el).val(suppression_rule.suppression_title);
            }
            
            if( $('#suppression-rule-description', this.$el).val().length === 0 || !only_if_blank){
                $('#suppression-rule-description', this.$el).val(suppression_rule.description);
            }

            if( suppression_rule.suppression_type !== null && $('#suppression-rule-type', this.$el).val() !== suppression_rule.suppression_type){
                $('#suppression-rule-type', this.$el).val(suppression_rule.suppression_type);
            }

            if( suppression_rule.match_type !== null && $('#suppression-rule-match-type', this.$el).val() !== suppression_rule.match_type){
                $('#suppression-rule-match-type', this.$el).val(suppression_rule.match_type);
            }

            if( $('#suppression-rule-scope', this.$el).val().length === 0 || !only_if_blank){
                $('#suppression-rule-scope', this.$el).val(suppression_rule.scope);
            }
                        
            $('#suppression-rule-key', this.$el).val(suppression_rule._key);
            
            this.populated_form_automatically = true;
        },

        addSuppressionRule: function(event){
            
            // Clear the form
            this.clearForm();
            
            // Show the modal
            //$('.new-entry', this.$el).show();
            $('.suppression-rule-edit-modal', this.$el).modal();
        },

        clearForm: function(){
            $('#suppression-rule-type', this.$el).val("normal");
            $('#suppression-rule-match-type', this.$el).val("all");
            $('#suppression-rule-title', this.$el).val("");
            $('#suppression-rule-description', this.$el).val("");
            $('#suppression-rule-scope', this.$el).val("");
            $('#suppression-rule-key', this.$el).val("");
        },

        doEditSuppressionRule: function(){
            
            // See if the input is valid
            /*if( !this.validate() ){
                return false;
            }*/
            
            // Get the key of the item being edited
            var key = $('#suppression-rule-key', this.$el).val(); // This will be empty for new items
            
            // Determine if this is a new entry
            var is_new = false;
            
            if(key === ""){
                is_new = true;
            }
            
           
            // Get the managed lookup info (if not new)
            var suppression_rule = {};
            
            if(!is_new){
                suppression_rule = this.getSuppressionRule(key);
            }
            
            // Update the attributes
            suppression_rule.suppression_title = $('#suppression-rule-title', this.$el).val();
            suppression_rule.description = $('#suppression-rule-description', this.$el).val();
            suppression_rule.suppression_type = $('#suppression-rule-type', this.$el).val();
            suppression_rule.match_type = $('#suppression-rule-match-type', this.$el).val();
            suppression_rule.scope = $('#suppression-rule-scope', this.$el).val();
            
            if(is_new){
                suppression_rule.disabled = false;
            }
            
            
            this.doUpdateToSuppressionRule(suppression_rule, key);
            return true;
        },

        toggleSuppressionRule: function(event){
            var key = $(event.target).data('key');
            var disabled = $(event.target).data('disabled');
            
            suppression_rule = this.getSuppressionRule(key);
            suppression_rule.disabled = disabled;
            this.doUpdateToSuppressionRule(suppression_rule, key);
        },

        removeSuppresionRule: function (event) {           
            var key = $(event.target).data('key');
            suppression_rule = this.getSuppressionRule(key);

            if (confirm('Are you sure you want to delete: "'+ suppression_rule.suppression_title+'"?')) {

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
                            alert("You do not have permission to update suppression rules.");
                        }
                        else{
                            alert("The suppression rule could not be modified: \n\n" + errorThrown);
                        }
                    },
                    success: function() {
                        this.renderSuppressionRulesList();
                    }.bind(this)
                });
                
                return true;         
            } else {
                return false;
            }
        },

        doUpdateToSuppressionRule: function(suppression_rule, key){
            
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
                data: JSON.stringify(suppression_rule),
                error: function(jqXHR, textStatus, errorThrown ){
                    if( jqXHR.status === 403 ){
                        alert("You do not have permission to update suppression rules.");
                    }
                    else{
                        alert("The suppression rule could not be modified: \n\n" + errorThrown);
                    }
                },
                success: function() {
                    this.renderSuppressionRulesList();
                    $('.suppression-rule-edit-modal', this.$el).modal('hide');
                }.bind(this)
            });
            
            return true;
        },

        getSuppressionRules: function(force_reload){

            // Default the arguments
            if(typeof force_reload === "undefined"){
                force_reload = false;
            }
            
            // Return the existing list if we can
            if(this.suppression_rules !== null && !force_reload){
                return this.suppression_rules;
            }
            
            this.suppression_rules = this.getSuppressionRule("");
            console.log("suppression_rules", this.suppression_rules);
            return this.suppression_rules;

        },

        getSuppressionRule: function(key){
            
            var uri = Splunk.util.make_url("/splunkd/__raw/servicesNS/" + this.collection_owner + "/" + this.app + "/storage/collections/data/" + this.collection + "/" + key + "?output_mode=json");
            var suppression_rules = null;
            
            jQuery.ajax({
                url:     uri,
                type:    'GET',
                async:   false,
                success: function(results) {
                    
                    // Use the include filter function to prune items that should not be included (if necessary)
                    if( key === "" && this.include_filter !== null ){
                        suppression_rules = [];
                        
                        // Store the unfiltered list of lookups
                        this.unfiltered_suppression_rules = results;
                        
                        for( var c = 0; c < results.length; c++){
                            if( this.include_filter(results[c]) ){
                                suppression_rules.push(results[c]);
                            }
                        }
                    }
                    
                    // Just pass the lookups if no filter is necessary.
                    else{
                        suppression_rules = results;
                    }
                }.bind(this)
            });
            
            return suppression_rules;
        },

        renderSuppressionRulesList: function(){
            var suppression_rules = this.getSuppressionRules(true);

            //var insufficient_permissions = !this.hasCapability('edit_lookups');
            var insufficient_permissions = false;

            // Template from el
            var lookup_list_template = $('#suppression-rule-list-template', this.$el).text();

            $('#table-container', this.$el).html( _.template(lookup_list_template,{ 
                suppression_rules: suppression_rules,
                editor: this.editor,
                list_link: this.list_link,
                list_link_title: this.list_link_title,
                insufficient_permissions: insufficient_permissions,
                allow_editing_collection: this.allow_editing_collection
            }));


            var columnMetaData = [
                                  null,                   // Title
                                  null,                   // Description
                                  null,                   // Type
                                  null,                   // Scope
                                  null,                   // Rules
                                  { "bSortable": false }  // Actions
                                ];
            
            if(insufficient_permissions){
                columnMetaData = [
                                      null,                   // Title
                                      null,                   // Description
                                      null,                   // Type
                                      null,                   // Scope
                                      null,                   // Rules
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
            this.$el.html(SuppressionRulesListTemplate);
            this.renderSuppressionRulesList();
        },

    });
    return SuppressionRulesListerView;
});        