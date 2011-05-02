import re

import termcolor

from twisted.python import log

child_msg = re.compile(r'^FROM (?P<child_id>\d+)(:.*?)(?P<msg>\[(.*?)\] .*?)$')

def customizeLogs():
	log.originalTextFromEventDict = log.textFromEventDict
	log.textFromEventDict = textFromEventDict

def colorizeChild(child_id, msg):
	colors = ['red', 'green', 'blue', 'yellow', 'magenta', 'cyan']
	return termcolor.colored(msg, colors[child_id % len(colors)])

def textFromEventDict(e):
	try:
		msg = e['message']
		if(msg):
			match = child_msg.match(e['message'][0])
			if not(match):
				return log.originalTextFromEventDict(e)
			child_id = int(match.group('child_id'))
			msg = match.group('msg')
			if(msg.startswith('[-] ')):
				msg = msg[4:]
			e['message'] = colorizeChild(child_id, str(child_id) + ': ' + msg),
		return log.originalTextFromEventDict(e)
	except Exception, e:
		import traceback
		traceback.print_exc()
		return 'error: ' + str(e)