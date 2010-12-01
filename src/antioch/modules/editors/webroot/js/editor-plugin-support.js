function getClientWindow(editorWindow){
	var win = editorWindow;
	if(! win.opener){
		return null;
	}
	while(win.opener){
		win = win.opener;
	}
	return win;
}

function getEditorDetails(editorWindow){
	clientWindow = getClientWindow(editorWindow);
	if(! clientWindow){
		return {};
	}
	info = clientWindow.editorDetails[editorWindow.name];
	return info;
}

