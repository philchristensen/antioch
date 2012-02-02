(function($) {
	var commandHistory = [];
	var historyPosition = -1;
	var currentCommand = ''
	
	var settings;
	
	var messageListeners = {
		observe: [
			function(msg){
				methods.setObservations(msg.observations);
			}
		],
		write: [
			function(msg){
				methods.write(msg.text, msg.is_error, msg.escape_html);
			}
		]
	}
	
	var methods = {
		init: function(options){
			// Create some defaults, extending them with any options that were provided
			settings = $.extend({
				listen: false,
				comet_url: "/comet/",
				rest_url: "/rest/",
				error_handler: function(err){
					alert(err);
				},
				// // The rest of these settings are defined in the client template
				// // when the plugin is instantiated, keeping all template-related
				// // code together. The setting names are also listed here:
				//
				// issued_command_template      actions_selector
				// error_template               name_selector
				// message_template             description_selector
				// player_image_template        contents_selector
				// 
				// players_wrapper_node         player_name_node
				// contents_wrapper_node        player_mood_node
				// players_list_node            people_here_node
				// contents_list_node           contents_here_node
				// player_image_node            clear_both_node
				// default_image_node           player_list_item_node
				// content_list_item_node
			}, options);
			
			return this.each(function(){
				function listen(handler){
					$.ajax(settings.comet_url, {
						dataType: 'json',
						contentType: 'application/json',
						cache: false,
						error:	function(jqXHR, textStatus, errorThrown){
							if(textStatus == 'timeout'){
								listen(handler);
							}
							else if(textStatus != 'abort'){
								settings.error_handler('Error in listen: ' + errorThrown);
							}
						},
						success: function(data, textStatus, jqXHR){
							handler(data);
							listen(handler);
						}
					});
				}
				
				function handleKeyEvent(event){
					/*
					 * Command-line key handler.
					 */
					switch(event.which){
						case 13:
							var command = event.target.value;
							if(command){
								methods.parse(command);
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
				
				$(this).keyup(handleKeyEvent);
					
				if(settings.listen){
					setTimeout(function() {
						listen(function(msgs){
							for(index in msgs){
								msg = msgs[index];
								methods.handleMessage(msg);
							}
						});
					}, 500);
				}
			});
		},
		
		callRemote: function(command, options, callback){
			$.ajax(settings.rest_url + command, {
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
		},
		
		parse: function(text){
			/*
			 * Send a command to the server.
			 */
			methods.callRemote('parse', {sentence: text});
			var actions = $(settings.actions_selector);
			actions.append(settings.issued_command_template.replace('$content', text))
			actions.scrollTo('max');
		},
		
		look: function(item){
			methods.parse('look ' + item);
		},
		
		write: function(text, error, escape){
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
				actions.append(settings.error_template.replace('$content', text));
			}
			else{
				actions.append(settings.message_template.replace('$content', text));
			}
			
			actions.scrollTo('max');
		},
		
		setObservations: function(observations){
			/*
			 * Called by the server to change the main client display.
			 */
			$(settings.name_selector).html(observations['name']);
			$(settings.description_selector).html(observations['description']);
			
			var player_content = $(settings.players_wrapper_node);
			var item_content = $(settings.contents_wrapper_node);
			
			if(observations['contents'].length){
				var player_list = $(settings.players_list_node);
				var contents_list = $(settings.contents_list_node);
				
				for(index in observations['contents']){
					var details = observations['contents'][index];
					if(details.type){
						image_div = ($(settings.player_image_node));
						if(details.image){
							image_div.append($(settings.player_image_template.replace('$content', details.image)));
						}
						else{
							image_div.append($(settings.default_image_node));
						}
						
						name_div = $(settings.player_name_node);
						name_div.html(details.name);
						
						list_item = $(settings.player_list_item_node);
						list_item.click(function(){
							methods.look(details.name);
						});
						list_item.append(image_div);
						list_item.append(name_div);
						
						if(details.mood){
							mood_div = $(settings.player_mood_node);
							mood_div.html(details.mood);
							list_item.append(mood_div);
						}
						player_list.append(list_item);
					}
					else{
						list_item = $(settings.content_list_item_node);
						list_item.html(details.name);
						list_item.click(function(){
							methods.look(details.name);
						});
						contents_list.append(list_item);
					}
				}
				
				if(player_list[0].children.length){
					player_content.append($(settings.people_here_node));
					player_content.append(player_list);
					player_content.append($(settings.clear_both_node))
				}
				if(contents_list[0].children.length){
					item_content.append($(settings.contents_here_node));
					item_content.append(contents_list);
					item_content.append($(settings.clear_both_node))
				}
			}
			
			var contents_area = $(settings.contents_selector);
			contents_area.empty();
			contents_area.append(player_content);
			contents_area.append(item_content);
			
			$(this).focus();
		},
		
		addMessageListener: function(command, listener){
			if(messageListeners[command]){
				messageListeners[command].push(listener);
			}
			else{
				messageListeners[command] = [listener];
			}
		},
		
		handleMessage: function(msg){
			handlers = messageListeners[msg['command']];
			if(handlers){
				for(index in handlers){
					handlers[index](msg);
				}
			}
			else{
				console.log("No handler found for command " + msg['command']);
			}
		},
	};
	
	$.fn.antioch = function(method){
		if(methods[method]){
			return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
		}
		else if(typeof method === 'object' || !method){
			return methods.init.apply(this, arguments);
		}
		else{
			$.error('Method ' +  method + ' does not exist on jQuery.antioch');
		}
	};
})(jQuery);
