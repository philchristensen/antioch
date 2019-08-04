# antioch
# Copyright (c) 1999-2019 Phil Christensen
#
#
# See LICENSE for details

"""
Provide the verb execution environment
"""

import time
import sys
import os.path
import logging
import argparse
import shlex

from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_builtins
from RestrictedPython.Guards import guarded_unpack_sequence
from antioch.core import errors
from antioch.util import ason

allowed_modules = (
    'hashlib',
    'string',
)

pylog = logging.getLogger(__name__)

argparser = argparse.ArgumentParser(prog='antioch',
    description="Configure antioch attribute deployment.")
argparser.add_argument('type', type=str, choices=['verb', 'property'],
    help="The kind of attribute being deployed.")
argparser.add_argument('name', type=str,
    help="The name of the attribute being deployed.")
argparser.add_argument('origin', type=str,
    help="An object reference for the origin of this attribute.")
argparser.add_argument('--owner', type=str, required=True,
    help="An object reference for the owner of this object.")
argparser.add_argument('--ability', action='store_true',
    help="This is an intrinsic ability of the origin.")
argparser.add_argument('--method', action='store_true',
    help="This is a programmable method of the origin.")
argparser.add_argument('--access-group', type=str, nargs="*",
    help="Allow or deny a group a certain permission on this attribute.")
argparser.add_argument('--access-object', type=str, nargs="*",
    help="Allow or deny a specific object a certain permission on this attribute.")

def is_frame_access_allowed():
    """
    Used by get/setattr to delegate access.
    
    Returns True if the call to __getattribute__ or __setattr__ originated
    in either the exchange, test, or bootstrap modules.
    
    Previously this used inspect, which made it super slow. The only potential
    issue with using _getframe() is that it's not guaranteed to be there in
    non CPython implementations.
    """
    f = sys._getframe(1)
    c1 = f.f_back.f_code
    c2 = f.f_back.f_back.f_code
    
    calling_filename = os.path.abspath(c2.co_filename)
    try:
        from antioch.core import interface
        model_source_path = os.path.abspath(interface.__file__)
        if(model_source_path.endswith('pyc')):
            model_source_path = model_source_path[:-1]
        if(calling_filename == model_source_path):
            # pylog.debug('%r =(1)= %r' % (c2.co_filename, model_source_path))
            return True
        
        from antioch.core import exchange
        exchange_source_path = os.path.abspath(exchange.__file__)
        if(exchange_source_path.endswith('pyc')):
            exchange_source_path = exchange_source_path[:-1]
        if(calling_filename == exchange_source_path):
            # pylog.debug('%r =(2)= %r' % (c2.co_filename, exchange_source_path))
            return True
        
        from antioch import test
        test_source_path = os.path.abspath(os.path.dirname(test.__file__))
        if(calling_filename.startswith(test_source_path)):
            # pylog.debug('%r 1startswith %r' % (c2.co_filename, test_source_path))
            return True
        
        from antioch.core import bootstrap
        bootstrap_source_path = os.path.abspath(os.path.dirname(bootstrap.__file__))
        if(calling_filename.startswith(bootstrap_source_path)):
            # pylog.debug('%r 2startswith %r' % (c2.co_filename, bootstrap_source_path))
            return True
        
        pylog.warning('secured access %r != %r' % (c2.co_filename,model_source_path))
        return False
    finally:
        del c2
        del c1
        del f

def massage_verb_code(code):
    """
    Take a given piece of verb code and wrap it in a function.
    
    This allows support of 'return' within verbs, and for verbs to return values.
    """
    code = code.replace('\r\n', '\n')
    code = code.replace('\n\r', '\n')
    code = code.replace('\r', '\n')
    code = '\n'.join(
        ['def verb():'] +
        ['\t' + x for x in code.split('\n') if x.strip()] +
        ['returnValue = verb()']
    )
    return code

