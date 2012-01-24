function registration_init(){
}

function registration_run(info){
	var resultDeferred = new Divmod.Defer.Deferred();
	
	if(info['kind'] == 'change-password'){
		var editorWindow = window.open('/plugin/registration/change-password', 'change-password', buildWindowString({
			scrollbars:	'no',
			width:		'725',
			height:		'535',
		}));
	}
	
	return resultDeferred;
}
