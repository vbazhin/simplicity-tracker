#coding: utf-8
from django.db import models
from django.http import QueryDict
from markitup.fields import MarkupField
from mptt.models import MPTTModel, TreeForeignKey
from django.contrib.auth.models import User
import datetime
import random
import md5
from django.utils import unittest

# Todo
    # Нужно сделать поддержку проектов
    # Кеширование шаблонов
    # Кеширование запросов
    # Юниттесты всех моделей
    # Универсальные временные зоны, utc время
    # Перенести определение длины ползунка на пользовательскую сторону (js)
    # Задания группам
    # Интернационализация

# Возможно
    # mpttшная древовидная структура комментариев



class Project(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название проекта")
    crew = models.ManyToManyField(User, blank=True, null=True)
    def __unicode__(self):
        return self.name




# Пакет тестов объекта Trad

class TradTestCase(unittest.TestCase):
    def setUp(self):
        try:
            self.user =  User.objects.get(username = 'admin')
        except User.DoesNotExist:
            self.user = User.objects.create(username='admin', is_staff=1, is_superuser=1)
        self.trad = Trad.objects.create(label='Me', is_expiration = 'Yes', expiration=datetime.datetime(2017, 12, 6, 16, 29, 43, 79043), author = self.user, status="new")
        self.comment = Comment(text = u'Задание принято пользователем ' + self.user.username, date = datetime.datetime.now(), trad_id = self.trad.id,  author = self.user)
    def test_time_left_returns_timedelta(self):
        """timedelta"""
        self.assertEqual(str(type(self.trad.time_left())), "<type 'datetime.timedelta'>")

    def test_renew_status_no_exceptions(self):
        '''Returns None'''
        self.assertEqual(self.trad.renew_status(('taken'), self.user), None)

    def test_define_status_returns_new(self):
        '''Returns current status'''
        self.assertEqual(self.trad.define_condition(), 'new')

class Trad(models.Model):

    STATUS_VALUES = (
        ('new', 'Новое'),
        ('taken', 'В работе'),
        ('refused', 'Отменено'),
        ('closed', 'Закрыто'),
        ('done', 'Сделано'),
        ('success', 'Завершено'),
    )

    TYPES = ( # Чтобы не дропать базу для следующей версии, когда будет поддержка проектов
        ('task', 'Задание'),
        ('notification', 'Уведомление'),
        )
    project = models.ForeignKey(Project, blank=True, null=True)
    label = models.CharField(max_length=100, verbose_name="Название")
    text = models.TextField(blank=True, max_length=5000, verbose_name="Описание")
    given = models.DateTimeField(auto_now_add=True, verbose_name="Дата назначения")
    is_expiration = models.CharField(blank=True,  max_length=3, verbose_name="Установить дату")
    expiration = models.DateTimeField(blank=True, null=True, verbose_name="Дата истечения")
    change_date = models.DateTimeField(auto_now=True, verbose_name="Дата изменения")
    # кое-что тут http://stackoverflow.com/questions/38601/using-django-time-date-widgets-in-custom-form
    status = models.CharField(blank=True, max_length=10, choices=STATUS_VALUES, verbose_name="Текущий статус")
    receiver = models.ManyToManyField(User, blank=True, null=True, related_name = 'receiver')
    author = models.ForeignKey(User, related_name = 'author')
    type = models.CharField(blank=True, null=True, max_length=12, choices=TYPES, verbose_name="Тип") # Чтобы не дропать базу для следующей версии, когда будет поддержка проектов

    def time_left(self):
        if self.is_expiration == 'Yes':
            time_left = self.expiration - datetime.datetime.now()
            return time_left

    def renew_status(self, new_data, current_user):
        if 'take' in new_data:
            comment = Comment(text = u'Задание принято пользователем ' + current_user.username, date = datetime.datetime.now(), trad_id = self.id,  author = current_user)
            self.status = 'taken'
        elif 'refuse' in new_data:
            comment = Comment(text = u'Пользователь ' + current_user.username + u' отказался от задания', date = datetime.datetime.now(), trad_id = self.id,  author = current_user)
            self.status = 'refused'
        elif 'done' in new_data:
            comment = Comment(text = u'Пользователь ' + current_user.username + u' выполнил задание', date = datetime.datetime.now(), trad_id = self.id,  author = current_user)
            self.status = 'done'
        elif 'success' in new_data:
            comment = Comment(text = u'Задание выполнено. Закрыто пользователем ' + current_user.username, date = datetime.datetime.now(), trad_id = self.id,  author = current_user)
            self.status = 'success'
        elif 'close' in new_data:
            comment = Comment(text = u'Задание закрыто пользователем ' + current_user.username, date = datetime.datetime.now(), trad_id = self.id,  author = current_user)
            self.status = 'closed'
        elif 'setback' in new_data:
            comment = Comment(text = u'Задание не принято пользователем ' + current_user.username, date = datetime.datetime.now(), trad_id = self.id,  author = current_user)
            self.status = 'new'
        elif 'delete' in new_data:
            try:
                self.delete()
            except:
                return 'Невозможно удалить'
        try:
            self.save()
        except:
            return 'Ошибка сохранения объекта'
        try:
            comment
        except:
            comment = None
        else:
            try:
                comment.save()
            except:
                return 'Ошибка сохранения комментария'




    def define_condition (self):
        if self.status == 'done':
            self.condition = 'На проверке'
        elif self.status == 'success':
            self.condition = 'Успешно'
        elif self.status == 'closed':
            self.condition = 'Закрыто'
        elif self.status == 'refused':
            self.condition = 'Не принято'
        else:
            if self.is_expiration == 'Yes':
                self.left = self.time_left()
                self.leftdays = self.left.days
                self.lefthours = self.left.seconds/3600
                self.leftminutes = self.left.seconds/60
                if self.left > datetime.timedelta(0):
                    if self.status == 'taken':
                        self.condition = 'В работе'
                    elif self.status == 'new':
                        self.condition = 'Новое'
                else:
                    self.condition = 'Не выполнено'
                    if self.status != 'error':
                        self.status = 'error'
                        self.save()
            else:
                if self.status == 'taken':
                    self.condition = 'В работе'
                elif self.status == 'new':
                    self.condition = 'Новое'
        status_attrs = {
            'done' : {'icon' : 'ok', 'alert' : 'success'},
            'success': {'icon' : 'ok', 'alert' : 'success'},
            'closed': {'icon' : 'ban-circle', 'alert' : 'none'},
            'refused': {'icon' : 'ban-circle', 'alert' : 'none'},
            'taken': {'icon' : 'cog', 'alert' : 'info'},
            'new': {'icon' : 'exclamation-sign', 'alert' : 'new'},
            'error': {'icon' : 'remove', 'alert' : 'error'}
        }
        self.attrs = status_attrs[self.status]
        if self.is_expiration == "Yes":
            self.delta0 = self.expiration - self.given
            self.delta1 = datetime.datetime.now() - self.given
            self.time = (self.delta1.total_seconds()/self.delta0.total_seconds())*100
            self.given_time = self.given.time()

        return self.status


    def __unicode__(self):
        return self.label




        
class Comment(models.Model):
    text = models.TextField(max_length=1000, verbose_name='Текст')
    date = models.DateTimeField(verbose_name="Дата")
    trad = models.ForeignKey(Trad)
    author = models.ForeignKey(User)

    def __unicode__(self):
        return self.text

from django.core.mail import send_mail


class DelegatedNames(models.Model):
    name = models.CharField(max_length=40, verbose_name='Имя')
    email = models.EmailField(max_length=80)
    
    def send_invite(self):
        send_mail('Subject here', 'Here is the message.', 'v.bazhin@gmail.com', ['v.bazhin@gmail.com'], fail_silently=False)
        
class InviteLink(models.Model):
    link = models.CharField(max_length=100, verbose_name="Ссылка")
    valid_status = models.CharField(max_length=10, verbose_name="Валидность")
    delegated_time = models.DateTimeField(auto_now_add=True, verbose_name="Делегирована")

    def generate(self):
        hash = md5.md5(str(random.getrandbits(128))).hexdigest() # Генерируем хеш
        self.link = hash
        self.valid_status = 'valid'
        self.save()
        return self

    #def __unicode__(self):
        #return self.id