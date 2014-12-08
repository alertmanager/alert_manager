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

    var EditableTableRenderer = TableView.BaseCellRenderer.extend({
        canRender: function(cell) {
            return ( cell.field==="auto_assign_user" || cell.field==="auto_assign" || cell.field==="auto_ttl_resolve" || cell.field==="auto_previous_resolve");
        },
        render: function($td, cell) {
            if (cell.field == "auto_assign" || cell.field == "auto_ttl_resolve" || cell.field == "auto_previous_resolve") {
                if (cell.value=="1") {
                    var checked='checked="checked"';
                }  else {
                    var checked='';
                }
                
                $td.addClass('numeric').html(_.template('<input type="checkbox" name="<%- field %>" value="1" <%- checked %>></input>', {
                    field: cell.field,
                    text: cell.value,
                    checked: checked
                }));
            } else {
                $td.html(_.template('<input type="text" name="<%- field %>" value="<%- text %>"></input>', {
                    field: cell.field,
                    text: cell.value
                }));
            }
        }        
    });

    $('#alert_settings').prepend('<input type="button" value="Save Settings" id="save_settings" />');

    mvc.Components.get('alert_settings').getVisualization(function(tableView) {
        // Add custom cell renderer
        tableView.table.addCellRenderer(new EditableTableRenderer());

        tableView.table.render();

    });
});