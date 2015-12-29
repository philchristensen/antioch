// Loaded in the client window automatically
(function($) {
    $(document).antioch('addMessageListener', 'ask', function(msg){
        var response = prompt(msg.details.question);
        var callback = msg.callback;
        callback.args.push(response);
        $(document).antioch('callRemote', 'registertask', {
            delay:      0,
            origin_id:  callback.origin_id.toString(),
            verb_name:  callback.verb_name,
            args:       JSON.stringify(callback.args),
            kwargs:     JSON.stringify(callback.kwargs),
        });
    });
})(jQuery);
