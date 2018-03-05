# antioch
# Copyright (c) 1999-2017 Phil Christensen
#
#
# See LICENSE for details

"""
Client-side prompt support.
"""
from zope.interface import provider

from antioch import IPlugin

def ask(p, question, callback, *args, **kwargs):
    details = dict(
        question    = question,
    )
    p.exchange.send_message(p.caller.get_id(), dict(
        command        = 'ask',
        details        = details,
        callback    = dict(
            origin_id    = callback.get_origin().get_id(),
            verb_name    = callback.get_names()[0],
            args        = args,
            kwargs        = kwargs,
        )
    ))

@provider(IPlugin)
class AskPlugin(object):
    script_url = '/static/js/ask-plugin.js'
    
    def get_environment(self):
        return dict(
            ask = ask,
        )

