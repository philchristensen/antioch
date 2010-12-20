#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: wizard_parse.py 61 2006-11-05 23:33:15Z phil $
#
# See LICENSE for details

from inner.space import parser, auth

sentence = command[command.find(" ") + 1:]
p = parser.Parser(parser.Lexer(sentence), caller, auth.get_registry())
caller.write(str(p.__dict__))