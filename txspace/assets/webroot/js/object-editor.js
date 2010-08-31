function loadObject(){
	var details = getEditorDetails(window);
	var info = details.info;
	
	$('#name-field').val(info['name']);
	$('#parent-field').val(info['parents']);
	$('#location-field').val(info['location']);
	$('#owner-field').val(info['owner']);
	$('#id-field').val(info['id']);
	
	document.title = 'Object #' + info['id'] + ' (' + info['name'] + ')';
	
	var verbsSelect = $('#verbs-select');
	verbsSelect.empty()
	for(index in info['verbs']){
		v = info['verbs'][index];
		verb_name = v['names'].split(',')[0]
		verbsSelect.append('<option value="' + verb_name + '">' + v['names'] + '</option>');
	}
	
	var propertiesSelect = $('#properties-select');
	propertiesSelect.empty()
	for(index in info['properties']){
		p = info['properties'][index];
		propertiesSelect.append('<option value="' + p['name'] + '">' + p['name'] + '</option>');
	}
}

function saveObject(){
	var details = getEditorDetails(window);
	var info = {};
	
	info['name'] = $('#name-field').val();
	info['parents'] = $('#parent-field').val();
	info['location'] = $('#location-field').val();
	info['owner'] = $('#owner-field').val();
	
	details.resultDeferred.callback(info);
	window.close();
}

function cancelObject(){
	var details = getEditorDetails(window);
	details.resultDeferred.callback(null);
	window.close();
}

function reloadObject(){
	var details = getEditorDetails(window);
	var connector = window.opener.getConnector();
	var deferred = connector.callRemote('get_object_details', details.info['id']);
	
	deferred.addCallback(function(response){
		details.info = response;
		loadObject();
	});
	deferred.addErrback(alertFailure);
	
	return deferred;
}

function requestObjectEditor(id){
	var connector = window.opener.getConnector();
	deferred = connector.callRemote('req_object_editor', id);
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
		var deferred = connector.callRemote('req_verb_editor', details.info['id'], verb_name);
		
		deferred.addCallback(function(response){
			reloadObject();
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
				reloadObject();
			});
			deferred.addErrback(alertFailure);
			
			return deferred;
		}
	}
}

function requestVerbEditor(object_id, verb_name){
	var details = getEditorDetails(window);
	var connector = window.opener.getConnector();
	var deferred = connector.callRemote('req_verb_editor', object_id, verb_name);
	
	deferred.addCallback(function(response){
		reloadObject();
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
			reloadObject();
		});
		deferred.addErrback(alertFailure);
		
		return deferred;
	}
}

function removeProperty(){
	var details = getEditorDetails(window);
	if($('#properties-select').val()){
		var prop_name = $('#properties-select').val();
		if(confirm("Are you sure you want to delete the property '" + prop_name + "'?")){
			var connector = window.opener.getConnector();
			var deferred = connector.callRemote('remove_property', details.info['id'], prop_name);
			
			deferred.addCallback(function(response){
				reloadObject();
			});
			deferred.addErrback(alertFailure);
			
			return deferred;
		}
	}
}
function requestPropertyEditor(object_id, property_name){
	var details = getEditorDetails(window);
	var connector = window.opener.getConnector();
	var deferred = connector.callRemote('req_property_editor', object_id, property_name);
	
	deferred.addCallback(function(response){
		reloadObject();
	});
	deferred.addErrback(alertFailure);
	
	return deferred;
}

function requestAccessEditor(){
	var details = getEditorDetails(window);
	var connector = window.opener.getConnector();
	
	deferred = connector.callRemote('req_access_editor', details.info['id'], 'object', '');
	deferred.addErrback(alertFailure);
	return deferred;
}

function jqueryLoaded(){
	jQuery.getScript('/assets/js/jquery.scrollTo-1.4.2-min.js');
	
	$('#parent-button').button({icons:{primary:'ui-icon-newwin'}, text:false}).click(function(){
		var parents = $('#parent-field').val().split(',');
		for(index in parents){
			requestObjectEditor(parents[index]);
		}
	});
	$('#location-button').button({icons:{primary:'ui-icon-newwin'}, text:false}).click(function(){
		requestObjectEditor($('#location-field').val())
	});
	$('#owner-button').button({icons:{primary:'ui-icon-newwin'}, text:false}).click(function(){
		requestObjectEditor($('#owner-field').val())
	});
	
	$('#access-button').button().click(requestAccessEditor);
	
	$('#verbs-select').dblclick(function(){
		var details = getEditorDetails(window);
		requestVerbEditor(details.info['id'], $('#verbs-select').val());
	});
	
	$('#properties-select').dblclick(function(){
		var details = getEditorDetails(window);
		requestPropertyEditor(details.info['id'], $('#properties-select').val());
	});
	
	$('#add-verb').button({icons:{primary:'ui-icon-plusthick'}}).click(addVerb);
	$('#remove-verb').button({icons:{primary:'ui-icon-minusthick'}}).click(removeVerb);
	$('#add-prop').button({icons:{primary:'ui-icon-plusthick'}}).click(addProperty);
	$('#remove-prop').button({icons:{primary:'ui-icon-minusthick'}}).click(removeProperty);
	
	$('#cancel-button').button().click(cancelObject);
	$('#save-button').button().click(saveObject);
	
	loadObject();
}