var editor;
var syntaxStates = ['DummyParser', 'HTMLMixedParser', 'txSpaceParser', 'txSpaceParser'];

function loadProperty(){
	var details = getEditorDetails(window);
	var info = details.info;
	
	$('#name-field').val(info['name']);
	$('#owner-field').val(info['owner']);
	
	$('#type-select').val(info['eval_type']);
	if(info['eval_type'] > 0){
		$('#type-select').val(info['eval_type'] + 1)
	}
	else if(info['name'] == 'description'){
		$('#type-select').val(1);
	}
	
	editor = new CodeMirror(CodeMirror.replace("prop_code"), {
		parserfile: ["parsexml.js", "parsecss.js", "parsejavascript.js", "tokenizejavascript.js",
						"parsehtmlmixed.js", "parsetxspace.js", "parsedummy.js"],
		path: "/assets/CodeMirror-0.63/js/",
		stylesheet: "/assets/CodeMirror-0.63/css/txspacecolors.css",
		content: info['value'],
		textWrapping: false,
		lineNumbers: true,
		indentUnit: 4,
		tabMode: "shift",
		height: "90%",
		initCallback: function(){
			editor.setParser(syntaxStates[$('#type-select').val()]);
		}
	});
}

function saveProperty(){
	var details = getEditorDetails(window);
	var info = {};
	
	info['name'] = $('#name-field').val();
	info['owner'] = $('#owner-field').val();
	info['value'] = editor.getCode();
	info['eval_type'] = $('#type-select').val();
	if(info['eval_type'] == 1){
		info['eval_type'] = 0;
	}
	else if(info['eval_type'] > 1){
		info['eval_type'] = info['eval_type'] - 1;
	}
	
	details.resultDeferred.callback(info);
	window.close();
}

function cancelProperty(){
	var details = getEditorDetails(window);
	details.resultDeferred.callback(null);
	window.close();
}

function toggleSyntax(type){
	editor.setParser(syntaxStates[type]);
}

function requestACLEditor(){
	var details = getEditorDetails(window);
	var connector = window.opener.getConnector();
	deferred = connector.callRemote('req_acl_editor', details.info['origin'], details.info['name']);
	deferred.addErrback(alertFailure);
	return deferred;
}


$(document).ready(function(){
	$('#acl-button').click(requestACLEditor);
	
	$('#cancel-button').click(cancelProperty);
	$('#save-button').click(saveProperty);
	
	$('#type-select').change(function(){
		toggleSyntax(parseInt($('#type-select').val()));
	})
	
	loadProperty();
});