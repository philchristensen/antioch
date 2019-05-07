# antioch
# Copyright (c) 1999-2019 Phil Christensen
#
#
# See LICENSE for details

"""
Custom authentication backend
"""

import logging, traceback, crypt

from django.contrib.auth import backends
from django.conf import settings
from django.db import connection

from rest_framework import permissions

from . import models, exchange

log = logging.getLogger(__name__)

ACTION_MAPS = {
    'object': {
        'retrieve': 'read',
        'destroy': 'write',
        'update': 'write',
        'partial_update': 'write'
    },
}

class AntiochPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        ex = exchange.ObjectExchange(connection, ctx=request.user.avatar.pk)
        user = ex.get_object(request.user.avatar.pk)
        obj = ex.load(view.basename, obj.pk)
        action = 'read' if view.action == 'retrieve' else 'write'
        return ex.is_allowed(user, action, obj)

class AntiochObjectBackend(backends.ModelBackend):
    """
    Authenticate against the antioch object database.
    """
    def authenticate(self, request, username=None, password=None):
        """
        Attempt to authenticate the provided request with the given credentials.
        """
        try:
            p = models.Player.objects.filter(
                avatar__name__iexact = username,
                enabled = True
            )[:1]
            
            if not(p):
                log.error("Django auth failed.")
                return None
            
            p = p[0]
            if(p.crypt != crypt.crypt(password, p.crypt[0:2])):
                return None
            
            log.info('%s logged in' % p.avatar)
            return p
        except models.Player.DoesNotExist:
            log.error("Player auth failed.")
            return None
        except Exception as e:
            log.error("Error in authenticate(): %s" % traceback.format_exc())

    def get_user(self, user_id):
        """
        Return the user object represented by user_id
        """
        try:
            p = models.Player.objects.get(pk=user_id)
            if(p):
                return p
            return None
        except models.Player.DoesNotExist:
            return None

