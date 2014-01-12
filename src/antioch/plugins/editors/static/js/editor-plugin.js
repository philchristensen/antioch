// Loaded in the client window automatically
(function($) {
  $('head').append($('<link>').attr({
    href:   "/assets/less/editors.less",
    type:   "text/css",
    media:  "screen",
    rel:    "stylesheet/less"
  }));
  $(document).antioch('addMessageListener', 'edit', function(msg){
    var lightbox = $('<div>').attr({
      'class': msg.details.kind + "-editor-modal center-block modal fade",
      'tabindex': "-1",
      'role': "dialog",
      'aria-labelledby': "editorFormLabel",
      'aria-hidden': "true",
    });
    $('body').append(lightbox);
    lightbox.modal({
      remote: '/editor/' + msg.details.kind + '/' + msg.details.id,
    });
  });
})(jQuery);
