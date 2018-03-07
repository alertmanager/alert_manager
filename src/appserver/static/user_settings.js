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

        if(confirm("Are you sure to change the active user directory to '"+new_user_directory+"'?")) {

            var rest_url = splunkUtil.make_url('/splunkd/__raw/services/user_settings');
            var post_data = {
                action         : 'set_user_directory',
                user_directory : new_user_directory,
            };
  	        $.post( rest_url, post_data, function(data, status) {
                mvc.Components.get("active_user_directory").startSearch()
            }, "text");

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

            user_data = JSON.stringify(data);

            var rest_url = splunkUtil.make_url('/splunkd/__raw/services/user_settings');
            var post_data = {
                action    : 'save_users',
                user_data : user_data,
            };
  	        $.post( rest_url, post_data, function(data, status) {
                mvc.Components.get("user_settings_search").startSearch()
            }, "text");
            
         }

    });
});
