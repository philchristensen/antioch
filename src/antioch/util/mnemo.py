
# Port of rufus-mnemo to Python
# https://github.com/jmettraux/rufus-mnemo
# Copyright (c) 2007-2011, John Mettraux, jmettraux@gmail.com

# didn't add the special spellings yet

consonants = list('bdghjkmnprstz')
vowels = list('aeiou')
syllables = [c + v for c in consonants for v in vowels] + ['wa', 'wo', 'ya', 'yo', 'yu']
negative = 'wi'

def encode(i):
	if i == 0:
		return ''
	
	mod = abs(i) % len(syllables)
	rest = abs(i) / len(syllables)
	
	return ''.join([
		['', negative][i < 0],
		encode(rest),
		syllables[mod],
	])

def decode(s):
	if not s:
		return 0
	
	if s.startswith(negative):
		return -1 * decode(s[len(negative):])
	
	rest = syllables.index(s[-2:]) if s[-2:] else 0
	return len(syllables) * decode(s[0:-2]) + rest
