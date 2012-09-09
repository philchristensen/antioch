// Loaded in the client window automatically
(function($) {
	var sizes = {
		object: {
			width: 470,
			height: 625,
		},
		verb: {
			width: 815,
			height: 590,
		},
		property: {
			width: 975,
			height: 585,
		},
		access: {
			width: 650,
			height: 250,
		}
	};
	$(document).antioch('addMessageListener', 'edit', function(msg){
		window.open(
			'/plugin/editor/' + msg.details.kind + '/' + msg.details.id,
			[msg.details.kind, 'editor', msg.details.id].join('-'), 
			buildWindowString(sizes[msg.details.kind.split('/')[0]])
		);
	});
})(jQuery);
