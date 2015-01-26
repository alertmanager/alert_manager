//
// LIBRARY REQUIREMENTS
//
require([
    "splunkjs/mvc",
    "splunkjs/mvc/utils",
    "splunkjs/mvc/tokenutils",
    "underscore",
    "jquery",
    "splunkjs/mvc/simplexml",
    "splunkjs/mvc/headerview",
    "splunkjs/mvc/footerview",
    "splunkjs/mvc/simplexml/dashboardview",
    "splunkjs/mvc/simplexml/dashboard/panelref",
    "splunkjs/mvc/simplexml/element/single",
    "splunkjs/mvc/simplexml/element/table",
    "splunkjs/mvc/simpleform/formutils",
    "splunkjs/mvc/simplexml/eventhandler",
    "splunkjs/mvc/simpleform/input/dropdown",
    "splunkjs/mvc/simpleform/input/multiselect",
    "splunkjs/mvc/simpleform/input/text",
    "splunkjs/mvc/simpleform/input/timerange",
    "splunkjs/mvc/simpleform/input/submit",
    "splunkjs/mvc/searchmanager",
    "splunkjs/mvc/postprocessmanager",
    "splunkjs/mvc/simplexml/urltokenmodel"
    ],
    function(
        mvc,
        utils,
        TokenUtils,
        _,
        $,
        DashboardController,
        HeaderView,
        FooterView,
        Dashboard,
        PanelRef,
        SingleElement,
        TableElement,
        FormUtils,
        EventHandler,
        DropdownInput,
        MultiSelectInput,
        TextInput,
        TimeRangeInput,
        SubmitButton,
        SearchManager,
        PostProcessManager,
        UrlTokenModel
        ) {



        var pageLoading = true;


        // 
        // TOKENS
        //
        
        // Create token namespaces
        var urlTokenModel = new UrlTokenModel();
        mvc.Components.registerInstance('url', urlTokenModel);
        var defaultTokenModel = mvc.Components.getInstance('default', {create: true});
        var submittedTokenModel = mvc.Components.getInstance('submitted', {create: true});

        urlTokenModel.on('url:navigate', function() {
            defaultTokenModel.set(urlTokenModel.toJSON());
            if (!_.isEmpty(urlTokenModel.toJSON()) && !_.all(urlTokenModel.toJSON(), _.isUndefined)) {
                submitTokens();
            } else {
                submittedTokenModel.clear();
            }
        });

        // Initialize tokens
        defaultTokenModel.set(urlTokenModel.toJSON());

        function submitTokens() {
            // Copy the contents of the defaultTokenModel to the submittedTokenModel and urlTokenModel
            FormUtils.submitForm({ replaceState: pageLoading });
        }

        function setToken(name, value) {
            defaultTokenModel.set(name, value);
            submittedTokenModel.set(name, value);
        }

        function unsetToken(name) {
            defaultTokenModel.unset(name);
            submittedTokenModel.unset(name);
        }

        
        
        //
        // SEARCH MANAGERS
        //

        var base_single_search = new SearchManager({
            "id": "base_single_search",
            "status_buckets": 0,
            "earliest_time": "$global_time.earliest$",
            "search": "| `all_alerts_single_trend(\"$global_time.earliest$\",\"$global_time.latest$\")` | eval is_now=1 | append [| `all_alerts_single_trend(\"-48h\",\"-24h\")` | eval is_trend=1 ]",
            "latest_time": "$global_time.latest$",
            "cancelOnUnload": true,
            "app": utils.getCurrentApp(),
            "auto_cancel": 90,
            "preview": true,
            "runWhenTimeIsUndefined": false
        }, {tokens: true, tokenNamespace: "submitted"});

        var search_informational = new PostProcessManager({
            "search": "search urgency=\"informational\" | stats count(is_now) AS count, count(is_trend) AS trend_count | eval trend=count-trend_count",
            "managerid": "base_single_search",
            "id": "search_informational"
        }, {tokens: true, tokenNamespace: "submitted"});

        var search_low = new PostProcessManager({
            "search": "search urgency=\"low\" | stats count(is_now) AS count, count(is_trend) AS trend_count | eval trend=count-trend_count",
            "managerid": "base_single_search",
            "id": "search_low"
        }, {tokens: true, tokenNamespace: "submitted"});

        var search_medium = new PostProcessManager({
            "search": "search urgency=\"medium\" | stats count(is_now) AS count, count(is_trend) AS trend_count | eval trend=count-trend_count",
            "managerid": "base_single_search",
            "id": "search_medium"
        }, {tokens: true, tokenNamespace: "submitted"});

        var search_high = new PostProcessManager({
            "search": "search urgency=\"high\"| stats count(is_now) AS count, count(is_trend) AS trend_count | eval trend=count-trend_count",
            "managerid": "base_single_search",
            "id": "search_high"
        }, {tokens: true, tokenNamespace: "submitted"});

        var search_critical = new PostProcessManager({
            "search": "search urgency=\"critical\"| stats count(is_now) AS count, count(is_trend) AS trend_count | eval trend=count-trend_count",
            "managerid": "base_single_search",
            "id": "search_critical"
        }, {tokens: true, tokenNamespace: "submitted"});

        var recent_alerts = new SearchManager({
            "id": "recent_alerts",
            "status_buckets": 0,
            "earliest_time": "$global_time.earliest$",
            "search": "| `all_alerts`| search owner=\"$owner$\" alert=\"$alert$\" category=\"$category$\" subcategory=\"$subcategory$\" job_id=\"$job_id$\" $tags$ $severity$ $priority$ $urgency$ $status$ |table dosearch, doedit, _time, owner, status, status_description, job_id, result_id, alert, app, category, subcategory, tags, severity, priority, urgency, search, event_search, earliest, latest, alert_time",
            "latest_time": "$global_time.latest$",
            "cancelOnUnload": true,
            "app": utils.getCurrentApp(),
            "auto_cancel": 90,
            "preview": true,
            "runWhenTimeIsUndefined": false
        }, {tokens: true, tokenNamespace: "submitted"});

        var search_alert_details = new SearchManager({
            "id": "search_alert_details",
            "status_buckets": 0,
            "earliest_time": "$global_time.earliest$",
            "search": "|loadjob $drilldown_job_id$",
            "latest_time": "$global_time.latest$",
            "cancelOnUnload": true,
            "app": utils.getCurrentApp(),
            "auto_cancel": 90,
            "preview": true,
            "runWhenTimeIsUndefined": false
        }, {tokens: true, tokenNamespace: "submitted"});

        var search_input_owner = new SearchManager({
            "id": "search_input_owner",
            "status_buckets": 0,
            "earliest_time": "-1m",
            "search": "|inputlookup incidents |dedup owner |table owner |sort owner",
            "latest_time": "now",
            "cancelOnUnload": true,
            "app": utils.getCurrentApp(),
            "auto_cancel": 90,
            "preview": true,
            "runWhenTimeIsUndefined": false
        }, {tokens: true});

        var search_input_alert = new SearchManager({
            "id": "search_input_alert",
            "status_buckets": 0,
            "earliest_time": "-1m",
            "search": "|inputlookup alert_settings |dedup alert |table alert |sort alert",
            "latest_time": "now",
            "cancelOnUnload": true,
            "app": utils.getCurrentApp(),
            "auto_cancel": 90,
            "preview": true,
            "runWhenTimeIsUndefined": false
        }, {tokens: true});

        var search_input_category = new SearchManager({
            "id": "search_input_category",
            "status_buckets": 0,
            "earliest_time": "-1m",
            "search": "|inputlookup alert_settings |dedup category |table category |sort category",
            "latest_time": "now",
            "cancelOnUnload": true,
            "app": utils.getCurrentApp(),
            "auto_cancel": 90,
            "preview": true,
            "runWhenTimeIsUndefined": false
        }, {tokens: true});

        var search_input_subcategory = new SearchManager({
            "id": "search_input_subcategory",
            "status_buckets": 0,
            "earliest_time": "-1m",
            "search": "|inputlookup alert_settings |dedup subcategory |table subcategory |sort subcategory",
            "latest_time": "now",
            "cancelOnUnload": true,
            "app": utils.getCurrentApp(),
            "auto_cancel": 90,
            "preview": true,
            "runWhenTimeIsUndefined": false
        }, {tokens: true});

        var search_input_tags = new SearchManager({
            "id": "search_input_tags",
            "status_buckets": 0,
            "earliest_time": "-1m",
            "search": "|inputlookup alert_settings | makemv delim=\" \" tags | mvexpand tags | dedup tags | table tags | sort tags",
            "latest_time": "now",
            "cancelOnUnload": true,
            "app": utils.getCurrentApp(),
            "auto_cancel": 90,
            "preview": true,
            "runWhenTimeIsUndefined": false
        }, {tokens: true});

        var search_input_urgency = new SearchManager({
            "id": "search_input_urgency",
            "status_buckets": 0,
            "earliest_time": "-1m",
            "search": "|inputlookup alert_urgencies | dedup urgency | table urgency",
            "latest_time": "now",
            "cancelOnUnload": true,
            "app": utils.getCurrentApp(),
            "auto_cancel": 90,
            "preview": true,
            "runWhenTimeIsUndefined": false
        }, {tokens: true});

        var search_input_status = new SearchManager({
            "id": "search_input_status",
            "status_buckets": 0,
            "earliest_time": "0",
            "search": "| inputlookup alert_status | eval filter_value=\"status=\\\"\"+status+\"\\\"\"",
            "latest_time": "$latest$",
            "cancelOnUnload": true,
            "app": utils.getCurrentApp(),
            "auto_cancel": 90,
            "preview": true,
            "runWhenTimeIsUndefined": false
        }, {tokens: true});

        var search_input_priority = new SearchManager({
            "id": "search_input_priority",
            "status_buckets": 0,
            "earliest_time": "-1m",
            "search": "|inputlookup alert_urgencies | dedup priority | table priority",
            "latest_time": "now",
            "cancelOnUnload": true,
            "app": utils.getCurrentApp(),
            "auto_cancel": 90,
            "preview": true,
            "runWhenTimeIsUndefined": false
        }, {tokens: true});

        var search_input_severity = new SearchManager({
            "id": "search_input_severity",
            "status_buckets": 0,
            "earliest_time": "-1m",
            "search": "|inputlookup alert_severities",
            "latest_time": "now",
            "cancelOnUnload": true,
            "app": utils.getCurrentApp(),
            "auto_cancel": 90,
            "preview": true,
            "runWhenTimeIsUndefined": false
        }, {tokens: true});



        //
        // SPLUNK HEADER AND FOOTER
        //

        new HeaderView({
            id: 'header',
            section: 'dashboards',
            el: $('.header'),
            acceleratedAppNav: true,
            useSessionStorageCache: true,
            splunkbar: true,
            appbar: true,
            litebar: false,
        }, {tokens: true}).render();

        new FooterView({
            id: 'footer',
            el: $('.footer')
        }, {tokens: true}).render();


        //
        // VIEWS: VISUALIZATION ELEMENTS
        //

        var sv_info = new SingleElement({
            "id": "sv_info",
            "field": "count",
            "drilldown": "none",
            "trendField": "trend",
            "managerid": "search_informational",
            "el": $('#sv_info')
        }, {tokens: true, tokenNamespace: "submitted"}).render();
        
        var sv_low = new SingleElement({
            "id": "sv_low",
            "field": "count",
            "drilldown": "none",
            "trendField": "trend",
            "managerid": "search_low",
            "el": $('#sv_low')
        }, {tokens: true, tokenNamespace: "submitted"}).render();
        
        var sv_medium = new SingleElement({
            "id": "sv_medium",
            "field": "count",
            "drilldown": "none",
            "trendField": "trend",
            "managerid": "search_medium",
            "el": $('#sv_medium')
        }, {tokens: true, tokenNamespace: "submitted"}).render();
        
        var sv_high = new SingleElement({
            "id": "sv_high",
            "field": "count",
            "drilldown": "none",
            "trendField": "trend",
            "managerid": "search_high",
            "el": $('#sv_high')
        }, {tokens: true, tokenNamespace: "submitted"}).render();
        
        var sv_critical = new SingleElement({
            "id": "sv_critical",
            "field": "count",
            "drilldown": "none",
            "trendField": "trend",
            "managerid": "search_critical",
            "el": $('#sv_critical')
        }, {tokens: true, tokenNamespace: "submitted"}).render();
        
        var alert_overview = new TableElement({
            "id": "alert_overview",
            "count": 10,
            "dataOverlayMode": "none",
            "drilldown": "row",
            "refresh.auto.interval": "300",
            "rowNumbers": "false",
            "wrap": "true",
            "managerid": "recent_alerts",
            "el": $('#alert_overview')
        }, {tokens: true, tokenNamespace: "submitted"}).render();

        alert_overview.on("click", function(e) {
            if (e.field !== undefined) {
                e.preventDefault();
                setToken("drilldown_job_id", TokenUtils.replaceTokenNames("$row.job_id$", _.extend(submittedTokenModel.toJSON(), e.data)));
            }
        });
        
        var alert_details = new TableElement({
            "id": "alert_details",
            "tokenDependencies": {"depends": "$drilldown_job_id$"},
            "count": 20,
            "dataOverlayMode": "none",
            "drilldown": "cell",
            "rowNumbers": "false",
            "wrap": "true",
            "managerid": "search_alert_details",
            "el": $('#alert_details')
        }, {tokens: true, tokenNamespace: "submitted"}).render();
        


        //
        // VIEWS: FORM INPUTS
        //
        var input_timerange = new TimeRangeInput({
            "id": "input_timerange",
            "default": {"latest_time": "now", "earliest_time": "-24h"},
            "searchWhenChanged": true,
            "earliest_time": "$form.global_time.earliest$",
            "latest_time": "$form.global_time.latest$",
            "el": $('#input_timerange')
        }, {tokens: true}).render();

        input_timerange.on("change", function(newValue) {
            FormUtils.handleValueChange(input_timerange);
        });

    
        var input_owner = new DropdownInput({
            "id": "input_owner",
            "choices": [
                {"value": "*", "label": "All"}
            ],
            "default": "*",
            "searchWhenChanged": true,
            "valueField": "owner",
            "labelField": "owner",
            "showClearButton": true,
            "selectFirstChoice": false,
            "value": "$form.owner$",
            "managerid": "search_input_owner",
            "el": $('#input_owner')
        }, {tokens: true}).render();

        input_owner.on("change", function(newValue) {
            FormUtils.handleValueChange(input_owner);
        });

    
        var input_alert = new DropdownInput({
            "id": "input_alert",
            "choices": [
                {"value": "*", "label": "All"}
            ],
            "default": "*",
            "valueField": "alert",
            "searchWhenChanged": true,
            "seed": "*",
            "labelField": "alert",
            "showClearButton": true,
            "selectFirstChoice": false,
            "value": "$form.alert$",
            "managerid": "search_input_alert",
            "el": $('#input_alert')
        }, {tokens: true}).render();

        input_alert.on("change", function(newValue) {
            FormUtils.handleValueChange(input_alert);
        });

    
        var input_category = new DropdownInput({
            "id": "input_category",
            "choices": [
                {"value": "*", "label": "All"}
            ],
            "default": "*",
            "valueField": "category",
            "searchWhenChanged": true,
            "seed": "*",
            "labelField": "category",
            "showClearButton": true,
            "selectFirstChoice": false,
            "value": "$form.category$",
            "managerid": "search_input_category",
            "el": $('#input_category')
        }, {tokens: true}).render();

        input_category.on("change", function(newValue) {
            FormUtils.handleValueChange(input_category);
        });

    
        var input_subcategory = new DropdownInput({
            "id": "input_subcategory",
            "choices": [
                {"value": "*", "label": "All"}
            ],
            "default": "*",
            "valueField": "subcategory",
            "searchWhenChanged": true,
            "seed": "*",
            "labelField": "subcategory",
            "showClearButton": true,
            "selectFirstChoice": false,
            "value": "$form.subcategory$",
            "managerid": "search_input_subcategory",
            "el": $('#input_subcategory')
        }, {tokens: true}).render();

        input_subcategory.on("change", function(newValue) {
            FormUtils.handleValueChange(input_subcategory);
        });

    
        var input_tags = new MultiSelectInput({
            "id": "input_tags",
            "choices": [
                {"value": "*", "label": "All"}
            ],
            "default": ["*", "[Untagged]"],
            "delimiter": " OR ",
            "valueSuffix": "\"",
            "valuePrefix": "tags=\"",
            "valueField": "tags",
            "searchWhenChanged": true,
            "seed": "*",
            "labelField": "tags",
            "value": "$form.tags$",
            "managerid": "search_input_tags",
            "el": $('#input_tags')
        }, {tokens: true}).render();

        input_tags.on("change", function(newValue) {
            FormUtils.handleValueChange(input_tags);
        });

    
        var input_urgency = new MultiSelectInput({
            "id": "input_urgency",
            "choices": [
                {"value": "*", "label": "All"}
            ],
            "default": ["*"],
            "delimiter": " OR ",
            "valueSuffix": "\"",
            "valuePrefix": "urgency=\"",
            "valueField": "urgency",
            "searchWhenChanged": true,
            "seed": "*",
            "labelField": "urgency",
            "value": "$form.urgency$",
            "managerid": "search_input_urgency",
            "el": $('#input_urgency')
        }, {tokens: true}).render();

        input_urgency.on("change", function(newValue) {
            FormUtils.handleValueChange(input_urgency);
        });

    
        var input_status = new MultiSelectInput({
            "id": "input_status",
            "choices": [
                {"value": "status=\"*\"", "label": "All"},
                {"value": "status!=\"*resolved\"", "label": "All open"},
                {"value": "status=\"*resolved\"", "label": "All resolved"}
            ],
            "default": ["status!=\"*resolved\""],
            "searchWhenChanged": true,
            "delimiter": " OR ",
            "valueField": "filter_value",
            "labelField": "status_description",
            "value": "$form.status$",
            "managerid": "search_input_status",
            "el": $('#input_status')
        }, {tokens: true}).render();

        input_status.on("change", function(newValue) {
            FormUtils.handleValueChange(input_status);
        });

    
        var input_priority = new MultiSelectInput({
            "id": "input_priority",
            "choices": [
                {"value": "*", "label": "All"}
            ],
            "default": ["*"],
            "delimiter": " OR ",
            "valueSuffix": "\"",
            "valuePrefix": "priority=\"",
            "valueField": "priority",
            "searchWhenChanged": true,
            "seed": "*",
            "labelField": "priority",
            "value": "$form.priority$",
            "managerid": "search_input_priority",
            "el": $('#input_priority')
        }, {tokens: true}).render();

        input_priority.on("change", function(newValue) {
            FormUtils.handleValueChange(input_priority);
        });

    
        var input_severity = new MultiSelectInput({
            "id": "input_severity",
            "choices": [
                {"value": "*", "label": "All"}
            ],
            "default": ["*"],
            "delimiter": " OR ",
            "valueSuffix": "\"",
            "valuePrefix": "severity=\"",
            "valueField": "severity",
            "searchWhenChanged": true,
            "seed": "*",
            "labelField": "severity",
            "value": "$form.severity$",
            "managerid": "search_input_severity",
            "el": $('#input_severity')
        }, {tokens: true}).render();

        input_severity.on("change", function(newValue) {
            FormUtils.handleValueChange(input_severity);
        });

    
        var input_job_id = new TextInput({
            "id": "input_job_id",
            "default": "*",
            "searchWhenChanged": true,
            "value": "$form.job_id$",
            "el": $('#input_job_id')
        }, {tokens: true}).render();

        input_job_id.on("change", function(newValue) {
            FormUtils.handleValueChange(input_job_id);
        });

    


        // 
        // SUBMIT FORM DATA
        //

        var submit = new SubmitButton({
            id: 'submit',
            el: $('#search_btn')
        }, {tokens: true}).render();

        submit.on("submit", function() {
            submitTokens();
        });

        // Initialize time tokens to default
        if (!defaultTokenModel.has('earliest') && !defaultTokenModel.has('latest')) {
            defaultTokenModel.set({ earliest: '0', latest: '' });
        }

        submitTokens();


        //
        // DASHBOARD READY
        //

        DashboardController.ready();
        pageLoading = false;

        $('body').removeClass('preload');

    }
);
