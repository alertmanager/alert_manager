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

    //Closer
    var alert_details="#alert_details"; 
    var closer='<div class="closer icon-x"> close</div>';
    $(alert_details).prepend(closer);
  
    $(alert_details).on("click", '.closer', function() {
      // console.log ( $(alert_details).parent().parent().parent() );
        $(alert_details).parent().parent().parent().hide();
      // $(my_element_id).parent().parent().parent().width("100%");
    });  
    //$(my_element_id).parent().parent().parent().addClass("fix_panel");
    $(alert_details).parent().parent().parent().addClass("float_panel");


    var SearchIconRenderer = TableView.BaseCellRenderer.extend({
        canRender: function(cell) {
            // Only use the cell renderer for the specific field
            return cell.field === 'dosearch';
        },
        render: function($td, cell) {
    
            var icon = 'search';
            
            var rendercontent='<div style="float:left; max-height:22px; margin:0px;"><i class="icon-<%-icon%>" >&nbsp;</i></div>';
                
            $td.addClass('search_icon').html(_.template(rendercontent, {
                    icon: icon
                }));
        }
    });

    var DrillDownRenderer = TableView.BaseCellRenderer.extend({
        canRender: function(cell) {
            // Only use the cell renderer for the specific field
            return (cell.field==="sid" || cell.field==="search" || cell.field==="earliest" || cell.field==="latest");
        },
        render: function($td, cell) {
            // ADD class to cell -> CSS
            $td.addClass(cell.field).html(cell.value);
        }
    });

     // Row Coloring Example with custom, client-side range interpretation
    var CustomRangeRenderer = TableView.BaseCellRenderer.extend({
        canRender: function(cell) {
            // Enable this custom cell renderer for both the active_hist_searches and the active_realtime_searches field
            return _(['severity_name']).contains(cell.field);
        },
        render: function($td, cell) {
            // Add a class to the cell based on the returned value
            var value = cell.value;
            // Apply interpretation for number of historical searches
            if (cell.field === 'severity_name') {
                if (value == "info") {
                    $td.addClass('range-cell').addClass('range-info');
                }
                else if (value == "Low") {
                    $td.addClass('range-cell').addClass('range-elevated');
                }
                else if (value == "Medium") {
                    $td.addClass('range-cell').addClass('range-medium');
                }
                else if (value == "High") {
                    $td.addClass('range-cell').addClass('range-high');
                }
                else if (value == "Critical") {
                    $td.addClass('range-cell').addClass('range-critical');
                }
                else if (value == "Fatal") {
                    $td.addClass('range-cell').addClass('range-fatal');
                }
            }

            // Update the cell content
            //$td.text(value.toFixed(2)).addClass('numeric');
            $td.text(value);
        }
    });


    var EventSearchBasedRowExpansionRenderer = TableView.BaseRowExpansionRenderer.extend({
        initialize: function(args) {
            // initialize will run once, so we will set up a search and a chart to be reused.
            this._searchManager = new SearchManager({
                id: 'details-search-manager',
                preview: false
            });
            this._chartView = new ChartView({
                managerid: 'details-search-manager',
                'charting.legend.placement': 'none'
            });
        },
        canRender: function(rowData) {
            // Since more than one row expansion renderer can be registered we let each decide if they can handle that
            // data
            // Here we will always handle it.
            return true;
        },
        render: function($container, rowData) {
            // rowData contains information about the row that is expanded.  We can see the cells, fields, and values
            // We will find the sourcetype cell to use its value
            var alertCell = _(rowData.cells).find(function (cell) {
               return cell.field === 'alert';
            });
            //update the search with the sourcetype that we are interested in
            this._searchManager.set({ search: 'eventtype=alert_metadata ' + alertCell.value + ' | timechart count'});
            // $container is the jquery object where we can put out content.
            // In this case we will render our chart and add it to the $container
            //$container.append(this._chartView.render().el);
            $container.append("<div>Assign to: <br />Change priority to: <br />Change status to:</div>");
        }
    });

    mvc.Components.get('alert_overview').getVisualization(function(tableView) {
        // Add custom cell renderer
        tableView.table.addCellRenderer(new CustomRangeRenderer());
        tableView.table.addCellRenderer(new DrillDownRenderer());
        tableView.table.addCellRenderer(new SearchIconRenderer());
        tableView.addRowExpansionRenderer(new EventSearchBasedRowExpansionRenderer());

        tableView.table.render();

    });



     $(document).on("click", "td", function(e) {
        
        // Displays a data object in the console
        e.preventDefault();
        // console.dir($(this));

        if ($(this).context.cellIndex!=1) {
            drilldown_sid=($(this).parent().find("td.sid")[0].innerHTML);
            submittedTokens.set("drilldown_sid", drilldown_sid);
            $(alert_details).parent().parent().parent().show();

        }
        if ($(this).context.cellIndex==1){

            var drilldown_search=($(this).parent().find("td.search")[0].innerHTML);
            var drilldown_search_earliest=($(this).parent().find("td.earliest")[0].innerHTML);
            var drilldown_search_latest=($(this).parent().find("td.latest")[0].innerHTML);

            var search_url="search?q=search "+drilldown_search+"&earliest="+drilldown_search_earliest+"&latest="+drilldown_search_latest;

            window.open(search_url,'_search');

        }
    });
});