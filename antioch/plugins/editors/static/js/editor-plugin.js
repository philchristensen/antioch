// Loaded in the client window automatically
(function($) {
  $(document).antioch('addMessageListener', 'edit', function(msg){
    var editorUrl = '/editor/' + msg.details.kind + '/' + msg.details.id;
    $('#observations').load(editorUrl, function(response, status, xhr) {
      if(status == "error"){
        var msg = "Couldn't load editor: "+ xhr.status + " " + xhr.statusText;
        $('#connection').antioch('write', msg, true);
        return;
      }

      $('.editor form').on('reset', function(event){
        event.preventDefault();
        $('#observations').empty();
      });

      $('.editor form').on('submit', function(event){
          event.preventDefault();
          console.log("form submitted!")  // sanity check
          $.ajax({
              url : editorUrl, // the endpoint
              type : "POST", // http method
              data :  $('.editor form').serialize(),
              success : function(json) {
                  console.log(json); // log the returned json to the console
                  console.log("success"); // another sanity check
                  $('#observations').empty();
              },
              error : function(xhr,errmsg,err) {
                console.log(xhr.status + ": " + xhr.responseText); 
              }
          });
      });
    });
  });
})(jQuery);