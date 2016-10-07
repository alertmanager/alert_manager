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
        splunkUtil
    ) {

    // Tokens
    var submittedTokens = mvc.Components.getInstance('submitted', {create: true});
    var defaultTokens   = mvc.Components.getInstance('default', {create: true});

    var user_directories = ["both", "builtin", "alert_manager"];
    var active_user_directory_search = mvc.Components.getInstance('active_user_directory');
    var active_user_directory_data = active_user_directory_search.data("preview", { count: 1 });
    var active_user_directory = '';

    active_user_directory_data.on("data", function() {
        active_user_directory = active_user_directory_data.data()["rows"][0][0];

        if($("#user_directories").length == 0) {
            $("<select />").attr("id", "user_directories").appendTo($("#user_directories_container"));

            $.each(user_directories, function(key, val) {
                if (val == active_user_directory) {
                    $('#user_directories')
                        .append($("<option></option>")
                        .attr("value",val)
                        .attr("selected","selected")
                        .text(val)); 
                } else {
                    $('#user_directories')
                        .append($("<option></option>")
                        .attr("value",val)
                        .text(val)); 
                }
            });
        }
    });
    // Save active user directory
    $(document).on("click", "#save_user_directories", function(event){

        if($("#user_directories").val() == undefined) { return false; }


        var new_user_directory = $("#user_directories").val();
        console.debug("new_user_directory", new_user_directory);

        if(active_user_directory == new_user_directory) { return false; }

        var post_data = {
            user_directory    : new_user_directory
        };

        if(confirm("Are you sure to change the active user directory to '"+new_user_directory+"'?")) {
            var url = splunkUtil.make_url('/custom/alert_manager/user_settings/set_user_directory');
            $.ajax( url,
            {
                uri:  url,
                type: 'POST',
                data: post_data,
  
                success: function(jqXHR, textStatus){
                    // Reload the table
                    mvc.Components.get("active_user_directory").startSearch()
                    console.debug("success");
                },
                
                // Handle cases where the file could not be found or the user did not have permissions
                complete: function(jqXHR, textStatus){
                    console.debug("complete");
                },
                
                error: function(jqXHR,textStatus,errorThrown) {
                    console.log("Error");
                } 
            });
        } else {
            return false;
        }

    });

    // Save Settings
    $(document).on("click", "#save_settings", function(event){
        // save data here
        
        var data = $("#handson_container").data('handsontable').getData();
        console.debug("save data", data);

        // Remove empty lines
        var data = _.filter(data, function(entry){
            return entry['name'] != null || entry['email'] != null; 
        });

        // remove builtin-users
        var data = _.filter(data, function(entry){
            return entry['type'] != "builtin"
        });

        // validate data
        var check = _.filter(data, function(entry){ 
            return entry['name']== null || entry['email'] == null; 
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
'        <p>There is at least one row with missing data. Check user and email.</p>' +
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

            var url = splunkUtil.make_url('/custom/alert_manager/user_settings/save');
            console.debug("url", url);

            $.ajax( url,
                    {
                        uri:  url,
                        type: 'POST',
                        data: post_data,
                        
                       
                        success: function(jqXHR, textStatus){
                            // Reload the table
                            mvc.Components.get("user_settings_search").startSearch()
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