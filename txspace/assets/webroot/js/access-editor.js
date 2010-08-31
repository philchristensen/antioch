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

function addRule(access){
	var perms = $('#editor');
	
	var thumb = $('<div class="drag-thumb"></div>');
	
	var allow_deny = $('<button class="rule-toggle ' + access['rule'] + '"></button>');
	allow_deny.button({
		label	: access['rule'],
	});
	
	allow_deny.click(function(e){
		if($(this).hasClass('allow')){
			$(this).button('option', 'label', 'deny');
			$(this).removeClass('allow').addClass('deny');
		}
		else{
			$(this).button('option', 'label', 'allow');
			$(this).removeClass('deny').addClass('allow');
		}
		e.stopImmediatePropagation();
	});
	
	var group_accessor = $('<button class="access-toggle ' + access['access'] + '"></button>');
	group_accessor.button({
		label	: access['access'],
	});
	group_accessor.click(function(e){
		if($(this).hasClass('group')){
			$(this).button('option', 'label', 'accessor');
			$(this).removeClass('group').addClass('accessor');
		}
		else{
			$(this).button('option', 'label', 'group');
			$(this).removeClass('accessor').addClass('group');
		}
		e.stopImmediatePropagation();
	});
	
	var accessor = $('<input type="text" class="accessor-field ui-widget" size="30" value="' + access['accessor'] + '" />');
	
	var permissions = $('<select class="permission-field ui-widget ui-widget-content"></select>');
	for(index in default_permissions){
		var permission = default_permissions[index];
		if(permission == access['permission']){
			permissions.append($('<option value="' + permission + '" selected="selected">' + permission + '</option>'));
		}
		else{
			permissions.append($('<option value="' + permission + '">' + permission + '</option>'));
		}
	}
	
	var delete_rule = $('<button class="delete-rule"></button>');
	delete_rule.button({
		icons	: {primary: 'ui-icon-trash'},
	}).click(function(){
		$(this).parent().toggleClass('deleted');
	});
	
	
	var row = $('<div id="access-' + access['access_id'] + '" class="access-rule"></div>');
	row.append(thumb);
	row.append(allow_deny);
	row.append(group_accessor);
	row.append(accessor);
	row.append(permissions);
	row.append(delete_rule);
	
	perms.append(row);
}

function loadAccess(){
	var details = getEditorDetails(window);
	var info = details.info;
	
	document.title = 'Access control for ' + info['id'];
	
	for(index in info['access']){
		var access = info['access'][index];
		addRule(access);
	}
}

function saveAccess(){
	var details = getEditorDetails(window);
	var info = {
		access	: function(){
			var access = {};
			var rules = $('#editor').find('.access-rule');
			var weight = 0;
			rules.each(function(index, element){
				var access_id = $(this).attr('id').split('-')[1];
				if(!access_id && $(this).hasClass('deleted')){
					return;
				}
				access[access_id] = {
					deleted		: $(this).hasClass('deleted'),
					access		: $(this).find('.access-toggle').button('option', 'label'),
					accessor	: $(this).find('.accessor-field').val(),
					rule		: $(this).find('.rule-toggle').button('option', 'label'),
					permission	: $(this).find('.permission-field').val(),
					weight		: weight++,
				};
			});
			return access;
		}(),
	};
	
	details.resultDeferred.callback(info);
	window.close();
}

function cancelAccess(){
	var details = getEditorDetails(window);
	details.resultDeferred.callback(null);
	window.close();
}

function jqueryLoaded(){
	$('#editor').sortable({
		handle:	".drag-thumb",
		items: 	".access-rule",  
	})
	
	$('#add-button').button({icons:{primary:'ui-icon-plusthick'}}).click(function(){
		addRule({
			access_id	: 0,
			access		: "group",
			accessor	: "",
			rule		: "allow",
			permission	: "anything",
		});
	});
	$('#cancel-button').button().click(cancelAccess);
	$('#save-button').button().click(saveAccess);
	
	$('#html-checkbox').button();
	
	loadAccess();
}