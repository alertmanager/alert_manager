require([
    "splunkjs/mvc",
    "splunkjs/mvc/utils",
    "splunkjs/mvc/tokenutils",
    "underscore",
    "jquery",
    "splunkjs/mvc/simplexml",
    'splunkjs/mvc/tableview',
    'splunkjs/mvc/chartview',
    'splunkjs/mvc/searchmanager'   
], function(
        mvc,
        utils,
        TokenUtils,
        _,
        $,
        DashboardController,
        TableView,
        ChartView,
        SearchManager 
    ) {

    // Tokens
    var submittedTokens = mvc.Components.getInstance('submitted', {create: true});
    var defaultTokens   = mvc.Components.getInstance('default', {create: true});

    // Save Settings
    $(document).on("click", "#save_settings", function(event){
        // save data here
        console.debug("save data", $("#handson_container").data('handsontable').getData());
        //console.debug("string",  JSON.stringify($("#handson_container").data('handsontable').getData()));
        mvc.Components.get("alert_settings_search").startSearch()
        
    });
});