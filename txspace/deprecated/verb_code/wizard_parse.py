# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

from txspace import parser, auth

sentence = command[command.find(" ") + 1:]
p = parser.Parser(parser.Lexer(sentence), caller, registry)
caller.write(str(p.__dict__))