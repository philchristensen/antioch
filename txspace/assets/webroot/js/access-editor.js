var default_permissions = [
	'anything',
	'read',
	'write',
	'entrust',
	'execute',
	'move',
	'transmute',
	'derive',
	'develop',
]

function loadAccess(){
	var details = getEditorDetails(window);
	var info = details.info;
	var perms = $('#access-container');
	
	for(index in info['access']){
		var access = info['access'][index];
		
		var thumb = $('<div class="drag-thumb"></div>');
		var allow_deny = $('<div class="rule-toggle ' + access['rule'] + '"></div>').click(function(e){
			if($(this).hasClass('allow')){
				$(this).removeClass('allow').addClass('deny');
			}
			else{
				$(this).removeClass('deny').addClass('allow');
			}
			e.stopImmediatePropagation();
		});
		
		var group_accessor = $('<div class="access-toggle ' + access['access'] + '"></div>').click(function(e){
			if($(this).hasClass('group')){
				$(this).removeClass('group').addClass('object');
			}
			else{
				$(this).removeClass('object').addClass('group');
			}
			e.stopImmediatePropagation();
		});
		var accessor = $('<input type="text" class="accessor-field" size="30" value="' + access['accessor'] + '" />');
		
		var permissions = $('<select class="permission-field"></select>');
		for(index in default_permissions){
			var permission = default_permissions[index];
			if(permission == access['permission']){
				permissions.append($('<option value="' + permission + '" selected="selected">' + permission + '</option>'));
			}
			else{
				permissions.append($('<option value="' + permission + '">' + permission + '</option>'));
			}
		}
		
		var row = $('<div id="access-' + access['id'] + '"></div>');
		row.append(thumb);
		row.append(allow_deny);
		row.append(group_accessor);
		row.append(accessor);
		row.append(permissions);
		
		perms.append(row);
	}
}

function saveAccess(){
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

function cancelAccess(){
	var details = getEditorDetails(window);
	details.resultDeferred.callback(null);
	window.close();
}