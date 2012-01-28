// Loaded in the client window automatically
(function($) {
	$(document).antioch('addMessageListener', 'edit', function(){
		alert('edit');
	});
})(jQuery);
