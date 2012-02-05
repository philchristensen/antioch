// Loaded in the client window automatically
(function($) {
	$(document).antioch('addMessageListener', 'ask', function(msg){
		var response = prompt(msg.details.question);
		var callback = msg.callback
		$(document).antioch('callRemote', 'register-task', {
			delay:      0,
			origin_id:  msg.callback.origin_id.toString(),
			verb_name:  msg.callback.verb_name,
			args:       JSON.stringify(msg.callback.args),
			kwargs:     JSON.stringify(msg.callback.kwargs),
		});
	});
})(jQuery);
