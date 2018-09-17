# antioch
# Copyright (c) 1999-2018 Phil Christensen
#
#
# See LICENSE for details



import logging

from celery import shared_task
from celery.utils.log import get_task_logger

from django.conf import settings
from django.db import connection

from antioch.core import code, exchange, errors, parser
from antioch.util import sql, ason

log = get_task_logger(__name__)

def get_exchange(ctx=None):
    """
    Get an ObjectExchange instance for the provided context.
    """
    if(ctx):
        return exchange.ObjectExchange(connection, queue=True, ctx=ctx)
    else:
        return exchange.ObjectExchange(connection)

@shared_task
def authenticate(username, password, ip_address):
    """
    Return the user id for the username/password combo, if valid.
    """
    with get_exchange() as x:
        connect = x.get_verb(1, 'connect')
        if(connect):
            connect(ip_address)

        authentication = x.get_verb(1, 'authenticate')
        if(authentication):
            u = authentication(username, password, ip_address)
            if(u):
                return {'user_id': u.get_id()}
        try:
            u = x.get_object(username)
            if not(u):
                raise errors.PermissionError("Invalid login credentials. (2)")
        except errors.NoSuchObjectError as e:
            raise errors.PermissionError("Invalid login credentials. (3)")
        except errors.AmbiguousObjectError as e:
            raise errors.PermissionError("Invalid login credentials. (4)")

        multilogin_accounts = x.get_property(1, 'multilogin_accounts')
        if(u.is_connected_player()):
            if(not multilogin_accounts or u not in multilogin_accounts.value):
                raise errors.PermissionError('User is already logged in.')

        if not(u.validate_password(password)):
            raise errors.PermissionError("Invalid login credentials. (6)")

    return {'user_id': u.get_id()}

@shared_task
def login(user_id, session_id, ip_address):
    """
    Register a login for the provided user_id.
    """
    with get_exchange(user_id) as x:
        x.login_player(user_id, session_id)

        system = x.get_object(1)
        if(system.has_verb("login")):
            system.login()
        log.info('user #%s logged in from %s' % (user_id, ip_address))

    return {'response': True}

@shared_task
def logout(user_id):
    """
    Register a logout for the provided user_id.
    """
    # we want to make sure to logout the user even
    # if the logout verb fails
    with get_exchange(user_id) as x:
        x.logout_player(user_id)

    with get_exchange(user_id) as x:
        system = x.get_object(1)
        if(system.has_verb("logout")):
            system.logout()
        log.info('user #%s logged out' % user_id)

    return {'response': True}

@shared_task
def parse(user_id, sentence):
    """
    Parse a command sentence for the provided user_id.
    """
    with get_exchange(user_id) as x:
        caller = x.get_object(user_id)

        log.info('%s: %s' % (caller, sentence))
        parser.parse(caller, sentence)

    return {'response': True}

@shared_task
def registertask(user_id, delay, origin_id, verb_name, args, kwargs):
    """
    Register a delayed task for the provided user_id.
    """
    with get_exchange(user_id) as x:
        try:
            task_id = x.register_task(user_id, delay, origin_id, verb_name, args, kwargs)
        except Exception as e:
            print(e)
            raise e

    return {'task_id': task_id}

@shared_task
def runtask(user_id, task_id):
    """
    Run a task for a particular user.
    """
    with get_exchange(user_id) as x:
        task = x.get_task(task_id)
        if(not task or task['killed']):
            return {'response': False}

        origin = x.get_object(task['origin_id'])
        args = json.loads(task['args'])
        kwargs = json.loads(task['kwargs'])

        v = origin.get_verb(task['verb_name'])
        v(*args, **kwargs)

    return {'response': True}

@shared_task
def iteratetasks():
    """
    Run one waiting task, if possible.
    """
    # note this is a 'superuser exchange'
    # should be fine, since all iterate_task does
    # is create another subprocess for the proper user
    with get_exchange() as x:
        task = x.iterate_task(self)

    return {'response':task}