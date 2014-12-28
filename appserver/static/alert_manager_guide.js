require.config({
    paths: {
        "app": "../app",
        "showdown": "//softwaremaniacs.org/playground/showdown-highlight/showdown",
    },
    shim: {
        "showdown": {
            deps: [],
            exports: "Showdown"
        },
    }
});

require([ "jquery", "showdown" ], function($, Showdown) {
    
    var converter = new Showdown.converter();
    var text = $("#markdown_content").text();
    var html = converter.makeHtml(text);
    $("#markdown_content").html(html);

});
