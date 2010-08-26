var editor;

function loadVerb(){
	var details = getEditorDetails(window);
	var info = details.info;
	
	$('#names-field').val(info['names']);
	$('#owner-field').val(info['owner']);
	
	editor = new CodeMirror(CodeMirror.replace("verb-code"), {
		parserfile: ["parsetxspace.js"],
		path: "/assets/CodeMirror-0.63/js/",
		stylesheet: "/assets/CodeMirror-0.63/css/txspacecolors.css",
		content: info['code'],
		textWrapping: false,
		lineNumbers: true,
		indentUnit: 4,
		tabMode: 'shift',
		height: '90%'
	});
}

function saveVerb(){
	var details = getEditorDetails(window);
	var info = {};
	
	info['names'] = $('#names-field').val();
	info['owner'] = $('#owner-field').val();
	info['code'] = editor.getCode();
	
	details.resultDeferred.callback(info);
	window.close();
}

function cancelVerb(){
	var details = getEditorDetails(window);
	details.resultDeferred.callback(null);
	window.close();
}

function requestAccessEditor(){
	var connector = window.opener.getConnector();
	var details = getEditorDetails(window);
	var deferred = connector.callRemote('req_access_editor', details.info['origin'], 'verb', details.info['names'][0]);
	deferred.addErrback(alertFailure);
	return deferred;
}

$(document).ready(function(){
	$('#access-button').click(requestAccessEditor);
	
	$('#cancel-button').click(cancelVerb);
	$('#save-button').click(saveVerb);
	
	loadVerb();
});