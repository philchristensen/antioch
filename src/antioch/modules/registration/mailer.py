# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

import smtplib, email, re, sys
from email import generator

try:
	from cStringIO import StringIO
except ImportError, e:
	from StringIO import StringIO

from antioch import model, sql

ADDRESS_REGEX = re.compile(r'^([0-9a-zA-Z]([-.\w]*[0-9a-zA-Z])*@([0-9a-zA-Z][-\w]*[0-9a-zA-Z]\.)+[a-zA-Z]{2,9})$')

def get_user_email(user):
	ex = user.get_exchange()
	system = ex.get_object(1)
	if(not isinstance(user, model.Object)):
		raise ValueError('Expecting player Object, got %r instead' % user)
	elif(user == system):
		return system.get('admin_email', 'daemon@antioch.local').value
	elif(not user.is_player()):
		raise ValueError('Expecting player Object, got %s instead' % user)
	
	player = ex.pool.runQuery(sql.build_select('player', avatar_id=user.get_id()))
	
	if('email' not in player[0]):
		raise RuntimeError("User email support not available for some reason. Weird.")
	
	return player[0]['email']

def send_user_message(source, dest, subject, content, **options):
	mail_server = options.get('mail_server', 'localhost')
	source_email = get_user_email(source)
	dest_email = get_user_email(dest)
	
	message = create_message(
		'%(source_name)s <%(source_email)s>' % dict(
			source_email	= source_email,
			source_name		= source.get_name(),
		),
		'%(dest_name)s <%(dest_email)s>' % dict(
			dest_email		= dest_email,
			dest_name		= dest.get_name(),
		),
		subject,
		content,
	)
	
	return send_message(mail_server, source_email, dest_email, message)

def send_message(mail_server, source, dest, message):
	try:
		smtp = smtplib.SMTP(mail_server)
		smtp.sendmail(source, dest, message)
		smtp.quit()
	except Exception, e:
		from twisted.python import failure
		reason = failure.Failure()
		reason.printTraceback(sys.stderr)
		return False
	
	return True

def create_message(source, dest, subject, body):
	msg = email.Message.Message()
	msg.set_payload(body)
	msg['From'] = source
	msg['To'] = dest
	msg['Subject'] = subject
	
	fp = StringIO()
	g = generator.Generator(fp, mangle_from_=False, maxheaderlen=60)
	g.flatten(msg)
	
	return fp.getvalue()
