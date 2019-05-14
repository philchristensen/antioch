// Loaded in the client window automatically
(function($) {
  // $('head').append($('<link>').attr({
  //   href:   "/static/less/editors.less",
  //   type:   "text/css",
  //   media:  "screen",
  //   rel:    "stylesheet/less"
  // }));
  // less.sheets.push($('link[href="/static/less/editors.less"]')[0]);
  // less.refresh();
  
  $(document).antioch('addMessageListener', 'edit', function(msg){
    var scratch = $('.card .card-back');
    scratch.load('/editor/' + msg.details.kind + '/' + msg.details.id, function(response, status, xhr) {
      if(status == "error"){
        var msg = "Couldn't load editor: "+ xhr.status + " " + xhr.statusText;
        $('#connection').antioch('write', msg, true);
      }
      else {
        // scratch.find('script').each(function(index, item){
        //   $.getScript(item.src);
        // });
        
        // var front = document.getElementById('observations');
        // var back = flippant.flip(front, response);
        $('#observations').parent('.card').addClass('flipped');
      }
    });
  });
})(jQuery);