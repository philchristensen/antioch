function inspect(obj){
	var output = '';
	for(p in obj){
		if(!(obj[p] instanceof Function)){
			output += p + ': ' + obj[p] + "\n";
		}
	}
	alert(output);
}

function getEditorDetails(editorWindow){
	if(!editorWindow.opener){
		return {};
	}
	return editorWindow.opener.getEditorDetails(editorWindow);
}

function alertFailure(failure){
	alert(failure.error);
}