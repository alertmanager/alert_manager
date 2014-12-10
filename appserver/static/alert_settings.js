require([
    "splunkjs/mvc",
    "splunkjs/mvc/utils",
    "splunkjs/mvc/tokenutils",
    "underscore",
    "jquery",
    "splunkjs/mvc/simplexml",
    'splunkjs/mvc/tableview',
    'splunkjs/mvc/chartview',
    'splunkjs/mvc/searchmanager',
    'splunk.util',
    'splunk.messenger',
], function(
        mvc,
        utils,
        TokenUtils,
        _,
        $,
        DashboardController,
        TableView,
        ChartView,
        SearchManager,
        splunkUtil,
        Messenger
    ) {

    // Tokens
    var submittedTokens = mvc.Components.getInstance('submitted', {create: true});
    var defaultTokens   = mvc.Components.getInstance('default', {create: true});

    // Save Settings
    $(document).on("click", "#save_settings", function(event){
        // save data here
        
        var data = $("#handson_container").data('handsontable').getData();
        console.debug("save data", data);

        data = JSON.stringify(data);
        var post_data = {
            contents    : data
        };

        //var url = 'http://splunk.local/en-GB/custom/alert_manager/alert_settings/save';
        var url = splunkUtil.make_url('/custom/alert_manager/alert_settings/save');
        console.debug("url", url);
        $.ajax( url,
                {
                    uri:  url,
                    type: 'POST',
                    data: post_data,
                    
                   
                    success: function(jqXHR, textStatus){
                        // Reload the table
                        mvc.Components.get("alert_settings_search").startSearch()
                        console.debug("success");
                    },
                    
                    // Handle cases where the file could not be found or the user did not have permissions
                    complete: function(jqXHR, textStatus){
                        console.debug("complete");
                    },
                    
                    error: function(jqXHR,textStatus,errorThrown) {
                        console.log("Error");
                    } 
                }
        );
         
        
    });
});