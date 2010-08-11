function loadEntity(){
	var details = getEditorDetails(window);
	var info = details.info;
	
	$('#name-field').val(info['name']);
	$('#parent-field').val(info['parent']);
	$('#location-field').val(info['location']);
	$('#owner-field').val(info['owner']);
	$('#id-field').val(info['id']);
	$('#type-select').val(info['entity_type']);
	
	var verbsSelect = $('#verbs-select');
	verbsSelect.empty()
	for(index in info['verbs']){
		var verb = info['verbs'][index];
		verbsSelect.append('<option value="' + verb + '">' + verb + '</option>');
	}
	
	var propsSelect = $('#props-select');
	propsSelect.empty()
	for(index in info['properties']){
		var prop = info['properties'][index];
		propsSelect.append('<option value="' + prop + '">' + prop + '</option>');
	}
}

function saveEntity(){
	var details = getEditorDetails(window);
	var info = {};
	
	info['name'] = $('#name-field').val();
	info['parent'] = $('#parent-field').val();
	info['location'] = $('#location-field').val();
	info['owner'] = $('#owner-field').val();
	info['entity_type'] = parseInt($('#type-select').val());
	
	details.resultDeferred.callback(info);
	window.close();
}

function cancelEntity(){
	var details = getEditorDetails(window);
	details.resultDeferred.callback(null);
	window.close();
}

function reloadEntity(){
	var details = getEditorDetails(window);
	var connector = window.opener.getConnector();
	var deferred = connector.callRemote('get_entity_attributes', details.info['id']);
	
	deferred.addCallback(function(response){
		details.info = response;
		loadEntity();
	});
	deferred.addErrback(alertFailure);
	
	return deferred;
}

function requestEntityEditor(id){
	var connector = window.opener.getConnector();
	deferred = connector.callRemote('req_entity_editor', id);
	deferred.addErrback(alertFailure);
	return deferred;
}

function addVerb(){
	var details = getEditorDetails(window);
	var connector = window.opener.getConnector();
	var verb_name = prompt("What do you want to call this verb?");
	
	if(! verb_name.match(/^\S+$/)){
		alert("Sorry, verb names cannot have spaces.");
	}
	else{
		var deferred = connector.callRemote('req_code_editor', details.info['id'], verb_name);
		
		deferred.addCallback(function(response){
			reloadEntity();
		});
		deferred.addErrback(alertFailure);
		
		return deferred;
	}
}

function removeVerb(){
	var details = getEditorDetails(window);
	if($('#verbs-select').val()){
		var verb_name = $('#verbs-select').val();
		if(confirm("Are you sure you want to delete the verb '" + verb_name + "'?")){
			var connector = window.opener.getConnector();
			var deferred = connector.callRemote('remove_verb', details.info['id'], verb_name);
			
			deferred.addCallback(function(response){
				reloadEntity();
			});
			deferred.addErrback(alertFailure);
			
			return deferred;
		}
	}
}

function requestVerbEditor(item){
	var details = getEditorDetails(window);
	var connector = window.opener.getConnector();
	var deferred = connector.callRemote('req_code_editor', details.info['id'], item);
	
	deferred.addCallback(function(response){
		reloadEntity();
	});
	deferred.addErrback(alertFailure);
	
	return deferred;
}

function addProperty(){
	var details = getEditorDetails(window);
	var connector = window.opener.getConnector();
	var prop_name = prompt("What do you want to call this property?");
	
	if(! prop_name.match(/^\S+$/)){
		alert("Sorry, property names cannot have spaces.");
	}
	else{
		var deferred = connector.callRemote('req_property_editor', details.info['id'], prop_name);
		
		deferred.addCallback(function(response){
			reloadEntity();
		});
		deferred.addErrback(alertFailure);
		
		return deferred;
	}
}

function removeProperty(){
	var details = getEditorDetails(window);
	if($('#props-select').val()){
		var prop_name = $('#props-select').val();
		if(confirm("Are you sure you want to delete the property '" + prop_name + "'?")){
			var connector = window.opener.getConnector();
			var deferred = connector.callRemote('remove_property', details.info['id'], prop_name);
			
			deferred.addCallback(function(response){
				reloadEntity();
			});
			deferred.addErrback(alertFailure);
			
			return deferred;
		}
	}
}
function requestPropertyEditor(item){
	var details = getEditorDetails(window);
	var connector = window.opener.getConnector();
	var deferred = connector.callRemote('req_property_editor', details.info['id'], item);
	
	deferred.addCallback(function(response){
		reloadEntity();
	});
	deferred.addErrback(alertFailure);
	
	return deferred;
}

function requestACLEditor(){
	var details = getEditorDetails(window);
	var connector = window.opener.getConnector();
	
	deferred = connector.callRemote('req_acl_editor', details.info['id'], null);
	deferred.addErrback(alertFailure);
	return deferred;
}

$(document).ready(function(){
	$('#parent-button').click(function(){
		requestEntityEditor($('#parent-field').val())
	});
	$('#location-button').click(function(){
		requestEntityEditor($('#location-field').val())
	});
	$('#owner-button').click(function(){
		requestEntityEditor($('#owner-field').val())
	});
	
	$('#acl-button').click(requestACLEditor);
	
	$('#verbs-select').dblclick(function(){
		requestVerbEditor($('#verbs-select').val());
	});
	
	$('#props-select').dblclick(function(){
		requestPropertyEditor($('#props-select').val());
	});
	
	$('#add-verb').click(addVerb);
	$('#remove-verb').click(removeVerb);
	$('#add-prop').click(addProperty);
	$('#remove-prop').click(removeProperty);
	
	$('#cancel-button').click(cancelEntity);
	$('#save-button').click(saveEntity);
	
	loadEntity();
});