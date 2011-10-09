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
	if(failure.error.stack){
        var frames = failure.parseStack();
        var ret = [];
        for (var i = 0; i < frames.length; ++i) {
            var f = frames[i];
            if (f.fname == "" && f.lineNumber == 0) {
                // ret.pop();
                continue;
            }
            else if(f.func.indexOf('_startRunCallbacks') != -1) {
                continue;
            }
            else if(f.func.indexOf('_runCallbacks') != -1) {
                continue;
            }
            var parts = f.fname.split('/');
            f.fname = parts.slice(parts.length - 2).join('/');
            
            ret.push(f);
        }
		alert(failure.toPrettyText(ret));
	}
	else{
		alert(failure.toString() + ' (No traceback available)');
	}
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