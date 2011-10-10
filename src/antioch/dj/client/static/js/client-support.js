var commandHistory = [];
var historyPosition = -1;
var currentCommand = ''

function getConnector(){
	/*
	 * Return the Athena connection to the server.
	 */
	// var element = document.getElementById('athenaid:1-client-connector');
	// return Nevow.Athena.Widget.get(element);
}

function callRemote(command, options, callback){
	$.ajax('/rest/' + command, {
		type: 'POST',
		dataType: 'json',
		processData: false,
		data: JSON.stringify(options),
		error:	function(jqXHR, textStatus, errorThrown){
			alert('Error in callRemote: ' + errorThrown);
		},
		success: function(data, textStatus, jqXHR){
			if(callback){
				callback(data);
			}
		}
	});
}

function listen(handler){
	$.ajax('/comet', {
		dataType: 'json',
		contentType: 'application/json',
		cache: false,
		error:	function(jqXHR, textStatus, errorThrown){
			if(textStatus == 'timeout'){
				listen(handler);
			}
			else if(textStatus != 'abort'){
				alert('Error in listen: ' + errorThrown);
			}
		},
		success: function(data, textStatus, jqXHR){
			handler(JSON.stringify(data));
			listen(handler);
		}
	});
}

// function getEditorDetails(editorWindow){
// 	/*
// 	 * Retrieve the proper info for the given window.
// 	 */
// 	return editorDetails[editorWindow.name]
// }

function handleKeyEvent(event){
	/*
	 * Command-line key handler.
	 */
	switch(event.which){
		case 13:
			var command = event.target.value;
			if(command){
				callRemote('parse', {user_id: 2, sentence: command});
				commandHistory.push(command);
				historyPosition = commandHistory.length - 1;
			}
			event.target.value = '';
			event.preventDefault();
			break;
		case 38:
			// up arrow
			if(historyPosition == commandHistory.length - 1){
				currentCommand = event.target.value
			}
			if(historyPosition >= 0){
				event.target.value = commandHistory[historyPosition--];
			}
			event.preventDefault();
			break;
		case 40:
			// down arrow
			if(historyPosition + 2 <= commandHistory.length){
				if(historyPosition + 2 == commandHistory.length){
					event.target.value = currentCommand;
				}
				else{
					event.target.value = commandHistory[historyPosition + 2];
				}
				historyPosition++;
			}
			event.preventDefault();
			break;
		default:
			break;
	}
}

function look(item){
	/*
	 * Primitive click-to-look support.
	 */
	callRemote('parse', {user_id: 2, sentence: 'look ' + item});
}
