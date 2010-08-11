# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Parser


This class parses command strings send by the user. It can understand a variety
of phrases, but they are all represented by the (BNF?) form:

<verb>[[[<dobj spec> ]<direct-object> ]+[<prep> [<pobj spec> ]<object-of-the-preposition>]*]

There are a long list of prepositions supported, some of which are interchangeable.
"""

import re, string, types

from txspace.errors import *
from txspace import exchange

#Here are all our supported prepositions
preps = [['with', 'using'],
		['at', 'to'],
		['in front of'],
		['in', 'inside', 'into', 'within'],
		['on top of', 'on', 'onto', 'upon', 'above'],
		['out of', 'from inside', 'from'],
		['over'], 
		['through'], 
		['under', 'underneath', 'beneath', 'below'],
		['around', 'round'],
		['between', 'among'],
		['behind', 'past'],
		['beside', 'by', 'near', 'next to', 'along'],
		['for', 'about'],
		#['is'],
		['as'],
		['off', 'off of']]

prepstring = ""
for item in preps:
	prepstring += "|".join(item)
	if(item != preps[len(preps) - 1]):
		prepstring += "|"

# TODO: These should be compiled ahead of time
PREP = r'(?P<prep>' + prepstring + r')'
SPEC = r"(?P<spec_str>my|the|a|an|\S+(?:\'s|s\'))"
PHRASE = r'(?:' + SPEC + r'\s)?(?P<obj_str>.+)'
POBJ_TEST = PREP + "\s" + PHRASE
QOTD = r'(?:\".+?(?!\\).\")'
MULTI_WORD = r'((\"|\').+?(?!\\).\2)|(\S+)'

class Lexer(object):
	"""
	An instance of this class will identify the various parts of a imperitive
	sentence. This may be of use to verb code, as well.
	"""
	def __init__(self, command):
		self.command = command
		
		self.dobj_str = None
		self.dobj_spec_str = None
		
		# First, find all words or double-quoted-strings in the text
		iterator = re.finditer(MULTI_WORD, command)
		self.words = []
		qotd_matches = []
		for item in iterator:
			if(item.group(1)):
				qotd_matches.append(item)
			word = item.group().strip('\'"').replace("\\'", "'").replace("\\\"", "\"")
			self.words.append(word)
		
		# Now, find all prepositions
		iterator = re.finditer(r"\b" + PREP + r"\b", command)
		prep_matches = []
		for item in iterator:
			prep_matches.append(item)
		
		#this method will be used to filter out prepositions inside quotes
		def nonoverlap(item):
			(start, end) = item.span()
			for word in qotd_matches:
				(word_start, word_end) = word.span()
				if(start > word_start and start < word_end):
					return False
				elif(end > word_start and end < word_end):
					return False
			return True
		
		#nonoverlap() will leave only true non-quoted prepositions
		prep_matches = filter(nonoverlap, prep_matches)
		
		#determine if there is anything after the verb
		if(len(self.words) > 1):
			#if there are prepositions, we only look for direct objects
			#until the first preposition
			if(prep_matches):
				end = prep_matches[0].start()-1
			else:
				end = len(command)
			#this is the phrase, which could be [[specifier ]object]
			dobj_phrase = command[len(self.words[0]) + 1:end]
			match = re.match(PHRASE, dobj_phrase)
			if(match):
				result = match.groupdict()
				self.dobj_str = result['obj_str'].strip('\'"').replace("\\'", "'").replace("\\\"", "\"")
				if(result['spec_str']):
					self.dobj_spec_str = result['spec_str'].strip('\'"').replace("\\'", "'").replace("\\\"", "\"")
				else:
					self.dobj_spec_str = ''
		
		self.prepositions = {}
		#iterate through all the prepositional phrase matches
		for index in range(len(prep_matches)):
			start = prep_matches[index].start()
			#if this is the last preposition, then look from here until the end
			if(index == len(prep_matches) - 1):
				end = len(command)
			#otherwise, search until the next preposition starts
			else:
				end = prep_matches[index + 1].start() - 1
			prep_phrase = command[start:end]
			phrase_match = re.match(POBJ_TEST, prep_phrase)
			if not(phrase_match):
				continue
			
			result = phrase_match.groupdict()
			
			#if we get a quoted string here, strip the quotes
			result['obj_str'] = result['obj_str'].strip('\'"').replace("\\'", "'").replace("\\\"", "\"")
			
			if(result['spec_str'] is None):
				result['spec_str'] = ''
			
			#if there is already a entry for this preposition, we turn it into
			#a list, and if it already is one, we append to it
			if(result['prep'] in self.prepositions):
				item = self.prepositions[result['prep']]
				if not(isinstance(item[0], list)):
					self.prepositions[result['prep']] = [[result['spec_str'], result['obj_str'], None], item]
				else:
					self.prepositions[result['prep']].append([result['spec_str'], result['obj_str'], None])
			#if it's a new preposition, we just save it here.
			else:
				self.prepositions[result['prep']] = [result['spec_str'], result['obj_str'], None]
	
	def get_details(self):
		return dict(
			command			= self.command,
			dobj_str		= self.dobj_str,
			dobj_spec_str	= self.dobj_spec_str,
			words			= self.words,
			prepositions	= self.prepositions,
		)

class TransactionParser(object):
	"""
	The parser instance is created by the avatar. A new instance is created
	for each remote call to perspective_parse.
	"""
	def __init__(self, lexer, caller, exchange, queue):
		"""
		Create a new parser object for the given command, as issued by
		the given caller, using the registry.
		"""
		self.lexer = lexer
		self.caller = caller
		self.exchange = exchange
		self.queue = queue
		
		self.this = None
		
		if(self.lexer):
			for key, value in self.lexer.get_details().items():
				self.__dict__[key] = value
		
			for prep in self.prepositions:
				prep_record_list = self.prepositions[prep]
				if not(isinstance(prep_record_list[0], list)):
					prep_record_list = [prep_record_list]
				for record in prep_record_list:
					#look for an object with this name/specifier
					obj = self.find_object(record[0], record[1])
					#try again (maybe it just looked like a specifier)
					if(not obj and record[0]):
						record[1] = record[0] + ' ' + record[1]
						record[0] = ''
						obj = self.find_object(record[0], record[1])
					#one last shot for pronouns
					if not(obj):
						obj = self.get_pronoun_object(record[1])
					record[2] = obj
		
		if(hasattr(self, 'dobj_str') and self.dobj_str):
			#look for an object with this name/specifier
			self.dobj = self.find_object(self.dobj_spec_str, self.dobj_str)
			#try again (maybe it just looked like a specifier)
			if(not self.dobj and self.dobj_spec_str):
				self.dobj_str = self.dobj_spec_str + ' ' + self.dobj_str
				self.dobj_spec_str = ''
				self.dobj = self.find_object(None, self.dobj_str)
			#if there's nothing with this name, then we look for
			#pronouns before giving up
			if not(self.dobj):
				self.dobj = self.get_pronoun_object(self.dobj_str)
		else:
			#didn't find anything, probably because nothing was there.
			self.dobj = None
			self.dobj_str = None
	
	def get_environment(self):
		def api_write(user, text, is_error=False):
			print 'trying to write: ' + str(text)
			self.queue.send(user.get_id(), dict(
				command		= 'write',
				text		= str(text),
				is_error	= is_error,
			))
		
		def api_observe(user, observations):
			print 'trying to display: ' + str(observations)
			self.queue.send(user.get_id(), dict(
				command			= 'observe',
				observations	= observations,
			))
		
		return dict(
			command			= self.command,
			caller			= self.caller,
			dobj			= self.dobj,
			dobj_str		= self.dobj_str,
			dobj_spec_str	= self.dobj_spec_str,
			words			= self.words,
			prepositions	= self.prepositions,
			this			= self.this,
			
			system			= self.exchange.get_object(1),
			here			= self.caller.get_location(),
			
			write			= api_write,
			observe			= api_observe,
			
			get_dobj		= self.get_dobj,
			get_dobj_str	= self.get_dobj_str,
			has_dobj		= self.has_dobj,
			has_dobj_str	= self.has_dobj_str,
			
			get_pobj		= self.get_pobj,
			get_pobj_str 	= self.get_pobj_str,
			has_pobj 		= self.has_pobj,
			has_pobj_str 	= self.has_pobj_str,
		)
	
	def find_object(self, specifier, name):
		"""
		Look for an object, with the optional specifier, in the area
		around the person who entered this command. If the posessive
		form is used (i.e., "Bill's spoon") and that person is not
		here, a NoSuchObjectError is thrown for that person.
		"""
		if(specifier == 'my'):
			search = self.caller
		elif(specifier and specifier.find("'") != -1):
			person = specifier[0:specifier.index("'")]
			search = self.caller.get_location().find(person)
			if not(search):
				return None
		else:
			search = self.caller.get_location()
		
		if(name):
			result = search.find(name)
		else:
			result = None
		
		return result
	
	def get_verb(self):
		"""
		Determine the most likely verb for this sentence. There is a search
		order for verbs, as follows:
			Caller->Caller's Contents->Location->Items in Location->
			Direct Object->Objects of the Preposition
		"""
		if(getattr(self, 'this', None) is not None):
			a = self.this.get_ancestor_with(verb_str)
			return a.get_verb(verb_str)
		
		if not(self.words):
			raise NoSuchVerbError('parser: ' + self.command)
		
		verb_str = self.words[0]
		matches = []
		ctx = self.caller
		
		location = self.caller.get_location()
		
		checks = [self.caller]
		checks.extend(self.caller.get_contents())
		if(location):
			checks.append(location)
			checks.extend(location.get_contents())
		checks.append(self.dobj)
		
		for key in self.prepositions:
			# if there were multiple uses of a preposition
			if(isinstance(self.prepositions[key][0], list)):
				# then check each one for a verb
				checks.extend([pobj[2] for pobj in self.prepositions[key] if pobj[2]])
			else:
				checks.append(self.prepositions[key][2])
		
		matches = [x for x in checks if x and x.has_verb(verb_str)]
		
		self.this = self.filter_matches(matches)
		
		if(isinstance(self.this, list)):
			if(len(self.this) > 1):
				raise AmbiguousVerbError(verb_str, self.this)
			elif(len(self.this) == 0):
				self.this = None
			else:
				self.this = self.this[0]
		
		if not(self.this):
			raise NoSuchVerbError('parser: ' + verb_str)
		
		#print "Verb found on: " + str(self.this)
		return self.this.get_verb(verb_str, recurse=True)
	
	def filter_matches(self, possible):
		result = []
		#print "possble is " + str(possible)
		if not(isinstance(possible, list)):
			possible = [possible]
		ctx = self.caller
		verb_str = self.words[0]
		for item in possible:
			if(item.is_player() and item is not self.caller):
				continue
			elif(item in result):
				continue
			
			origin = item.get_ancestor_with('verb', verb_str)
			verb = origin.get_verb(verb_str)
			
			if(verb.is_ability() and self.caller != item):
				continue
			elif(verb.is_method()):
				continue

			result.append(item)

		#print "result is " + str(result)
		return result
		
	def get_pronoun_object(self, pronoun):
		"""
		Return the correct object for various pronouns.
		Also, a object number (starting with a #) will
		return the object for that id.
		"""
		ctx = self.caller
		if(pronoun == "me"):
			return self.caller
		elif(pronoun == "here"):
			return self.caller.get_location()
		# elif(pronoun == "this"):
		# 	return self.caller.get_observing(ctx)
		elif(pronoun[0] == "#"):
			return self.exchange.get_object(pronoun)
		else:
			return None
	
	def get_dobj(self):
		"""
		Get the direct object for this parser. If there was no
		direct object found, raise a NoSuchObjectError
		"""
		if not(self.dobj):
			raise NoSuchObjectError(self.dobj_str)
		return self.dobj
	
	def get_pobj(self, prep):
		"""
		Get the object for the given preposition. If there was no
		object found, raise a NoSuchObjectError; if the preposition
		was not found, raise a NoSuchPrepositionError.
		"""
		if not(prep in self.prepositions):
			raise NoSuchPrepositionError(prep)
		if(isinstance(self.prepositions[prep][0], list)):
			matches = []
			for item in self.prepositions[prep]:
				if(item[2]):
					matches.append(item[2])
			if(len(matches) > 1):
				raise AmbiguousObjectError(matches[0][1], matches)
			elif not(matches):
				raise NoSuchObjectError(self.prepositions[prep][0][1])
		if not(self.prepositions[prep][2]):
			raise NoSuchObjectError(self.prepositions[prep][1])
		return self.prepositions[prep][2]
	
	def get_dobj_str(self):
		"""
		Get the direct object **string** for this parser. If there was no
		direct object **string** found, raise a NoSuchObjectError
		"""
		if not(self.dobj_str):
			raise NoSuchObjectError('direct object')
		return self.dobj_str
	
	def get_pobj_str(self, prep, return_list=False):
		"""
		Get the object **string** for the given preposition. If there was no
		object **string** found, raise a NoSuchObjectError; if the preposition
		was not found, raise a NoSuchPrepositionError.
		"""
		if not(self.prepositions.has_key(prep)):
			raise NoSuchPrepositionError(prep)
		if(isinstance(self.prepositions[prep][0], list)):
			matches = []
			for item in self.prepositions[prep]:
				if(item[1]):
					matches.append(item[1])
			if(len(matches) > 1):
				if(return_list):
					return matches
				else:
					raise matches[0]
			elif not(matches):
				raise NoSuchObjectError(self.prepositions[prep][0][1])
		return self.prepositions[prep][1]
	
	def get_pobj_spec_str(self, prep, return_list=False):
		"""
		Get the object **specifier** for the given preposition. If there was no
		object **specifier** found, return the empty string; if the preposition
		was not found, raise a NoSuchPrepositionError.
		"""
		if not(self.prepositions.has_key(prep)):
			raise NoSuchPrepositionError(prep)
		if(isinstance(self.prepositions[prep][0], list)):
			matches = []
			for item in self.prepositions[prep]:
				matches.append(item[0])
			if(len(matches) > 1):
				if(return_list):
					return matches
				else:
					return matches[0]
		return self.prepositions[prep][0]
	
	def has_dobj(self):
		"""
		Was a direct object found?
		"""
		return self.dobj is not None
	
	def has_pobj(self, prep):
		"""
		Was an object for this preposition found?
		"""
		if(prep not in self.prepositions):
			return False
		
		found_prep = False
		
		if(isinstance(self.prepositions[prep][0], list)):
			for item in self.prepositions[prep]:
				if(item[2]):
					found_prep = True
					break
		else:
			found_prep = bool(self.prepositions[prep][2])
		return found_prep
	
	def has_dobj_str(self):
		"""
		Was a direct object string found?
		"""
		return self.dobj_str != None
	
	def has_pobj_str(self, prep):
		"""
		Was a object string for this preposition found?
		"""
		if(prep not in self.prepositions):
			return False
		
		found_prep = False
		
		if(isinstance(self.prepositions[prep][0], list)):
			for item in self.prepositions[prep]:
				if(item[1]):
					found_prep = True
					break
		else:
			found_prep = bool(self.prepositions[prep][1])
		return found_prep
