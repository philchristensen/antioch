function inspect(obj){
	var output = '';
	for(prop in obj){
		if(!(obj[prop] instanceof Function)){
			output += prop + ': ' + obj[prop] + "\n";
		}
	}
	alert(output);
}

function getEditorDetails(editorWindow){
	return editorWindow.opener.getEditorDetails(editorWindow);
}

function alertFailure(failure){
	alert(failure.error);
}