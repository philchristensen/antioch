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
    $('#editorWindow').modal({
      remote: '/editor/' + msg.details.kind + '/' + msg.details.id,
    });
	});
})(jQuery);
