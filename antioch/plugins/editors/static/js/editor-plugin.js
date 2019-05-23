// Loaded in the client window automatically
(function($) {
  $(document).antioch('addMessageListener', 'edit', function(msg){
    $('#observations').load('/editor/' + msg.details.kind + '/' + msg.details.id, function(response, status, xhr) {
      if(status == "error"){
        var msg = "Couldn't load editor: "+ xhr.status + " " + xhr.statusText;
        $('#connection').antioch('write', msg, true);
      }
    });
  });
})(jQuery);