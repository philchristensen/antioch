# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
A variety of antioch error classes
"""

class UserError(Exception):
	"""
	This is the superclass for all Errors that may be generated which
	should be reported to the user who "caused" them. At construction,
	additional information can be supplied that will be presented to the
	user if they are a "wizard" user.
	"""
	def __init__(self, message, data=None):
		self._message = message
		self.data = data
	
	def __str__(self):
		return str(self._message)
	
	def __repr__(self):
		data = ""
		if(self.data):
			data += ("\n    " + str(self.data))
		return str(self._message) + data

class TestError(Exception):
	"""
	Special error used by tests.
	"""
	def __init__(self, message=None, data=None):
		self._message = message
		self.data = data
	
	def __str__(self):
		return str(self._message)
	
	def __repr__(self):
		data = ""
		if(self.data):
			data += ("\n    " + str(self.data))
		return str(self._message) + data

class UsageError(UserError):
	"""
	This exception is available as a convenience to verbs that
	wish to print an error message and exit (rolling back any changes).
	"""

class AmbiguousObjectError(UserError):
	"""
	When this class is raised, it means that at some point a single
	object was expected, but multiple ones were found instead.
	When printed to the user, this shows a list of matching items,
	along with their unique IDs, so the user can choose the correct one.
	"""
	def __init__(self, name, matches, message=None):
		self.name = name
		if(message):
			result = message
		else:
			result = "When you say, \"" + self.name + "\", do you mean "
			for index in range(len(matches)):
				match = matches[index]
				if(index > 0 and index <= len(matches) - 1):
					result += ", "
				if(index == len(matches) - 1):
					result += " or "
				result += str(match)
			result += "?"
		UserError.__init__(self, result, matches)

class AmbiguousVerbError(UserError):
	"""
	When this class is raised, it means that when searching for a verb,
	multiple possibilities were encountered. There are some uncertainties
	about whether this should be presented to the user or not, since there
	is little they can do about it, unless they are wizardly.
	When printed to the user, this shows a list of objects with matching verbs.
	"""
	def __init__(self, name, matches):
		self.name = name
		result = "More than one object defines \"" + self.name + "\": "
		for match in matches:
			index = matches.index(match)
			if(index > 0 and index <= len(matches) - 1):
				result = result + ", "
			if(index == len(matches) - 1):
				result = result + " and "
			result = result + str(match)
		result = result + "."
		UserError.__init__(self, result, matches)

class PermissionError(UserError):
	"""
	The user tried to do something he doesn't have permission for. (duh?)
	"""

class AccessError(PermissionError):
	"""
	A more specific kind of PermissionError.
	"""
	def __init__(self, accessor, access_str, subject):
		self.subject = subject
		self.accessor = accessor
		self.access_str = access_str

		PermissionError.__init__(self, "%s is not allowed to '%s' on %s" % (str(accessor), access_str, str(subject)))

class RecursiveError(UserError):
	"""
	Raised if the user attempts to put a container inside one of its contents,
	or set the parent of an object to one of its children. This is unlikely
	to happen because of user error, and may not need to be presented to the
	user, but will be for the time.
	"""
	pass

class QuotaError(UserError):
	"""
	Raised if the user tries to create objects he does not have enough quota for.
	"""
	pass

class NoSuchObjectError(UserError):
	"""
	Most often raised by the parser when a verb requests an object that is not
	there. If the verb is written correctly, means the user tried to manipulate
	a non-existant object (a typo, or other misteak).
	"""
	def __init__(self, name):
		UserError.__init__(self, "There is no '" + str(name) + "' here.")

class NoSuchPrepositionError(UserError):
	"""
	Raised by the parser when the programmer attempts to retreive the object
	for a preposition that was not used in the sentence.
	"""
	def __init__(self, prep):
		UserError.__init__(self, "I don't understand you.", prep)

class NoSuchVerbError(UserError):
	"""
	Raised by the parser when it cannot find a verb for a sentence.
	"""
	def __init__(self, name):
		UserError.__init__(self, "I don't know how to do that.", name)

class NoSuchPropertyError(UserError):
	"""
	Raised by the system when it cannot find a needed property.
	"""
	def __init__(self, name, origin=None):
		UserError.__init__(self, "There is no '" + str(name) + "' property defined" + ['.', ' on %s.' % origin][bool(origin)])

class ExecutionError(UserError):
	"""
	Raised when user code causes some kind of exception.
	"""
	
	def __init__(self, code, e):
		self.code = code
		self.e = e
		UserError.__init__(self, "An error occurred in user code: %s" % e)