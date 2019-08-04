# antioch
# Copyright (c) 1999-2019 Phil Christensen
#
# See LICENSE for details

from django.test import TestCase
from django.test.utils import captured_output

from antioch.core.code import argparser, parse_deployment

class DeploymentsTestCase(TestCase):
    def test_simple_case(self):
        test_args = '#!antioch verb example "author class" --owner "wizard"'
        d = parse_deployment(test_args)
        self.assertEqual(d.type, 'verb')
        self.assertEqual(d.owner, 'wizard')
        self.assertEqual(d.origin, 'author class')
    
    def test_multiline_case(self):
        test_args = '#!antioch verb example\\ \n# "author class" \\ \n# --owner "wizard"'
        d = parse_deployment(test_args)
        self.assertEqual(d.type, 'verb')
        self.assertEqual(d.owner, 'wizard')
        self.assertEqual(d.origin, 'author class')
    
    def test_failure_case(self):
        test_args = '#!antioch verb example'
        
        with captured_output('stderr') as stdout:
            with self.assertRaises(SystemExit):
                d = parse_deployment(test_args)
        
        error = "antioch: error: the following arguments are required: origin, --owner\n"
        self.assertEqual(stdout.getvalue(), argparser.format_usage() + error)
            
    