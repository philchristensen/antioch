// import Nevow.Athena

txspace.ClientConnector = Nevow.Athena.Widget.subclass('txspace.ClientConnector');

txspace.ClientConnector.methods(
	function parse(self, text){
		/*
		 * Send a command to the server.
		 */
		self.callRemote('parse', text);
		var actions = $('.actions');
		actions.append('<br/><span class="issued-command">' + text + '</span>')
		actions.scrollTo('max');
	},
	function setObservations(self, observations){
		/*
		 * Called by the server to change the main client display.
		 */
		$('.name').html(observations['name']);
		$('.description').html(observations['description']);
		
		var contents_area = $('.contents');
		var player_content = $('<div id="players-list"></div>');
		var item_content = $('<div id="contents-list"></div>');
		if(observations['contents'].length){
			var player_list = $('<ul></ul>');
			var contents_list = $('<ul></ul>');
			
			for(key in observations['contents']){
				(function(){
					var details = observations['contents'][key];
					if(details.type > 0){
						image_div = ($('<div class="player-image"></div>'));
						if(details.image){
							image_div.append($('<img src="' + details.image + '" />'));
						}
						else{
							image_div.append($('<img src="/assets/images/silhouette.png" />'));
						}
					
						name_div = $('<div class="player-name"></div>');
						name_div.html(details.name);
					
						list_item = $('<li></li>');
						list_item.click(function(){
							look(details.name);
						});
						list_item.append(image_div);
						list_item.append(name_div);
					
						if(details.mood){
							mood_div = $('<div class="player-mood"></div>');
							mood_div.html(details.mood);
							list_item.append(mood_div);
						}
						player_list.append(list_item);
					}
					else{
						list_item = $('<li onClick="look(this.innerHTML)"></li>');
						list_item.html(details.name);
						list_item.click(function(){
							look(details.name);
						});
						contents_list.append(list_item);
					}
				})()
			}
			
			player_content.append($('<strong>people here:</strong>'));
			player_content.append(player_list);
			player_content.append($('<br style="clear: both;"/>'))
			
			item_content.append($('<strong>obvious contents:</strong>'));
			item_content.append(contents_list);
			item_content.append($('<br style="clear: both;"/>'))
		}
		contents_area.empty();
		contents_area.append(player_content);
		contents_area.append(item_content);
		
		$('.client-prompt').focus();
	},
	function write(self, text, error){
		/*
		 * Called by the server to output a line to the action pane.
		 */
		var actions = $('.actions');
		
		while(text.indexOf('<') != -1)
			text = text.replace('<', '&lt;');
		
		while(text.indexOf('>') != -1)
			text = text.replace(">", '&gt;')
		
		while(text.indexOf("\n") != -1)
			text = text.replace("\n", '<br/>')
		
		while(text.indexOf('  ') != -1)
			text = text.replace('  ', '&nbsp;&nbsp;')
		
		if(error){
			actions.append('<br/><span class="error-response">' + text + '</span>');
		}
		else{
			actions.append('<br/>' + text);
		}
		
		actions.scrollTo('max');
	},
	function objedit(self, info){
		/*
		 * Called by the server to open an object editor window.
		 */
		return openEditor('entity', info, 435, 390);
	},
	function verbedit(self, info){
		/*
		 * Called by the server to open a verb editor window.
		 */
		return openEditor('verb', info, 821, 551);
	},
	function propedit(self, info){
		/*
		 * Called by the server to open a property editor window.
		 */
		return openEditor('property', info, 821, 351);
	},
	function acledit(self, info){
		/*
		 * Called by the server to open an ACL editor window.
		 */
		return openEditor('acl', info, 435, 390);
	},
	function logout(self){
		/*
		 * Called by the server to logout the user.
		 */
		window.location = '/logout';
		return true;
	}
);

// the waiting deferred and the editor details
// are keyed to the window name.
var editorDetails = {};

var commandHistory = [];
var historyPosition = -1;
var currentCommand = ''

function openEditor(type, info, width, height){
	/*
	 * Once the server has sent `info`, this function opens an
	 * editor window. The child window uses the parent's Athena
	 * connection to communicate with the server.
	 */
	var resultDeferred = new Divmod.Defer.Deferred();
	
	var window_name = type + '-' + Date.now();
	var editorWindow = window.open('/edit/' + type, window_name, 'menubar=no,status=no,toolbar=no,location=no,directories=no,resizable=yes,scrollbars=no,width=' + width + ',height=' + height);
	
	editorDetails[window_name] = {
		info			: info,
		resultDeferred	: resultDeferred,
	}
	
	// this 'thread' waits for the editor window to
	// close before cancelling the waiting deferred
	var spyID = setInterval(function(){
		if(editorWindow.closed && ! resultDeferred._called){
			resultDeferred.callback(null);
			delete editorDetails[window_name];
			clearInterval(spyID);
		}
	}, 100);
	
	return resultDeferred;
}

function getEditorDetails(editorWindow){
	/*
	 * Retrieve the proper info for the given window.
	 */
	return editorDetails[editorWindow.name];
}

function getConnector(){
	/*
	 * Return the Athena connection to the server.
	 */
	var element = document.getElementById('athenaid:1-client-connector');
	return Nevow.Athena.Widget.get(element);
}

function handleKeyEvent(event){
	/*
	 * Command-line key handler.
	 */
	switch(event.which){
		case 13:
			var connector = getConnector();
			var command = event.target.value;
			if(command){
				connector.parse(command);
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
	var connector = getConnector()
	
	connector.parse('look ' + item);
}

$(document).ready(function(){
	$('.client-prompt').keyup(handleKeyEvent);
	
	$('.look-me').click(function(){
		look('me');
	});
	
	$('.look-here').click(function(){
		look('here');
	});
});