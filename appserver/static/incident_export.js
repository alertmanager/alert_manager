require.config({
    paths: {
        IncidentExportView: "../app/alert_manager/views/IncidentExportView"
    }
});

require([
         "jquery",
         "underscore",
         'splunkjs/mvc',
         "backbone",
         "IncidentExportView",
         "splunkjs/mvc/searchmanager",
         "splunkjs/mvc/simplexml/ready!"
     ], function($, _, mvc, Backbone, IncidentExportView, SearchManager) {

     	var defaultTokenModel = mvc.Components.get("default");

     	const MIME_TYPE = 'text/html';
		$(document).on("click", "#export_content", function(event){
			if ( $( "#download_link" ).length ) {
				console.log("Link already exists");
				$( "#download_link" ).remove();
			}

			window.URL = window.webkitURL || window.URL;
			var bb = new Blob([$("#incident_detail_container").html()], {type: MIME_TYPE});
			var a = document.createElement('a');
			a.download = "export.html";
			a.href = window.URL.createObjectURL(bb);
			a.textContent = 'Download file';
			a.id = "download_link"

			a.dataset.downloadurl = [MIME_TYPE, a.download, a.href].join(':');
			a.draggable = true;

			$("#download_placeholder").append(a);

		});

 });

