var editor;
var syntaxStates = {
	'string'	: 'DummyParser', 
	'html'		: 'HTMLMixedParser', 
	'python'	: 'antiochParser', 
	'dynamic'	: 'antiochParser',
};

function loadProperty(){
	var details = getEditorDetails(window);
	var info = details.info;
	
	$('#name-field').val(info['name']);
	$('#owner-field').val(info['owner']);
	
	$('#type-select').val(info['type']);
	
	document.title = 'Property #' + info['id'] + ' (' + info['name'] + ') on Object ' + info['origin'];
	
	editor = new CodeMirror(CodeMirror.replace("property-value"), {
		parserfile: ["parsexml.js", "parsecss.js", "parsejavascript.js", "tokenizejavascript.js",
						"parsehtmlmixed.js", "parseantioch.js", "parsedummy.js"],
		path: "/plugin/editor/assets/js/CodeMirror-0.91/js/",
		stylesheet: "/plugin/editor/assets/js/CodeMirror-0.91/css/antiochcolors.css",
		content: info['value'],
		textWrapping: false,
		lineNumbers: true,
		indentUnit: 4,
		tabMode: "shift",
		height: null,
		width: null,
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
	info['type'] = $('#type-select').val();
	
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

function requestAccessEditor(){
	var details = getEditorDetails(window);
	var connector = getClientWindow(window).getConnector();
	deferred = connector.callRemote('req_access_editor', details.info['origin'], 'property', details.info['name']);
	deferred.addErrback(alertFailure);
	return deferred;
}

function init(){
	$('#access-button').button().click(requestAccessEditor);
	
	$('#cancel-button').button().click(cancelProperty);
	$('#save-button').button().click(saveProperty);
	
	$('#type-select').change(function(){
		var lang = $('#type-select').val();
		toggleSyntax(lang);
		if(lang == 'string'){
			// show html check
			$('#html-checkbox').add($('#html-label')).show();
		}
		else {
			// hide html check
			$('#html-checkbox').add($('#html-label')).hide();
			$('#html-checkbox').removeAttr('checked');
		}
	});
	
	$('#html-checkbox').change(function(){
		toggleSyntax($(this).is(':checked') ? 'html' : 'string');
	});
	
	loadProperty();
}