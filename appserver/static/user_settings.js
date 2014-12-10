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

    var UserTableRenderer = TableView.BaseCellRenderer.extend({
        canRender: function(cell) {
            return (cell.field==="email");
        },
        render: function($td, cell) {
            $td.html('<div>Bla: '+cell.value+'</div>');
        }        
    });

    mvc.Components.get('alert_user_list').getVisualization(function(tableView) {
        // Add custom cell renderer
        tableView.table.addCellRenderer(new UserTableRenderer());

        tableView.table.render();

    });
});