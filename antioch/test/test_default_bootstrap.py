# antioch
# Copyright (c) 1999-2019 Phil Christensen
#
# See LICENSE for details

from django.test import TestCase
from django.db import connection
from django.conf import settings

from antioch import test
from antioch.core import parser, exchange, source, models

class DefaultBootstrapTestCase(TestCase):
    fixtures = ['core-default.json']
    
    def setUp(self):
        try:
            repo = models.Repository.objects.get(slug='default')
        except models.Repository.DoesNotExist:
            repo = models.Repository(
                slug='default',
                prefix='antioch/core/bootstrap/default_verbs',
                url=settings.DEFAULT_GIT_REPO_URL
            )
            repo.save()
        source.deploy_all(repo)

        self.exchange = exchange.ObjectExchange(connection)
        self.exchange.queue = test.Anything(
            flush    = lambda: None,
        )
    
    def test_player_look(self):
        caller = self.exchange.get_object('wizard')
        
        l = parser.Lexer('look here')
        p = parser.TransactionParser(l, caller, self.exchange)
        
        v = p.get_verb()
        self.assertEqual(p.this, caller)
        
        def push(user_id, msg):
            self.assertEqual(user_id, caller.get_id())
            self.assertEqual(msg['observations']['name'], 'The Laboratory')
        
        self.exchange.queue.push = push
        v.execute(p)
    
    def test_player_eval(self):
        self.skipTest("Test broken without celery support")
        caller = self.exchange.get_object('wizard')
        
        l = parser.Lexer('eval "test"')
        p = parser.TransactionParser(l, caller, self.exchange)
        
        v = p.get_verb()
        self.assertEqual(p.this, caller)
        
        self._test_player_eval_ran = False
        
        def push(user_id, msg):
            self._test_player_eval_ran = True
            self.assertEqual(user_id, 2)
            self.assertEqual(msg['text'], 'test')
        
        self.exchange.queue.push = push
        v.execute(p)
        
        self.assertEqual(self._test_player_eval_ran, True)
    
    def test_player_write(self):
        self.skipTest("Test broken without celery support")
        caller = self.exchange.get_object('wizard')
        
        l = parser.Lexer('exec write(caller, "test")')
        p = parser.TransactionParser(l, caller, self.exchange)
        
        v = p.get_verb()
        self.assertEqual(p.this, caller)
        
        self._test_player_write_ran = False
        
        def push(user_id, msg):
            self._test_player_write_ran = True
            self.assertEqual(user_id, 2)
            self.assertEqual(msg['text'], 'test')
        
        self.exchange.queue.push = push
        v.execute(p)
        
        self.assertEqual(self._test_player_write_ran, True)
    
    def test_player_multiparent_look(self):
        caller = self.exchange.get_object('wizard')
        random = self.exchange.instantiate('object', name='random')
        caller.add_parent(random)
        
        l = parser.Lexer('look here')
        p = parser.TransactionParser(l, caller, self.exchange)
        
        v = p.get_verb()
        self.assertEqual(p.this, caller)
        
        def push(user_id, msg):
            self.assertEqual(user_id, caller.get_id())
            self.assertEqual(msg['observations']['name'], 'The Laboratory')
        
        self.exchange.queue.push = push
        v.execute(p)
    
    # def test_wizard_edit(self):
    #     caller = self.exchange.get_object('wizard')
    #
    #     l = parser.Lexer('edit me')
    #     p = parser.TransactionParser(l, caller, self.exchange)
    #
    #     v = p.get_verb()
    #     self.assertEqual(p.this, caller)
    #
    #     def push(user_id, msg):
    #         self.assertEqual(user_id, 2)
    #         self.assertEqual(msg['details']['name'], 'Wizard')
    #
    #     self.exchange.queue.push = push
    #     v.execute(p)
    #
    # def test_wizard_edit_system(self):
    #     caller = self.exchange.get_object('wizard')
    #
    #     l = parser.Lexer('edit #1')
    #     p = parser.TransactionParser(l, caller, self.exchange)
    #
    #     v = p.get_verb()
    #     self.assertEqual(p.this, caller)
    #
    #     def push(user_id, msg):
    #         self.assertEqual(user_id, 2)
    #         self.assertEqual(msg['details']['id'], 1)
    #         self.assertEqual(msg['details']['name'], 'System Object')
    #
    #     self.exchange.queue.push = push
    #     v.execute(p)
