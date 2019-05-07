# antioch
# Copyright (c) 1999-2019 Phil Christensen
#
#
# See LICENSE for details

"""
Django client views.
"""

import logging

from django import shortcuts
from django.contrib.auth.decorators import login_required

from antioch import plugins
from antioch.core import tasks

log = logging.getLogger(__name__)

@login_required
def client(request):
    """
    Return the main client window.
    """
    return shortcuts.render(request, 'client/client.html', dict(
        title           = "antioch client",
        scripts         = [p.script_url for p in plugins.iterate() if p and p.script_url],
    ))

def logout(request):
    """
    Logout of antioch.
    """
    tasks.logout.delay(request.user.avatar.id)
    auth.logout(request)
    return shortcuts.redirect('client:client')
