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
    'select2/select2'
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
        Select
    ) {

    // Tokens
    var submittedTokens = mvc.Components.getInstance('submitted', {create: true});
    var defaultTokens   = mvc.Components.getInstance('default', {create: true});

    // Save templates
    $(document).on("click", "#save_templates", function(event){
        // save data here

        var data = $("#handson_container_templates").data('handsontable').getData();
        console.debug("save template data", data);

        // Remove empty lines
        var data = _.filter(data, function(entry){
            return entry['template_name'] != null || entry['template_file'] != null || entry['content_type'] != null || entry['subject'] != null || entry['attachments'] != null;
        });

        // validate data
        var check = _.filter(data, function(entry){
            return entry['template_name']== null || entry['template_file'] == true || entry['content_type'] == null || entry['subject'] == null;
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
'        <p>There is at least one row with missing data.</p>' +
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

            var rest_url = splunkUtil.make_url('/splunkd/__raw/services/alert_manager/email_templates');
            var post_data = {
                action        : 'update_email_templates',
                template_data : data,
            };
  	        $.post( rest_url, post_data, function(data, status) {
                mvc.Components.get("email_templates_search").startSearch()
            }, "text");


         }

    });

});