def parse_deployment(source):
    if not source.startswith("#!antioch"):
        raise ValueError("Source code does not begin with antioch shebang.")
    shebang = ''
    for line in source.splitlines():
        line = line.strip()
        if line.startswith('#'):
            line = line[1:]
        else:
            break
        if not line.endswith('\\'):
            shebang += line
            break
        else:
            shebang += ' '
            shebang += line[:-1]
    return argparser.parse_args(shlex.split(shebang[1:])[1:])

def r_eval(caller, src, environment={}, filename='<string>', runtype="eval"):
    """
    Evaluate an expression in the provided environment.
    """
    def _writer(s, is_error=False):
        if(s.strip()):
            write(environment.get('parser'))(caller, s, is_error=is_error)
    
    env = get_restricted_environment(_writer, environment.get('parser'))
    env['runtype'] = runtype
    env['caller'] = caller
    env.update(environment)
    
    code = compile_restricted(src, filename, 'eval')
    try:
        value =  eval(code, env)
    except errors.UsageError as e:
        if(caller):
            _writer(str(e), is_error=True)
        else:
            raise e
    
    return value

def r_exec(caller, src, environment={}, filename='<string>', runtype="exec"):
    """
    Execute an expression in the provided environment.
    """
    def _writer(s, is_error=False):
        if(s.strip()):
            write(environment.get('parser'))(caller, s, is_error=is_error)
    
    env = get_restricted_environment(_writer, environment.get('parser'))
    env['runtype'] = runtype
    env['caller'] = caller
    env.update(environment)
    
    code = compile_restricted(massage_verb_code(src), filename, 'exec')
    try:
        exec(code, env)
    except errors.UsageError as e:
        if(caller):
            _writer(str(e), is_error=True)
        else:
            raise e
    
    if("returnValue" in env):
        return env["returnValue"]

def restricted_import(name, gdict, ldict, fromlist, level=-1):
    """
    Used to drastically limit the importable modules.
    """
    if(name in allowed_modules):
        return __builtins__['__import__'](name, gdict, ldict, fromlist, level)
    raise ImportError('Restricted: %s' % name)

def get_protected_attribute(obj, name, g=getattr):
    if(name.startswith('_') and not is_frame_access_allowed()):
        raise AttributeError(name)
    return g(obj, name)

def set_protected_attribute(obj, name, value, s=setattr):
    if(name.startswith('_') and not is_frame_access_allowed()):
        raise AttributeError(name)
    return s(obj, name, value)

def inplace_var_modification(operator, a, b):
    if(operator == '+='):
        return a+b
    raise NotImplementedError("In-place modification with %s not supported." % operator)

def get_restricted_environment(writer, p=None):
    """
    Given the provided parser object, construct an environment dictionary.
    """
    class _print_(object):
        def _call_print(self, s):
            writer(s)
    
    class _write_(object):
        def __init__(self, obj):
            object.__setattr__(self, 'obj', obj)
        
        def __setattr__(self, name, value):
            """
            Private attribute protection using is_frame_access_allowed()
            """
            set_protected_attribute(self.obj, name, value)
        
        def __setitem__(self, key, value):
            """
            Passthrough property access.
            """
            self.obj[key] = value
    
    safe_builtins['__import__'] = restricted_import
    
    for name in ['dict', 'getattr', 'hasattr']:
        safe_builtins[name] = __builtins__[name]
    
    env = dict(
        _apply_           = lambda f,*a,**kw: f(*a, **kw),
        _print_           = lambda x: _print_(),
        _write_           = _write_,
        _getattr_         = get_protected_attribute,
        _getitem_         = lambda obj, key: obj[key],
        _getiter_         = lambda obj: iter(obj),
        _inplacevar_      = inplace_var_modification,
        _unpack_sequence_ = guarded_unpack_sequence,
        __import__        = restricted_import,
        __builtins__      = safe_builtins,
    )
    
    from antioch import plugins
    for plugin in plugins.iterate():
        for name, func in list(plugin.get_environment().items()):
            if(hasattr(func, 'im_func')):
                func.__func__.__name__ = name
            else:
                func.__name__ = name
            api(func) if callable(func) else None
    
    for name, func in list(api.locals.items()):
        env[name] = func(p)
    
    for name in dir(errors):
        if not(name.endswith('Error')):
            continue
        cls = getattr(errors, name)
        env[name] = cls
    
    return env

