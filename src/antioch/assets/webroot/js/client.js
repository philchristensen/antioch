// import Nevow.Athena

antioch.ClientConnector = Nevow.Athena.Widget.subclass('antioch.ClientConnector');

antioch.ClientConnector.methods(
	function plugin(self, name, plugin_script_url, args){
		var resultDeferred = new Divmod.Defer.Deferred();
		function initialize_plugin(){
			eval(name + '_init();');
			run_plugin();
		}
		
		function run_plugin(){
			var result = eval(name + '_run(args);');
			if(result.addCallback){
				result.addCallback(function(r){
					resultDeferred.callback(r);
				});
			}
			else{
				resultDeferred.callback(result);
			}
			return result;
		}
		
		if(plugin_installs[plugin_script_url]){
			jQuery.getScript(plugin_script_url, run_plugin);
		}
		else{
			jQuery.getScript(plugin_script_url, initialize_plugin);
		}
		
		return resultDeferred;
	},
	function parse(self, text){
		/*
		 * Send a command to the server.
		 */
		self.callRemote('parse', text);
		var actions = $('#actions');
		actions.append('<br/><span class="issued-command">' + text + '</span>')
		actions.scrollTo('max');
	},
	function setObservations(self, observations){
		/*
		 * Called by the server to change the main client display.
		 */
		$('.name').html(observations['name']);
		$('.description').html(observations['description']);
		
		var player_content = $('<div id="players-list"></div>');
		var item_content = $('<div id="contents-list"></div>');
		
		if(observations['contents'].length){
			var player_list = $('<ul></ul>');
			var contents_list = $('<ul></ul>');
			
			for(index in observations['contents']){
				var details = observations['contents'][index];
				if(details.type){
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
					list_item = $('<li></li>');
					list_item.html(details.name);
					list_item.click(function(){
						look(details.name);
					});
					contents_list.append(list_item);
				}
			}
			
			if(player_list[0].children.length){
				player_content.append($('<strong>people here:</strong>'));
				player_content.append(player_list);
				player_content.append($('<br style="clear: both;"/>'))
			}
			if(contents_list[0].children.length){
				item_content.append($('<strong>obvious contents:</strong>'));
				item_content.append(contents_list);
				item_content.append($('<br style="clear: both;"/>'))
			}
		}

		var contents_area = $('.contents');
		contents_area.empty();
		contents_area.append(player_content);
		contents_area.append(item_content);
		
		$('.client-prompt').focus();
	},
	function write(self, text, error, escape){
		/*
		 * Called by the server to output a line to the action pane.
		 */
		var actions = $('#actions');
		
		if(typeof(escape) == 'undefined'){
			escape = true;
		}
		
		if(escape){
			while(text.indexOf('<') != -1)
				text = text.replace('<', '&lt;');
			
			while(text.indexOf('>') != -1)
				text = text.replace(">", '&gt;')
			
			while(text.indexOf("\n") != -1)
				text = text.replace("\n", '<br/>')
			
			while(text.indexOf('  ') != -1)
				text = text.replace('  ', '&nbsp;&nbsp;')
		}
		
		if(error){
			actions.append('<br/><span class="error-response">' + text + '</span>');
		}
		else{
			actions.append('<br/>' + text);
		}
		
		actions.scrollTo('max');
	},
	function logout(self){
		/*
		 * Called by the server to logout the user.
		 */
		window.location = '/logout';
		return true;
	}
);

var plugin_installs = {};
