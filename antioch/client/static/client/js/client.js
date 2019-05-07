if(!window.console){
  console = {
    log: function(x){
    }
  }
}

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
        comet_url: "/api/exec/messages/",
        rest_url: "/api/exec/",
        
        callback: function(){
          // methods.write('Connected...');
        },
        
        error_handler: function(err){
          methods.write(err, true, true);
        },
        
        observation_template: "<div class=\"jumbotron\"></span>",
        issued_command_template: "<div class=\"alert alert-warning issued-command\"><div class=\"date-container\"></div>$content</div>",
        error_template: "<div class=\"alert alert-danger received-error\"><div class=\"date-container\"></div>$content</div>",
        message_template: "<div class=\"panel panel-info received-message\"><div class=\"panel-body date-container\">$content</div></div>",
        
        // // The rest of these settings are defined in the client template
        // // when the plugin is instantiated, keeping all template-related
        // // code together. The setting names are also listed here:
        //
        // issued_command_template    actions_selector
        // error_template       name_selector
        // message_template       description_selector
        // player_image_template    contents_selector
        // 
        // players_wrapper_node     player_name_node
        // contents_wrapper_node    player_mood_node
        // players_list_node      people_here_node
        // contents_list_node     contents_here_node
        // player_image_node      clear_both_node
        // default_image_node     player_list_item_node
        // content_list_item_node
      }, options);
      
      return this.each(function(){
        function listen(handler){
          $.ajax({
            method: 'GET',
            url: settings.comet_url,
            contentType: "application/json",
            cache: false,
            error:    function(jqXHR, textStatus, errorThrown){
              if(textStatus == 'timeout'){
                listen(handler);
              }
              else if(textStatus != 'abort'){
                if(errorThrown){
                  settings.error_handler('Error in listen: ' + errorThrown);
                }
                else{
                  settings.error_handler('Error in listen: Server Gone');
                }
              }
            },
            success: function(data, textStatus, jqXHR){
              handler(data);
              setTimeout(function(){
                listen(handler);
              }, 1);
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
            settings.callback()
          }, 500);
        }
        else{
          settings.callback();
        }
      });
    },
    
    logAction: function(content){
      var d = new Date();
      var real_date = $('<div class="real-date d-none">').html(d.toString());
      var relative_date = $('<div class="relative-date">');
      var date = $('<h6 class="date keep-relative">').append(real_date).append(relative_date);
      content = $(content);
      content.css('display', 'none').find('.date-container').prepend(date);
      $('#actions').prepend(content);
      content.queue(function(next){
        //$(this).show('slide', { direction: "up" }, 500);
        $(this).slideDown('fast');
        next();
      });
    },
    
    callRemote: function(command, options, callback){
      $.ajax({
        method: 'POST',
        url: settings.rest_url + command + '/command/',
        contentType: "application/json",
        data: JSON.stringify(options),
        headers: {
          'X-CSRFToken': Cookies.get('csrftoken')
        },
        error:    function(jqXHR, textStatus, errorThrown){
          if(errorThrown){
            settings.error_handler('Error in callRemote: ' + errorThrown);
          }
          else{
            settings.error_handler('Error in callRemote: Server Gone');
          }
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
      // var actions = $(settings.actions_selector);
      // methods.logAction(settings.issued_command_template.replace('$content', text))
    },
    
    look: function(item){
      methods.parse('look ' + item);
    },
    
    write: function(text, error, escape){
      /*
       * Called by the server to output a line to the action pane.
       */
      if(typeof(escape) == 'undefined'){
        escape = true;
      }
      
      if(escape){
        text = $('<div>').text(text).html();
        text = text.replace(/^\s\s\s\s/gm, '&nbsp;&nbsp;&nbsp;&nbsp;');
        text = text.replace(/\n/g, '<br>');
      }
      
      if(error){
        text = settings.error_template.replace('$content', text);
      }
      else{
        text = settings.message_template.replace('$content', text);
      }
      methods.logAction(text);
    },
    
    setObservations: function(observations){
      /*
       * Called by the server to change the main client display.
       */
      $('.window-title').html(observations['name'])
      
      var t = $(settings.observation_template);
      // t.append($('<h3 class="name">').html(observations['name']));
      t.append($('<p class="lead description">').html(observations['description']));
      
      var player_content = $(settings.players_wrapper_node);
      var item_content = $(settings.contents_wrapper_node);
      
      if(observations['contents'].length){
        var player_list = $(settings.players_list_node);
        var contents_list = $(settings.contents_list_node);
        
        for(index in observations['contents']){
          (function(details){
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
          })(observations['contents'][index]);
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
      
      t.append(player_content);
      t.append(item_content);
      
      $('#observations').empty();
      $('#observations').append(t);
      
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
    console.log(msg)
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
