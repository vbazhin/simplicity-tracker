from django.test import TestCase
from django.utils import unittest
from models import *

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)


# Пакет тестов объекта Trad

class TradTestCase(unittest.TestCase):
    def setUp(self):
        try:
            self.user =  User.objects.get(username = 'admin')
        except User.DoesNotExist:
            self.user = User.objects.create(username='admin',
                                            is_staff=1,
                                            is_superuser=1)
        self.trad = Trad.objects.create(label='Me',
                                        is_expiration = 'Yes',
                                        expiration=datetime.datetime(2017, 12, 6, 16, 29, 43, 79043),
                                        author = self.user,
                                        status="new")
        self.comment = Comment(text = u'Задание принято пользователем '
                                      + self.user.username,
                               date = datetime.datetime.now(),
                               trad_id = self.trad.id,
                               author = self.user)
    def test_time_left_returns_timedelta(self):
        """timedelta"""
        self.assertEqual(str(type(self.trad.time_left())), "<type 'datetime.timedelta'>")

    def test_renew_status_no_exceptions(self):
        '''Returns None'''
        self.assertEqual(self.trad.renew_status(('taken'), self.user), None)

    def test_define_status_returns_new(self):
        '''Returns current status'''
        self.assertEqual(self.trad.define_condition(), 'new')
