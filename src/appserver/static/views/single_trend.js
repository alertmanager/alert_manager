define(function(require) {
    var _ = require('underscore');
    var mvc = require('splunkjs/mvc');
    var SimpleSplunkView = require('splunkjs/mvc/simplesplunkview');
    
    var TrendIndicator = SimpleSplunkView.extend({
        // Override fetch settings
        outputMode: 'json',
        returnCount: 2,
        // Default options
        options: {
            
        },
        // Template for trend indicator
        template: _.template(
               // '<div class="single-trend <%- trendClass %>">' +
                        '<div class="trend-arrow arrow-<%- trendClass %>" />' +
                        '<div class="delta delta-<%- trendClass %>"><%- diff %></div>' 
               // '</div>'
        ),
        displayMessage: function() {
            // Don't display messages
        },
        createView: function() {
            return true;
        },
        
        updateView: function(viz, data) {
            this.$el.empty();
            var model = null;
            if (this.settings.has('trendField')) {
                var trendClass = 'nochange', diff = '0',
                    field = this.settings.get('field');

                var v = parseInt(data[0][this.settings.get('trendField')], 10);
                if (v > 0) {
                    trendClass = 'increase';
                    diff = ['+', String(v)].join('');
                } else if (v < 0) {
                    trendClass = 'decrease';
                    diff = [ String(v)].join('');
                } else if (v == 0) {
                    trendClass = 'nochange';
                    diff = ['+/-',  String(v)].join('');
                }

                model = {
                    trendClass: trendClass,
                    diff: diff
                };
            } 
            if (!model) {
                return;
            }
            // Render the HTML
            this.$el.html(this.template(model));
        }
    });

    return TrendIndicator;
    
});