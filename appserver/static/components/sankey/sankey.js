// AppFramework Sankey Plug-In
// ---------------------------
// 
// Provide an easy-to-use plug-in that takes data that relates a
// many-to-many relationship with scores into a Sankey display, a form
// of flow display.  Any relationship between two fields can be
// illustrated, although the most common is 
// "stats count by field1, field2"

define(function(require, exports, module) {
    var _ = require("underscore");
    var $ = require("jquery");
    var SimpleSplunkView = require("splunkjs/mvc/simplesplunkview");
    var d3 = require("../d3/d3");
    // Load D3 Sankey plugin
    require("./contrib/d3-sankey");

    // Import CSS for the sankey chart.
    require("css!./sankey.css");

    var SankeyChart = SimpleSplunkView.extend({
        moduleId: module.id,

        className: "sankey-diagram",

        options: {
            managerid: null,
            data: "preview",
            formatLabel: _.identity,
            height: 300,
            formatTooltip: function(d) {
                return (d.source.name + ' -> ' + d.target.name + ': ' + d.value);
            }
        },

        // This is how we extend the SimpleSplunkView's options value for
        // this object, so that these values are available when
        // SimpleSplunkView initializes.
        initialize: function() {
            SimpleSplunkView.prototype.initialize.apply(this, arguments);

            this.settings.on("change:formatLabel change:formatTooltip", this.render, this);


            // Set up resize callback. 
            $(window).resize(_.debounce(_.bind(this._handleResize, this), 20));
        },

        _handleResize: function() {
            this.render();
        },

        // The object this method returns will be passed to the
        // updateView() method as the first argument, to be
        // manipulated according to the data and the visualization's
        // needs.
        createView: function() {
            var margin = {top: 10, right: 10, bottom: 10, left: 10};
            var availableWidth = parseInt(this.settings.get("width") || this.$el.width());
            var availableHeight = parseInt(this.settings.get("height") || this.$el.height());

            this.$el.html("");

            var svg = d3.select(this.el)
                .append("svg")
                .attr("width", availableWidth)
                .attr("height", availableHeight)
                .attr("pointer-events", "all");

            return { svg: svg, margin: margin};
        },

        // Where the data and the visualization meet.  Both 'viz' and
        // 'data' are the data structures returned from their
        // respective construction methods, createView() above and
        // onData(), below.
        updateView: function(viz, data) {
            var that = this;
            var containerHeight = this.$el.height();
            var containerWidth = this.$el.width();

            // Clear svg
            var svg = $(viz.svg[0]);
            svg.empty();
            svg.height(containerHeight);
            svg.width(containerWidth);

            // Add the graph group as a child of the main svg
            var graphWidth = containerWidth - viz.margin.left - viz.margin.right;
            var graphHeight = containerHeight - viz.margin.top - viz.margin.bottom;
            var graph = viz.svg
                .append("g")
                .attr("width", graphWidth)
                .attr("height", graphHeight)
                .attr("transform", "translate(" + viz.margin.left + "," + viz.margin.top + ")");

            var formatLabel = this.settings.get('formatLabel') || _.identity;
            var formatTooltip = this.settings.get('formatTooltip');

            var sankey = d3.sankey()
                .nodeWidth(15)
                .nodePadding(10)
                .size([graphWidth, graphHeight]);

            var path = sankey.link();

            sankey.nodes(data.nodes)
                .links(data.links)
                .layout(1);

            var link = graph.append("g").selectAll(".link")
                .data(data.links)
                .enter().append("path")
                .attr("class", "link")
                .attr("d", path)
                .style("stroke-width", function(d) {
                    return Math.max(1, d.dy);
                })
                .sort(function(a, b) {
                    return b.dy - a.dy;
                });

            link.append("title")
                .text(function(d) {
                    return formatTooltip(d);
                });

            var node = graph.append("g").selectAll(".node")
                .data(data.nodes)
                .enter()
                .append("g")
                .attr("class", "node")
                .attr("transform", function(d) {
                    return "translate(" + d.x + "," + d.y + ")";
                });

            var color = d3.scale.category20();

            // Draw the rectangles at each end of the link that
            // correspond to a given node, and then decorate the chart
            // with the names for each node.
            node.append("rect")
                .attr("height", function(d) {
                    return d.dy;
                })
                .attr("width", sankey.nodeWidth())
                .style("fill", function(d) {
                    d.color = color(d.name.replace(/ .*/, ""));
                    return d.color;
                })
                .style("stroke", function(d) {
                    return d3.rgb(d.color).darker(2);
                })
                .on("mouseover", function(node) {
                    var linksToHighlight = link.filter(function(d) {
                        return d.source.name === node.name || d.target.name === node.name;
                    });
                    linksToHighlight.classed('hovering', true);
                })
                .on("mouseout", function(node) {
                    var linksToHighlight = link.filter(function(d) {
                        return d.source.name === node.name || d.target.name === node.name;
                    });
                    linksToHighlight.classed('hovering', false);
                })
                .append("title")
                .text(function(d) {
                    return formatLabel(d.name) + "\n" + d.value;
                });

            node.attr("transform", function(d) {
                return "translate(" + d.x + "," + d.y + ")";
            })
                .call(d3.behavior.drag()
                    .origin(function(d) {
                        return d;
                    })
                    .on("dragstart", function() {
                        this.parentNode.appendChild(this);
                    })
                    .on("drag", dragmove));

            node.append("text")
                .attr("x", -6)
                .attr("y", function(d) {
                    return d.dy / 2;
                })
                .attr("dy", ".35em")
                .attr("text-anchor", "end")
                .attr("transform", null)
                .text(function(d) {
                    return formatLabel(d.name);
                })
                .filter(function(d) {
                    return d.x < graphWidth / 2;
                })
                .attr("x", 6 + sankey.nodeWidth())
                .attr("text-anchor", "start");

            // This view publishes the 'click:link' event that
            // other Splunk views can then use to drill down
            // further into the data.  We return the source and target
            // names as values to be used in further Splunk searches.
            // This allows us to accept events from the visualization
            // library and provide them consistently to other Splunk
            // views.
            var format_event_data = function(e) {
                return {
                    source: e.source.name,
                    target: e.target.name,
                    value: e.value
                };
            };

            function dragmove(d) {
                d3.select(this).attr("transform", "translate(" + d.x + "," + (d.y = Math.max(0, Math.min(graphHeight - d.dy, d3.event.y))) + ")");
                sankey.relayout();
                link.attr("d", path);
            }

            link.on('click', function(e) {
                that.trigger('click:link', format_event_data(e));
            });

            node.on('mousedown', function(e) {
                var linksToNodes = function(links, type) {
                    return _.map(links, function(link) {
                        return {
                            name: link[type].name,
                            value: link[type].value
                        };
                    });
                };

                var clickEvent = {
                    name: e.name,
                    value: e.value,
                    incomingLinks: linksToNodes(e.targetLinks, "source"),
                    outgoingLinks: linksToNodes(e.sourceLinks, "target")
                };
                that.trigger('click:node', clickEvent);
            });
        },

        // This function turns the three expected data items into data
        // structures Sankey understands, and then calls
        // updateView().  This is the function that is called when
        // new data is available, and triggers the actual rendering of
        // the visualization above.  The data passed here corresponds
        // to the basic format requested by the view.
        formatData: function(data) {
            var nodeList = _.uniq(_.pluck(data, 0).concat(_.pluck(data, 1)));

            var links = _.map(data, function(item) {
                return {
                    source: nodeList.indexOf(item[0]),
                    target: nodeList.indexOf(item[1]),
                    value: parseInt(item[2], 10)
                };
            });

            var nodes = _.map(nodeList, function(node) {
                return {
                    name: node
                };
            });

            return { nodes: nodes, links: links };
        },
        render: function() {
            this.$el.height(this.settings.get('height'));
            return SimpleSplunkView.prototype.render.apply(this, arguments);
        }
    });

    return SankeyChart;
});
