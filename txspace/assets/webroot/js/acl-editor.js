function loadACL(){
	var details = getEditorDetails(window);
	var info = details.info;
	var perms = $('#permissions-field');
	
	for(index in info['permissions']){
		perms.val(perms.val() + info['permissions'][index].join(' ') + "\n");
	}
}

function saveACL(){
	var details = getEditorDetails(window);
	var info = {permissions:[]};
	var perms = $('#permissions-field')
	var permlines = perms.val().split("\n");
	
	for(index in permlines){
		var perm = permlines[index];
		info['permissions'][info['permissions'].length] = perm.split(' ');
	}
	
	details.resultDeferred.callback(info);
	window.close();
}

function cancelACL(){
	var details = getEditorDetails(window);
	details.resultDeferred.callback(null);
	window.close();
}