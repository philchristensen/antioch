var editorDetails = {};

function plugin_init(info, attribs){
	var resultDeferred = new Divmod.Defer.Deferred();
	var window_name = 'editor-plugin-' + info['kind'] + '-' + info['id'];
	var type = info['kind'];
	
	var editorWindow = window.open('/plugin/editor/' + type, window_name, buildWindowString(attribs));
	
	editorDetails[window_name] = {
		info			: info,
		resultDeferred	: resultDeferred,
	};
	
	// this 'thread' waits for the editor window to
	// close before cancelling the waiting deferred
	var spyID = setInterval(function(){
		return function(){
			if(editorWindow && editorWindow.closed && ! resultDeferred._called){
				resultDeferred.callback(null);
				delete editorDetails[window_name];
				clearInterval(spyID);
			}
		}
	}(), 100);
	
	return resultDeferred;
}

function editor_plugin_init(info){
	if(info['kind'] == 'object'){
		return plugin_init(info, {
			scrollbars:	'no',
			width:		'465',
			height:		'535',
		});
	}
	else if(info['kind'] == 'property'){
		return plugin_init(info, {
			scrollbars:	'no',
			width:		'630',
			height:		'525',
		});
	}
	else if(info['kind'] == 'verb'){
		return plugin_init(info, {
			scrollbars:	'no',
			width:		'970',
			height:		'600',
		});
	}
}

function access_plugin_init(info){
	info['kind'] = 'access';
	return plugin_init(info, {
		scrollbars:	'auto',
		width:		'750',
		height:		'295',
	});
}
