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

        // Remove empty rows
        var data = _.filter(data, function(entry){ 
            return entry['alert'] != null || entry['category'] != null || entry['subcategory'] != null || entry['tags'] != null || entry['display_fields'] != null || entry['notification_scheme'] != null;
        });

        // validate data
        var check = _.filter(data, function(entry){ 
            return entry['alert'] == null; 
        });
        console.debug("check", check);
        if (check.length>0) {
            var modal = ''+
'<div class="modal fade" id="validation_failed">' +
'  <div class="modal-dialog model-sm">' +
'    <div class="modal-content">' +
'      <div class="modal-header">' +
'        <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>' +
'        <h4 class="modal-title">Validation failed</h4>' +
'      </div>' +
'      <div class="modal-body">' +
'        <p>There is at least one row with missing data. Check alert and auto_assign_owner (when auto_assign is activated) amd alert_script (when run_alert_script is activated).</p>' +
'      </div>' +
'      <div class="modal-footer">' +
'        <button type="button" class="btn btn-primary" data-dismiss="modal">OK</button>' +
'      </div>' +
'    </div>' +
'  </div>' +
'</div>';
            $('body').prepend(modal);
            $('#validation_failed').modal('show');
        } else {

            data = JSON.stringify(data);
            var post_data = {
                contents    : data
            };

            //var url = 'http://splunk.local/en-GB/custom/alert_manager/incident_settings/save';
            var url = splunkUtil.make_url('/custom/alert_manager/incident_settings/save');
            console.debug("post_data", post_data);

            $.ajax( url,
                    {
                        uri:  url,
                        type: 'POST',
                        data: post_data,
                        
                       
                        success: function(jqXHR, textStatus){
                            // Reload the table
                            mvc.Components.get("incident_settings_search").startSearch()
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
         }
        
    });
});
