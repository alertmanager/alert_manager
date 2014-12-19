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
        // Icon CSS classes
        icons: {
            increase: 'icon-triangle-up-small',
            decrease: 'icon-triangle-down-small'
        },
        // Template for trend indicator
        template: _.template(
                '<div class="single-trend <%- trendClass %>">' +
                        '<i class="<%- icon %>"></i> ' +
                        '<%- diff %>' +
                        '</div>'
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
                var icon = 'icon-minus', trendClass = 'nochange', diff = 'no change',
                    field = this.settings.get('field');

                var v = parseInt(data[0][this.settings.get('trendField')], 10);
                if (v > 0) {
                    trendClass = 'increase';
                    icon = this.icons.increase;
                    diff = ['+', String(v)].join('');
                } else if (v < 0) {
                    trendClass = 'decrease';
                    icon = this.icons.decrease;
                    diff = ['-', String(v)].join('');
                }

                model = {
                    icon: icon,
                    trendClass: trendClass,
                    diff: diff,
                    prev: prev
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