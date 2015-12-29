# antioch
# Copyright (c) 1999-2016 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Log customization support.
"""

import sys, time

from django.utils import termcolors

styles = dict(
    ERROR = termcolors.make_style(fg='red', opts=['bold']),
    WARNING = termcolors.make_style(fg='yellow', opts=['bold']),
    INFO = termcolors.make_style(fg='cyan'),
    DEBUG = termcolors.make_style(fg='blue'),
)

class DjangoColorFormatter(object):
    """
    Colorize log output when outputting to a terminal.
    """
    def __init__(self, logformat=None, datefmt=None):
        """
        Create a formatter with the provided formats.
        """
        self.logformat = logformat if logformat else '[%(asctime)s] %(levelname)s: %(msg)s'
        self.datefmt = datefmt if datefmt else '%d/%b/%Y %H:%M:%S'
    
    def format(self, log):
        """
        Format a message.
        """
        supports_color = True
        unsupported_platform = (sys.platform in ('win32', 'Pocket PC'))
        is_a_tty = hasattr(sys.__stdout__, 'isatty') and sys.__stdout__.isatty()
        
        try:
            msg = log.msg % log.args
        except:
            msg = '%s %s' % (log.msg, log.args)
        
        result = self.logformat % dict(
            name = log.name,
            asctime = time.strftime(self.datefmt, time.gmtime(log.created)),
            levelname = log.levelname,
            pathname = log.pathname,
            funcName = log.funcName,
            lineno = log.lineno,
            msg = msg,
            thread = log.thread,
            threadName = log.threadName,
            process = log.process,
            processName = log.processName,
        )
        
        if log.levelname not in styles or unsupported_platform or not is_a_tty:
            return result
        else:
            return styles[log.levelname](result)