def run_system_verb(exchange, verb_name, *args, **kwargs):
    origin = exchange.get_object(1)
    verb = origin.get_verb(verb_name)
    return verb(*args, **kwargs)

def api(func):
    """
    Bless a function into the verb API.
    """
    def _api(p):
        def __api(*args, **kwargs):
            return func(p, *args, **kwargs)
        return __api
    
    api.locals = getattr(api, 'locals', {})
    api.locals[func.__name__] = _api
    
    return _api

@api
def task(p, delay, origin, verb_name, *args, **kwargs):
    """
    Verb API: queue up a new task.
    """
    # remind me again why we can't do this?
    from antioch.core import tasks
    tasks.registertask.delay(
        user_id        = p.caller.id,
        delay        = str(delay),
        origin_id    = str(origin.id),
        verb_name    = str(verb_name),
        args        = json.dumps(args),
        kwargs        = json.dumps(kwargs),
    )
    
    # #force exception here if undumpable
    # p.exchange.send_message(p.caller, dict(
    #     command        = 'task',
    #     delay        = int(delay),
    #     origin        = str(origin),
    #     verb_name    = str(verb_name),
    #     args        = json.dumps(args),
    #     kwargs        = json.dumps(kwargs),
    # ))

@api
def execute(p, code):
    """
    Verb API: Execute the code in place.
    """
    return r_exec(p.caller, code, p.get_environment())


@api
def evaluate(p, code):
    """
    Verb API: Evalue the expression in place.
    """
    return r_eval(p.caller, code, p.get_environment())

@api
def tasks(p):
    """
    Verb API: Return a list of tasks for this user, or all tasks.
    """
    if(p.caller.is_wizard()):
        return p.exchange.get_tasks()
    else:
        return p.exchange.get_tasks(user_id=p.caller.get_id())

@api
def write(p, user, text, is_error=False, escape_html=True):
    """
    Verb API: Print a string of text to the user's console.
    """
    p.exchange.send_message(user.get_id(), dict(
        command        = 'write',
        text        = str(text),
        is_error    = is_error,
        escape_html    = escape_html,
    ))

@api
def log(p, text, is_error=False):
    """
    Verb API: Print a string of text to the server's console.
    """
    if p.caller and not(p.caller.is_wizard()):
        return
    if(is_error):
        pylog.error(text)
    else:
        pylog.info(text)

@api
def broadcast(p, text, escape_html=True):
    """
    Verb API: Print a string to the console of everyone nearby.
    """
    if(p.caller.location is None):
        return
    for obj in p.caller.location.get_contents():
        p.exchange.send_message(obj.get_id(), dict(
            command        = 'write',
            text        = str(text),
            is_error    = False,
            escape_html    = escape_html,
        ))

@api
def observe(p, user, observations):
    """
    Verb API: Send a dict of observations to the user's client.
    """
    p.exchange.send_message(user.get_id(), dict(
        command            = 'observe',
        observations    = observations,
    ))

@api
def count_named(p, key):
    """
    Verb API: Get the total number of objects sharing a global name or ID.
    """
    return p.exchange.refs(key)

@api
def get_object(p, key, return_list=False):
    """
    Verb API: Load an object by its global name or ID.
    """
    return p.exchange.get_object(key, return_list=return_list)

@api
def create_object(p, name, unique_name=False):
    """
    Verb API: Create a new object.
    """
    # this method can be run from system.authenticate() to implement
    # guest support, so it has to work when p.caller == None
    owner_id = p.caller.get_id() if p.caller else None
    return p.exchange.instantiate('object', name=name, unique_name=unique_name, owner_id=owner_id)

@api
def get_last_client_ip(p, player):
    """
    Verb API: Get the last IP address used by the given player.
    
    [ACL] allowed to administer player
    """
    p.caller.is_allowed('administer', player, fatal=True)
    return p.exchange.get_last_client_ip(player.get_id())