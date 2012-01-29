// Loaded in the client window automatically
debugger;
(function($) {
	var sizes = {
		object: {
			width: 600,
			height: 500,
		},
		verb: {
			width: 600,
			height: 500,
		},
		property: {
			width: 600,
			height: 500,
		},
		access: {
			width: 600,
			height: 500,
		}
	};
	$(document).antioch('addMessageListener', 'edit', function(msg){
		window.open(
			'/plugin/editor/' + msg.details.kind + '/',
			[msg.details.kind, 'editor', msg.details.id].join('-'), 
			buildWindowString(sizes[msg.details.kind])
		);
	});
})(jQuery);
