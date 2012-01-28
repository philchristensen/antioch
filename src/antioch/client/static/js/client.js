(function($) {
	var commandHistory = [];
	var historyPosition = -1;
	var currentCommand = ''
	
	var methods = {
		init: function(options){ 
			// Create some defaults, extending them with any options that were provided
			var settings = $.extend({
				
			}, options);
			
			return this.each(function(){
				function handleMessages(msgs){
					for(index in msgs){
						msg = msgs[index];
						if(msg.command == 'observe'){
							methods.setObservations(msg.observations);
						}
						else if(msg.command == 'write'){
							methods.write(msg.text, msg.is_error, msg.escape_html);
						}
					}
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
				
				// $('#client-wrapper').splitter({
				// 	type: 'h',
				// 	anchorToWindow: true,
				// 	sizeTop: true
				// });
				// $('#bottom-pane').splitter({
				// 	type: 'h',
				// });
				
				$(this).keyup(handleKeyEvent);
				
				setTimeout(function() {
					listen(handleMessages);
				}, 500);
			});
		},
		
		callRemote: function(command, options, callback){
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
		},
		
		parse: function(text){
			/*
			 * Send a command to the server.
			 */
			methods.callRemote('parse', {sentence: text});
			var actions = $('#actions');
			actions.append('<br/><span class="issued-command">' + text + '</span>')
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
				actions.append('<br/><span class="error-response">' + text + '</span>');
			}
			else{
				actions.append('<br/>' + text);
			}
			
			actions.scrollTo('max');
		},
		
		setObservations: function(observations){
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
			
			$(this).focus();
		}
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
