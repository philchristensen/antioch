import sys, re, time

from django.utils import termcolors

styles = dict(
	ERROR = termcolors.make_style(fg='red', opts=['bold']),
	WARNING = termcolors.make_style(fg='yellow', opts=['bold']),
	INFO = termcolors.make_style(fg='cyan'),
	DEBUG = termcolors.make_style(fg='blue'),
)

class DjangoColorFormatter(object):
	def __init__(self, logformat=None, datefmt=None):
		self.logformat = logformat if logformat else '[%(asctime)s] %(levelname)s: %(msg)s'
		self.datefmt = datefmt if datefmt else '%d/%b/%Y %H:%M:%S'
	
	def format(self, log):
		supports_color = True
		unsupported_platform = (sys.platform in ('win32', 'Pocket PC'))
		is_a_tty = hasattr(sys.__stdout__, 'isatty') and sys.__stdout__.isatty()
		
		result = self.logformat % dict(
			asctime = time.strftime(self.datefmt, time.gmtime(log.created)),
			**log.__dict__
		)
		
		if log.levelname not in styles or unsupported_platform or not is_a_tty:
			return result
		else:
			return styles[log.levelname](result)

