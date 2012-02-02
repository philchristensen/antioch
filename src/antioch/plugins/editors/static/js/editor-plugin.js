// Loaded in the client window automatically
(function($) {
	var sizes = {
		object: {
			width: 470,
			height: 595,
		},
		verb: {
			width: 815,
			height: 590,
		},
		property: {
			width: 815,
			height: 590,
		},
		access: {
			width: 600,
			height: 500,
		}
	};
	$(document).antioch('addMessageListener', 'edit', function(msg){
		window.open(
			'/plugin/editor/' + msg.details.kind + '/' + msg.details.id,
			[msg.details.kind, 'editor', msg.details.id].join('-'), 
			buildWindowString(sizes[msg.details.kind])
		);
	});
})(jQuery);
