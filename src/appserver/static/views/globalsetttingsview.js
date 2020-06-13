"use strict";

define(
    ["backbone", "jquery", "splunkjs/splunk"],
    function(Backbone, jquery, splunk_js_sdk) {
        sdk = splunk_js_sdk;
        var GlobalSettingsView = Backbone.View.extend({
            // -----------------------------------------------------------------
            // Backbone Functions, These are specific to the Backbone library
            // -----------------------------------------------------------------
            initialize: function initialize() {
                Backbone.View.prototype.initialize.apply(this, arguments);
                this.init_properties(splunk_js_sdk,"alert_manager","alert_manager","settings","index","input","idx","main");
                this.init_properties(splunk_js_sdk,"alert_manager","alert_manager","settings","default_owner","input","default_owner","unassigned");
                this.init_properties(splunk_js_sdk,"alert_manager","alert_manager","settings","default_priority","select","default_priority","low");
                this.init_properties(splunk_js_sdk,"alert_manager","alert_manager","settings","incident_list_length","input","incident_list_length","10");
                this.init_properties(splunk_js_sdk,"alert_manager","alert_manager","settings","auto_close_info_status","input","auto_close_info_status","auto_info_resolved");
                this.init_properties(splunk_js_sdk,"alert_manager","alert_manager","settings","incident_list_length","input","incident_list_length","10");
                this.init_properties(splunk_js_sdk,"alert_manager","alert_manager","settings","auto_close_info_status","input","auto_close_info_status","auto_info_resolved");

                this.init_properties(splunk_js_sdk,"alert_manager","alert_manager","settings","collect_data_results","checkbox","collect_data_results", true);
                this.init_properties(splunk_js_sdk,"alert_manager","alert_manager","settings","index_data_results","checkbox","index_data_results", false);
                this.init_properties(splunk_js_sdk,"alert_manager","alert_manager","settings","auto_close_info","checkbox","auto_close_info", false);

                this.init_properties(splunk_js_sdk,"alert_manager","alert_actions","alert_manager","param.impact","select","param_impact","low");
                this.init_properties(splunk_js_sdk,"alert_manager","alert_actions","alert_manager","param.urgency","select","param_urgency","low");
            },

            events: {
                "click .setup_button": "trigger_setup",
            },

            render: function() {
                this.el.innerHTML = this.get_template(splunk_js_sdk);

                return this;
            },

            // -----------------------------------------------------------------
            // Custom Functions, These are unrelated to the Backbone functions
            // -----------------------------------------------------------------
            // ----------------------------------
            // Main Setup Logic
            // ----------------------------------
            // This performs some sanity checking and cleanup on the inputs that
            // the user has provided before kicking off main setup process
            trigger_setup: function trigger_setup() {
                // Used to hide the error output, when a setup is retried
                this.display_error_output([]);

                console.log("Triggering setup");
                var idx_input_element = jquery("input[name=idx]");
                var idx = idx_input_element.val();
                var sanitized_idx = this.sanitize_string(idx);

                var default_owner_input_element = jquery("input[name=default_owner]");
                var default_owner = default_owner_input_element.val();
                var sanitized_default_owner = this.sanitize_string(default_owner);
                
                var default_priority_input_element = jquery("select[name=default_priority]");
                var default_priority = default_priority_input_element.val();
                var sanitized_default_priority = default_priority; 

                var incident_list_length_input_element = jquery("input[name=incident_list_length]");
                var incident_list_length = incident_list_length_input_element.val();
                var sanitized_incident_list_length = this.sanitize_string(incident_list_length);
                
                var collect_data_results_input_element = jquery("input[name=collect_data_results]");
                var collect_data_results = collect_data_results_input_element.prop('checked');
                var sanitized_collect_data_results = collect_data_results;                

                var index_data_results_input_element = jquery("input[name=index_data_results]");
                var index_data_results = index_data_results_input_element.prop('checked');
                var sanitized_index_data_results = index_data_results;
                
                var auto_close_info_input_element = jquery("input[name=auto_close_info]");
                var auto_close_info = auto_close_info_input_element.prop('checked');
                var sanitized_auto_close_info = auto_close_info;

                var auto_close_info_status_input_element = jquery("input[name=auto_close_info_status]");
                var auto_close_info_status = auto_close_info_status_input_element.val();
                var sanitized_auto_close_info_status = this.sanitize_string(auto_close_info_status);

                var param_impact_input_element = jquery("select[name=param_impact]");
                var param_impact = param_impact_input_element.val();
                var sanitized_param_impact = param_impact;

                var param_urgency_input_element = jquery("select[name=param_urgency]");
                var param_urgency = param_urgency_input_element.val();
                var sanitized_param_urgency = param_urgency;

                var error_messages_to_display = this.validate_inputs(
                    sanitized_idx,
                    sanitized_default_owner,
                    sanitized_incident_list_length,
                    sanitized_auto_close_info_status
                );

                var did_error_messages_occur = error_messages_to_display.length > 0;
                if (did_error_messages_occur) {
                    // Displays the errors that occurred input validation
                    this.display_error_output(error_messages_to_display);
                } else {
                    this.perform_setup(
                        splunk_js_sdk,
                        sanitized_idx,
                        sanitized_default_owner,
                        sanitized_default_priority,
                        sanitized_incident_list_length,
                        sanitized_collect_data_results,
                        sanitized_index_data_results,
                        sanitized_auto_close_info,
                        sanitized_auto_close_info_status,
                        sanitized_param_impact,
                        sanitized_param_urgency
                    );
                }
            },

            // This is where the main setup process occurs
            perform_setup: async function perform_setup(splunk_js_sdk, 
                    idx, 
                    default_owner,
                    default_priority,
                    incident_list_length,
                    collect_data_results,
                    index_data_results,
                    auto_close_info,
                    auto_close_info_status,
                    param_impact,
                    param_urgency) {
                var app_name = "alert_manager";

                var application_name_space = {
                    owner: "nobody",
                    app: app_name,
                    sharing: "app",
                };

                try {
                    // Create the Splunk JS SDK Service object
                    splunk_js_sdk_service = this.create_splunk_js_sdk_service(
                        splunk_js_sdk,
                        application_name_space,
                    );

                    // Creates the custom configuration files of this Splunk App
                    // All required information for this Splunk App is placed in
                    // there
                    await this.create_alert_manager_configuration_file(
                        splunk_js_sdk_service,
                        idx,
                        default_owner,
                        default_priority,
                        incident_list_length,
                        collect_data_results,
                        index_data_results,
                        auto_close_info,
                        auto_close_info_status
                    );

                    await this.create_alert_actions_configuration_file(
                        splunk_js_sdk_service,
                        param_impact,
                        param_urgency
                    );


                    // Completes the setup, by access the app.conf's [install]
                    // stanza and then setting the `is_configured` to true
                    await this.complete_setup(splunk_js_sdk_service);

                    // Reloads the splunk app so that splunk is aware of the
                    // updates made to the file system
                    await this.reload_splunk_app(splunk_js_sdk_service, app_name);

                    // Redirect to the Splunk App's home page
                    this.redirect_to_splunk_app_homepage(app_name);
                } catch (error) {
                    // This could be better error catching.
                    // Usually, error output that is ONLY relevant to the user
                    // should be displayed. This will return output that the
                    // user does not understand, causing them to be confused.
                    var error_messages_to_display = [];
                    if (
                        error !== null &&
                        typeof error === "object" &&
                        error.hasOwnProperty("responseText")
                    ) {
                        var response_object = JSON.parse(error.responseText);
                        error_messages_to_display = this.extract_error_messages(
                            response_object.messages,
                        );
                    } else {
                        // Assumed to be string
                        error_messages_to_display.push(error);
                    }

                    this.display_error_output(error_messages_to_display);
                }
            },

            create_alert_manager_configuration_file: async function create_alert_manager_configuration_file(
                splunk_js_sdk_service,
                idx,
                default_owner,
                default_priority,
                incident_list_length,
                collect_data_results,
                index_data_results,
                auto_close_info,
                auto_close_info_status
            ) {
                var custom_configuration_file_name = "alert_manager";
                var stanza_name = "settings";
                var properties_to_update = {
                    index: idx,
                    default_owner: default_owner,
                    default_priority: default_priority,
                    incident_list_length: incident_list_length,
                    collect_data_results: collect_data_results,
                    index_data_results: index_data_results,
                    auto_close_info: auto_close_info,
                    auto_close_info_status: auto_close_info_status,
                };

                await this.update_configuration_file(
                    splunk_js_sdk_service,
                    custom_configuration_file_name,
                    stanza_name,
                    properties_to_update,
                );
            },

            create_alert_actions_configuration_file: async function create_alert_actions_configuration_file(
                splunk_js_sdk_service,
                param_urgency,
                param_impact
            ) {
                var custom_configuration_file_name = "alert_actions";
                var stanza_name = "alert_manager";
                var properties_to_update = {
                    "param.impact": param_impact,
                    "param.urgency": param_urgency
                };

                await this.update_configuration_file(
                    splunk_js_sdk_service,
                    custom_configuration_file_name,
                    stanza_name,
                    properties_to_update,
                );
            },

            complete_setup: async function complete_setup(splunk_js_sdk_service) {
                var app_name = "alert_manager";
                var configuration_file_name = "app";
                var stanza_name = "install";
                var properties_to_update = {
                    is_configured: "true",
                };

                await this.update_configuration_file(
                    splunk_js_sdk_service,
                    configuration_file_name,
                    stanza_name,
                    properties_to_update,
                );
            },

            reload_splunk_app: async function reload_splunk_app(
                splunk_js_sdk_service,
                app_name,
            ) {
                var splunk_js_sdk_apps = splunk_js_sdk_service.apps();
                await splunk_js_sdk_apps.fetch();

                var current_app = splunk_js_sdk_apps.item(app_name);
                current_app.reload();
            },

            // ----------------------------------
            // Splunk JS SDK Helpers
            // ----------------------------------
            // ---------------------
            // Process Helpers
            // ---------------------

            init_properties: async function init_properties(
                splunk_js_sdk,
                application_name_space, 
                configuration_file_name,
                stanza_name,
                stanza_property,
                type,
                input_name,
                default_value              
            ) {
            
                service = this.create_splunk_js_sdk_service(
                        splunk_js_sdk,
                        application_name_space,
                );

                relpath = "properties/" + configuration_file_name + "/" + stanza_name
                
                
                var endpoint = new splunkjs.Service.Endpoint(service, relpath);
                endpoint.get(stanza_property, null, function(err, response){ 

                    if (typeof response != "undefined" && response.data!=""  ) {
                        if (type === 'input') {
                            jquery("input[name="+input_name+"]").val(response.data);
                        } else if (type==='select') {
                            jquery("select[name="+input_name+"]").val(response.data);
                        } else if (type === 'checkbox') {
                            checked = (response.data == 'true');
                            jquery("input[name="+input_name+"]").prop('checked',checked);
                        }


                    }
                    else {
                        console.log("Setting default_value", default_value);

                        if (type === 'input') {
                            jquery("input[name="+input_name+"]").val(default_value);
                        } else if (type==='select') {
                            jquery("select[name="+input_name+"]").val(default_value);
                        } else if (type === 'checkbox') {
                            jquery("input[name="+input_name+"]").prop('checked', default_value);
                        }
                    }

                })
            },
            
            update_configuration_file: async function update_configuration_file(
                splunk_js_sdk_service,
                configuration_file_name,
                stanza_name,
                properties,
            ) {
                // Retrieve the accessor used to get a configuration file
                var splunk_js_sdk_service_configurations = splunk_js_sdk_service.configurations(
                    {
                        // Name space information not provided
                    },
                );
                await splunk_js_sdk_service_configurations.fetch();

                // Check for the existence of the configuration file being edited
                var does_configuration_file_exist = this.does_configuration_file_exist(
                    splunk_js_sdk_service_configurations,
                    configuration_file_name,
                );

                // If the configuration file doesn't exist, create it
                if (!does_configuration_file_exist) {
                    await this.create_configuration_file(
                        splunk_js_sdk_service_configurations,
                        configuration_file_name,
                    );
                }

                // Retrieves the configuration file accessor
                var configuration_file_accessor = this.get_configuration_file(
                    splunk_js_sdk_service_configurations,
                    configuration_file_name,
                );
                await configuration_file_accessor.fetch();

                // Checks to see if the stanza where the inputs will be
                // stored exist
                var does_stanza_exist = this.does_stanza_exist(
                    configuration_file_accessor,
                    stanza_name,
                );

                // If the configuration stanza doesn't exist, create it
                if (!does_stanza_exist) {
                    await this.create_stanza(configuration_file_accessor, stanza_name);
                }
                // Need to update the information after the creation of the stanza
                await configuration_file_accessor.fetch();

                // Retrieves the configuration stanza accessor
                var configuration_stanza_accessor = this.get_configuration_file_stanza(
                    configuration_file_accessor,
                    stanza_name,
                );
                await configuration_stanza_accessor.fetch();

                // We don't care if the stanza property does or doesn't exist
                // This is because we can use the
                // configurationStanza.update() function to create and
                // change the information of a property
                await this.update_stanza_properties(
                    configuration_stanza_accessor,
                    properties,
                );
            },

            // ---------------------
            // Existence Functions
            // ---------------------
            does_configuration_file_exist: function does_configuration_file_exist(
                configurations_accessor,
                configuration_file_name,
            ) {
                var was_configuration_file_found = false;

                var configuration_files_found = configurations_accessor.list();
                for (var index = 0; index < configuration_files_found.length; index++) {
                    var configuration_file_name_found =
                        configuration_files_found[index].name;
                    if (configuration_file_name_found === configuration_file_name) {
                        was_configuration_file_found = true;
                    }
                }

                return was_configuration_file_found;
            },

            does_stanza_exist: function does_stanza_exist(
                configuration_file_accessor,
                stanza_name,
            ) {
                var was_stanza_found = false;

                var stanzas_found = configuration_file_accessor.list();
                for (var index = 0; index < stanzas_found.length; index++) {
                    var stanza_found = stanzas_found[index].name;
                    if (stanza_found === stanza_name) {
                        was_stanza_found = true;
                    }
                }

                return was_stanza_found;
            },

            does_stanza_property_exist: function does_stanza_property_exist(
                configuration_stanza_accessor,
                property_name,
            ) {
                var was_property_found = false;

                for (const [key, value] of Object.entries(
                    configuration_stanza_accessor.properties(),
                )) {
                    if (key === property_name) {
                        was_property_found = true;
                    }
                }

                return was_property_found;
            },

            // ---------------------
            // Retrieval Functions
            // ---------------------
            get_configuration_file: function get_configuration_file(
                configurations_accessor,
                configuration_file_name,
            ) {
                var configuration_file_accessor = configurations_accessor.item(
                    configuration_file_name,
                    {
                        // Name space information not provided
                    },
                );

                return configuration_file_accessor;
            },

            get_configuration_file_stanza: function get_configuration_file_stanza(
                configuration_file_accessor,
                configuration_stanza_name,
            ) {
                var configuration_stanza_accessor = configuration_file_accessor.item(
                    configuration_stanza_name,
                    {
                        // Name space information not provided
                    },
                );

                return configuration_stanza_accessor;
            },

            get_configuration_file_stanza_property: function get_configuration_file_stanza_property(
                configuration_file_accessor,
                configuration_file_name,
            ) {
                return null;
            },

            // ---------------------
            // Creation Functions
            // ---------------------
            create_splunk_js_sdk_service: function create_splunk_js_sdk_service(
                splunk_js_sdk,
                application_name_space,
            ) {
                var http = new splunk_js_sdk.SplunkWebHttp();

                var splunk_js_sdk_service = new splunk_js_sdk.Service(
                    http,
                    application_name_space,
                );

                return splunk_js_sdk_service;
            },

            create_configuration_file: function create_configuration_file(
                configurations_accessor,
                configuration_file_name,
            ) {
                var parent_context = this;

                return configurations_accessor.create(configuration_file_name, function(
                    error_response,
                    created_file,
                ) {
                    // Do nothing
                });
            },

            create_stanza: function create_stanza(
                configuration_file_accessor,
                new_stanza_name,
            ) {
                var parent_context = this;

                return configuration_file_accessor.create(new_stanza_name, function(
                    error_response,
                    created_stanza,
                ) {
                    // Do nothing
                });
            },

            update_stanza_properties: function update_stanza_properties(
                configuration_stanza_accessor,
                new_stanza_properties,
            ) {
                var parent_context = this;

                return configuration_stanza_accessor.update(
                    new_stanza_properties,
                    function(error_response, entity) {
                        // Do nothing
                    },
                );
            },


            // ----------------------------------
            // Input Cleaning and Checking
            // ----------------------------------
            sanitize_string: function sanitize_string(string_to_sanitize) {
                var sanitized_string = string_to_sanitize.trim();

                return sanitized_string;
            },

            validate_idx_input: function validate_idx_input(idx) {
                var error_messages = [];

                if (typeof idx === "" || idx === "") {
                    var is_string_empty = true; 
                }

                if (is_string_empty) {
                    error_message =
                        "The `index` specified was empty. Please provide" + " a value.";
                    error_messages.push(error_message);
                }

                return error_messages;
            },

            validate_default_owner_input: function validate_default_owner_input(default_owner) {
                var error_messages = [];

                if (typeof default_owner === "" || default_owner === "") {
                    var is_string_empty = true; 
                }
                
                if (is_string_empty) {
                    error_message =
                        "The `default_owner` specified was empty. Please provide" + " a value.";
                    error_messages.push(error_message);
                }

                return error_messages;
            },

            validate_default_priority_input: function validate_default_priority_input(default_priority) {
                var error_messages = [];

                var is_string_empty = typeof default_priority === "";

                if (is_string_empty) {
                    error_message =
                        "The `default_priority` specified was empty. Please provide" + " a value.";
                    error_messages.push(error_message);
                }

                return error_messages;
            },

            validate_incident_list_length_input: function validate_incident_list_length_input(incident_list_length) {
                var error_messages = [];

                if (typeof incident_list_length === "" || incident_list_length === "") {
                    var is_string_empty = true;
                }

                if (is_string_empty) {
                    error_message =
                        "The `incident_list_length` specified was empty. Please provide" + " a value.";
                    error_messages.push(error_message);
                }

                return error_messages;
            },

            validate_auto_close_info_status_input: function validate_auto_close_info_status_input(auto_close_info_status) {
                var error_messages = [];

                if (typeof auto_close_info_status === "" || auto_close_info_status === "") {
                    var is_string_empty = true; 
                }

                if (is_string_empty) {
                    error_message =
                        "The `auto_close_info_status` specified was empty. Please provide" + " a value.";
                    error_messages.push(error_message);
                }

                return error_messages;
            },
         
            validate_inputs: function validate_inputs(
                    idx,
                    default_owner,
                    incident_list_length,
                    auto_close_info_status) {
                var error_messages = [];

                var idx_errors = this.validate_idx_input(idx);
                var default_owner_errors = this.validate_default_owner_input(default_owner);
                var incident_list_length_errors = this.validate_incident_list_length_input(incident_list_length);
                var auto_close_info_status_errors = this.validate_auto_close_info_status_input(auto_close_info_status);

                error_messages = error_messages.concat(idx_errors);
                error_messages = error_messages.concat(default_owner_errors);
                error_messages = error_messages.concat(incident_list_length_errors);
                error_messages = error_messages.concat(auto_close_info_status_errors);

                return error_messages;
            },

            // ----------------------------------
            // GUI Helpers
            // ----------------------------------
            extract_error_messages: function extract_error_messages(error_messages) {
                // A helper function to extract error messages

                var error_messages_to_display = [];
                for (var index = 0; index < error_messages.length; index++) {
                    error_message = error_messages[index];
                    error_message_to_display =
                        error_message.type + ": " + error_message.text;
                    error_messages_to_display.push(error_message_to_display);
                }

                return error_messages_to_display;
            },

            redirect_to_splunk_app_homepage: function redirect_to_splunk_app_homepage(
                app_name,
            ) {
                var redirect_url = "/app/" + app_name;

                window.location.href = redirect_url;
            },

            // ----------------------------------
            // Display Functions
            // ----------------------------------
            display_error_output: function display_error_output(error_messages) {
                // Hides the element if no messages, shows if any messages exist
                var did_error_messages_occur = error_messages.length > 0;

                var error_output_element = jquery(".setup.container .error.output");

                if (did_error_messages_occur) {
                    var new_error_output_string = "";
                    new_error_output_string += "<ul>";
                    for (var index = 0; index < error_messages.length; index++) {
                        new_error_output_string +=
                            "<li>" + error_messages[index] + "</li>";
                    }
                    new_error_output_string += "</ul>";

                    error_output_element.html(new_error_output_string);
                    error_output_element.stop();
                    error_output_element.fadeIn();
                } else {
                    error_output_element.stop();
                    error_output_element.fadeOut({
                        complete: function() {
                            error_output_element.html("");
                        },
                    });
                }
            },

            get_template: function get_template() {
                template_string =
                    "<div class='title'>" +
                    "    <h1>Alert Manager Global Settings</h1>" +
                    "</div>" +
                    "<div class='setup container'>" +
                    "    <div class='left'>" +
                    "        <h2>Globals</h2>" +
                    "        <div class='field idx'>" +
                    "            <div class='title'>" +
                    "                <div>" +
                    "                    <h3>Index:</h3>" +
                    "                    Please specify the index to use." +
                    "                </div>" +
                    "            </div>" +
                    "            </br>" +
                    "            <div class='user_input'>" +
                    "                <div class='text'>" +
                    "                    <input type='text' name='idx'></input>" +
                    "                </div>" +
                    "            </div>" +     
                    "        </div>" +
                    "        <div class='field_default_owner'>" +
                    "            <div class='title'>" +
                    "                <h3>Default Owner:</h3>" +
                    "                Please specify the Default Owner." +
                    "            </div>" +
                    "            </br>" +
                    "            <div class='user_input'>" +
                    "                <div class='text'>" +
                    "                    <input type='text' name='default_owner'></input>" +
                    "                </div>" +
                    "            </div>" +
                    "        </div>" +
                    "        <div class='field_default_priority'>" +
                    "            <div class='title'>" +
                    "                <h3>Default Priority:</h3>" +
                    "                Please specify the Default Priority." +
                    "            </div>" +
                    "            </br>" +
                    "            <div class='user_input'>" +
                    "                <div class='text'>" +
                    "                   <select input id='default_priority' name='default_priority' selected='low'>" +
                    "                       <option value='informational'>Informational</option>" +
                    "                       <option value='low'>Low</option>" +
                    "                       <option value='medium'>Medium</option>" +
                    "                       <option value='high'>High</option>" +
                    "                       <option value='critical'>Critical</option>" +
                    "                   </select>" +
                    "                </div>" +
                    "            </div>" +
                    "        </div>" +                    
                    "        <div class='field_incident_list_length'>" +
                    "            <div class='title'>" +
                    "                <h3>Number of incidents show in incident posture:</h3>" +
                    "                Please specify how many incidents to show (rows)." +
                    "            </div>" +
                    "            </br>" +
                    "            <div class='user_input'>" +
                    "                <div class='text'>" +
                    "                    <input type='text' name='incident_list_length'></input>" +
                    "                </div>" +
                    "            </div>" +
                    "        </div>" + 
                    "        <div class='field_collect_data_results'>" +
                    "            <div class='title'>" +
                    "                <h3>Save incident results to KVStore:</h3>" +
                    "                Please specify if incident results should be stored to KVStore." +
                    "            </div>" +
                    "            </br>" +
                    "            <div class='user_input'>" +
                    "                <div class='checkbox'>" +
                    "                    <input type='checkbox' name='collect_data_results'></input>" +
                    "                </div>" +
                    "            </div>" +
                    "        </div>" +
                    "        <div class='field_index_data_results'>" +
                    "            <div class='title'>" +
                    "                <h3>Save incident results to Index:</h3>" +
                    "                Please specify if incident results should be indexed." +
                    "            </div>" +
                    "            </br>" +
                    "            <div class='user_input'>" +
                    "                <div class='checkbox'>" +
                    "                    <input type='checkbox' name='index_data_results'></input>" +
                    "                </div>" +
                    "            </div>" +
                    "        </div>" + 
                    "        <div class='field_auto_close_info'>" +
                    "            <div class='title'>" +
                    "                <h3>Automatically close informational events:</h3>" +
                    "                Please specify if informational events should be closed automatically." +
                    "            </div>" +
                    "            </br>" +
                    "            <div class='user_input'>" +
                    "                <div class='checkbox'>" +
                    "                    <input type='checkbox' name='auto_close_info'></input>" +
                    "                </div>" +
                    "            </div>" +
                    "        </div>" +
                    "        <div class='field_auto_close_info_status'>" +
                    "            <div class='title'>" +
                    "                <h3>Status to use for automatically closed informational events:</h3>" +
                    "                Please specify the status for automatically closed informational events." +
                    "            </div>" +
                    "            </br>" +
                    "            <div class='user_input'>" +
                    "                <div class='text'>" +
                    "                    <input type='text' name='auto_close_info_status'></input>" +
                    "                </div>" +
                    "            </div>" +
                    "        </div>" +
                    "        <h2>Alert Action Defaults</h2>" +
                    "        <div class='field_param_impact'>" +
                    "            <div class='title'>" +
                    "                <h3>Impact:</h3>" +
                    "                Default value for Alert Action Impact." +
                    "            </div>" +
                    "            </br>" +
                    "            <div class='user_input'>" +
                    "                <div class='text'>" +
                    "                   <select input id='param_impact' name='param_impact'>" +
                    "                       <option value='low'>Low</option>" +
                    "                       <option value='medium'>Medium</option>" +
                    "                       <option value='high'>High</option>" +
                    "                   </select>" +
                    "                </div>" +
                    "            </div>" +
                    "        </div>" +
                    "        <div class='field_param_urgency'>" +
                    "            <div class='title'>" +
                    "                <h3>Urgency:</h3>" +
                    "                Default value for Alert Action Urgency." +
                    "            </div>" +
                    "            </br>" +
                    "            <div class='user_input'>" +
                    "                <div class='text'>" +
                    "                   <select input id='param_urgency' name='param_urgency'>" +
                    "                       <option value='low'>Low</option>" +
                    "                       <option value='medium'>Medium</option>" +
                    "                       <option value='high'>High</option>" +
                    "                   </select>" +
                    "                </div>" +
                    "            </div>" +
                    "        </div>" +                    
                    "        <h2>Complete the Setup</h2>" +
                    "        <div>" +
                    "            Please press the 'Perform Setup` button below to complete the Splunk App setup." +
                    "        </div>" +
                    "        <br/>" +
                    "        <div>" +
                    "            <button name='setup_button' class='setup_button'>" +
                    "                Perform Setup" +
                    "            </button>" +
                    "        </div>" +
                    "        <br/>" +
                    "        <div class='error output'>" +
                    "        </div>" +
                    "    </div>" +  
                    "</div>";

                return template_string;
            },
        }); // End of GlobalSettingsView class declaration

        return GlobalSettingsView;
    }, // End of require asynchronous module definition function
); // End of require statement