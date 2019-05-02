# antioch
# Copyright (c) 1999-2019 Phil Christensen
#
#
# See LICENSE for details

"""
Django client views.
"""

import os.path, time, logging

from django import template, shortcuts, http
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.middleware import csrf
from django.views.decorators.csrf import csrf_exempt

import json

from antioch import plugins, celery_config
from antioch.core import parser, tasks

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

@login_required
def comet(request):
    """
    Check for messages for this user.
    """
    queue_id = '-'.join([settings.USER_QUEUE, str(request.user.avatar.id)])
    log.debug("checking for messages for %s" % queue_id)

    with celery_config.app.default_connection() as conn:
        from kombu import simple, Exchange, Queue
        exchange = Exchange('antioch',
            type            = 'direct',
            auto_delete     = False,
            durable         = True,
        )
        channel = conn.channel()
        unbound_queue = Queue(queue_id,
            exchange        = exchange,
            routing_key     = queue_id,
            auto_delete     = False,
            durable         = False,
            exclusive       = False,
        )
        queue = unbound_queue(channel)
        queue.declare()

        sq = simple.SimpleBuffer(channel, queue, no_ack=True)
        try:
            msg = sq.get(block=True, timeout=10)
            messages = [msg.body.decode()]
        except sq.Empty as e:
            messages = []
        sq.close()
    
    log.debug('returning to client: %s' % messages)
    return http.HttpResponse('[%s]' % ','.join(messages), content_type="application/json")

@login_required
@csrf_exempt
def rest(request, command):
    """
    Query the appserver and wait for a response.
    """
    kwargs = json.loads(request.read())

    task = getattr(tasks, command)
    result = task.delay(request.user.avatar.id, **kwargs)
    data = result.get(timeout=settings.JOB_TIMEOUT)
    response = json.dumps(data)

    return http.HttpResponse(response, content_type="application/json")

def logout(request):
    """
    Logout of antioch.
    """
    tasks.logout.delay(request.user.avatar.id)
    auth.logout(request)
    return shortcuts.redirect('client:client')
