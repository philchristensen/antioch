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
