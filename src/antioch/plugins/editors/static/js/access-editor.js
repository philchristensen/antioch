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
	
	var allow_deny = $('<button type="button" class="rule-toggle ' + access['rule'] + '"></button>');
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
	
	var group_accessor = $('<button type="button" class="access-toggle ' + access['access'] + '"></button>');
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
	
	var delete_rule = $('<button type="button" class="delete-rule"></button>');
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

function saveAccess(){
	var rules = $('#editor').find('.access-rule');
	var weight = 0;
	rules.each(function(i, e){
		var access_id = $(this).attr('id').split('-')[1];
		if(!access_id && $(this).hasClass('deleted')){
			return;
		}
		
		var elements = [
			$('<input type="hidden" name="accessid-' + access_id + '" value="' + access_id + '">'),
			$('<input type="hidden" name="deleted-' + access_id + '" value="' + ($(this).hasClass('deleted') ? 1 : 0) + '">'),
			$('<input type="hidden" name="access-' + access_id + '" value="' + $(this).find('.access-toggle').button('option', 'label') + '">'),
			$('<input type="hidden" name="accessor-' + access_id + '" value="' + $(this).find('.accessor-field').val() + '">'),
			$('<input type="hidden" name="rule-' + access_id + '" value="' + $(this).find('.rule-toggle').button('option', 'label') + '">'),
			$('<input type="hidden" name="permission-' + access_id + '" value="' + $(this).find('.permission-field').val() + '">'),
			$('<input type="hidden" name="weight-' + access_id + '" value="' + (weight++) + '">')
		];
		
		for(index in elements){
			$('#access-form').append(elements[index]);
		}
	});
}
