default_window_settings = {
	menubar: 'no',
	status: 'no',
	toolbar: 'no',
	location: 'no',
	directories: 'no',
	resizable: 'yes',
	scrollbars: 'auto',
	width: null,
	height: null,
}

function inspect(obj){
	var output = '';
	for(p in obj){
		if(!(obj[p] instanceof Function)){
			output += p + ': ' + obj[p] + "\n";
		}
	}
	alert(output);
}

function alertFailure(failure){
	alert(failure.error);
}

function buildWindowString(attribs){
	output = [];
	for(key in default_window_settings){
		setting = key + '='
		if(attribs[key]){
			setting += attribs[key];
		}
		else{
			setting += default_window_settings[key];
		}
		output.push(setting);
	}
	return output.join(',');
}