# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details


# Port of rufus-mnemo to Python
# https://github.com/jmettraux/rufus-mnemo
# Original copyright (c) 2007-2011, John Mettraux, jmettraux@gmail.com

consonants = list('bdghjkmnprstz')
vowels = list('aeiou')
syllables = [c + v for c in consonants for v in vowels] + ['wa', 'wo', 'ya', 'yo', 'yu']
negative = 'wi'

replacements = [
	[ 'hu', 'fu' ],
	[ 'si', 'shi' ],
	[ 'ti', 'chi' ],
	[ 'tu', 'tsu' ],
	[ 'zi', 'tzu' ],
]

def encode(i):
	if i == 0:
		return ''
	
	mod = abs(i) % len(syllables)
	rest = abs(i) / len(syllables)
	
	result = ''.join([
		['', negative][i < 0],
		encode(rest),
		syllables[mod],
	])
	for old, new in replacements:
		result = result.replace(old, new)
	return result

def decode(s):
	if not s:
		return 0
	
	if s.startswith(negative):
		return -1 * decode(s[len(negative):])
	
	for new, old in replacements:
		s = s.replace(old, new)
	
	rest = syllables.index(s[-2:]) if s[-2:] else 0
	return len(syllables) * decode(s[0:-2]) + rest
