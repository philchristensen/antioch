var commandHistory = [];
var historyPosition = -1;
var currentCommand = ''

function getConnector(){
	/*
	 * Return the Athena connection to the server.
	 */
	var element = document.getElementById('athenaid:1-client-connector');
	return Nevow.Athena.Widget.get(element);
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

function init(){
	jQuery.getScript('/assets/js/jquery.scrollTo-1.4.2-min.js');
	jQuery.getScript('/assets/js/jquery.dimensions-1.1.2-min.js', function(data, status){
		jQuery.getScript('/assets/js/jquery.splitter-1.5.1.js', function(data, status){
			$('#client-wrapper').splitter({
				type: 'h',
				anchorToWindow: true,
				sizeTop: true
			});
			$('#bottom-pane').splitter({
				type: 'h',
			});
		});
	});
	
	$('.client-prompt').keyup(handleKeyEvent);
	
	$('.look-me').click(function(){
		look('me');
	});
	
	$('.look-here').click(function(){
		look('here');
	});
}