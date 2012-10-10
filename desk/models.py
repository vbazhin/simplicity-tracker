#author: v.bazhin
#coding: utf-8
from django.db import models
from django.contrib.auth.models import User
import datetime
import random
import md5
from django.utils import unittest
from django.core.mail import send_mail
from django.utils.translation import pgettext
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.utils.html import escape

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
    name = models.CharField(max_length=100, verbose_name=gettext_lazy("Project name"))
    crew = models.ManyToManyField(User, blank=True, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = gettext_lazy('Project')
        verbose_name_plural = gettext_lazy('Projects')


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


status_attrs = {
    'done' : {'icon' : 'ok', 'alert' : 'success'},
    'success': {'icon' : 'ok', 'alert' : 'success'},
    'closed': {'icon' : 'ban-circle', 'alert' : 'none'},
    'refused': {'icon' : 'ban-circle', 'alert' : 'error'},
    'taken': {'icon' : 'cog', 'alert' : 'info'},
    'new': {'icon' : 'exclamation-sign', 'alert' : 'new'},
    'error': {'icon' : 'remove', 'alert' : 'error'}
}


class Trad(models.Model):

    STATUS_VALUES = (
        ('new', pgettext('issue condition', 'New')),
        ('taken', pgettext('issue condition', 'In progress')),
        ('refused', pgettext('issue condition', 'Rejected')),
        ('closed', pgettext('issue condition', 'Closed')),
        ('done', pgettext('issue condition', 'Done')),
        ('success', pgettext('issue condition', 'Success'))
    )

    TYPES = ( # Чтобы не дропать базу для следующей версии, когда будет поддержка проектов
        ('tassk', pgettext('Type of issue', 'Task')),
        ('notification', pgettext('Type of issue', 'Notification')),
        )
    project = models.ForeignKey(Project, blank=True, null=True, verbose_name=gettext_lazy('Project'))
    label = models.CharField(max_length=100, verbose_name=gettext_lazy('Label'))
    text = models.TextField(blank=True, max_length=5000, verbose_name=gettext_lazy('Description'))
    given = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Occurrence time'))
    is_expiration = models.CharField(blank=True,  max_length=3, verbose_name=gettext_lazy('Expiration'))
    expiration = models.DateTimeField(blank=True, null=True, verbose_name=gettext_lazy('Expiration date'))
    change_date = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Change date'))
    # кое-что тут http://stackoverflow.com/questions/38601/using-django-time-date-widgets-in-custom-form
    status = models.CharField(blank=True, max_length=10, choices=STATUS_VALUES, verbose_name=gettext_lazy('Current status'))
    receiver = models.ManyToManyField(User, blank=True, null=True, related_name = 'receiver', verbose_name=gettext_lazy('Receiver') )
    author = models.ForeignKey(User, related_name = 'author', verbose_name = gettext_lazy('Author'))
    type = models.CharField(blank=True, null=True, max_length=12, choices=TYPES, verbose_name=gettext_lazy("Type")) # Чтобы не дропать базу для следующей версии, когда будет поддержка проектов
    is_deleted = models.CharField(blank=True, null=True, max_length=3, verbose_name=gettext_lazy('Is deleted'))

    def time_left(self):
        if self.is_expiration == 'Yes':
            time_left = self.expiration - datetime.datetime.now()
            return time_left

    def add(self, data, request_user):

        tz_offset = data['timezone_offset']
        expdate = data['expdate']
        exptime = data['exptime']
        if expdate == None:
            exp_value = 'No'
            exp = None
        else:
            exp_value = 'Yes'
            exp = datetime.datetime.combine(expdate, exptime) # Соединяем дату и время
            #if exptime == None:
            #is_exp = 'No'
        self = Trad(label = data['label'], text = escape(data['text']), given=datetime.datetime.now(), is_expiration = exp_value, expiration=exp, status='new', author = request_user) # Поменять date - now(), expiration - забивается
        self.save()
        receivers = data['receiver']
        #if not receivers:
        #receivers = User.objects.exclude(id = request.user.id)
        self.receiver = receivers

    def save_edited(self, data, request_user):
        expdate = data['expdate']
        exptime = data['exptime']
        if expdate == None:
            exp_value = 'No'
            exp = None
        else:
            exp_value = 'Yes'
            exp = datetime.datetime.combine(expdate, exptime)
            #if exptime == None:
            #is_exp = 'No'
        self.label = data['label']
        self.text = data['text']
        self.given=datetime.datetime.now()
        self.is_expiration = exp_value
        self.expiration=exp
        self.status='new'
        self.author = request_user # Поменять date - now(), expiration - забивается
        self.save()
        receivers = data['receiver']
        if not receivers:
            receivers = User.objects.exclude(id = request_user.id)
        self.receiver = receivers


    def renew_status(self, new_data, current_user):
        self.status = new_data
        comment = Comment(type='status_cmt', text = self.status, date = datetime.datetime.now(), trad_id = self.id,  author = current_user)
        try:
            self.save()
        except:
            return _('Issue saving error')
        try:
            comment
        except:
            comment = None
        else:
            try:
                comment.save()
            except:
                return _('Comment saving error')


    def define_condition (self):
        if self.status == 'done':
            self.condition = pgettext('issue condition', 'On check')
        elif self.status == 'success':
            self.condition = pgettext('issue condition', 'Success')
        elif self.status == 'closed':
            self.condition = pgettext('issue condition', 'Closed')
        elif self.status == 'refused':
            self.condition = pgettext('issue condition', 'Rejected')
        else:
            if self.is_expiration == 'Yes':
                self.left = self.time_left()
                self.leftdays = self.left.days
                self.lefthours = self.left.seconds/3600
                self.leftminutes = self.left.seconds/60
                if self.left > datetime.timedelta(0):
                    if self.status == 'taken':
                        self.condition = 'In progress'
                    elif self.status == 'new':
                        self.condition = pgettext('issue condition', 'New')
                else:
                    self.condition = pgettext('issue condition', 'Failed')
                    if self.status != 'error':
                        self.status = 'error'
                        self.save()
            else:
                if self.status == 'taken':
                    self.condition = pgettext('issue condition', 'In progress')
                elif self.status == 'new':
                    self.condition = pgettext('issue condition', 'New')
        self.attrs = status_attrs[self.status]
        if self.is_expiration == "Yes":
            self.delta0 = self.expiration - self.given
            self.delta1 = datetime.datetime.now() - self.given
            self.time = (self.delta1.total_seconds()/self.delta0.total_seconds())*100
            self.given_time = self.given.time()
        return self.status

    def count_comments(self):
        self.comments_num = Comment.objects.filter(trad = self).count()

    def delete(self):
        if self.is_deleted != 'Yes':
            try:
                self.is_deleted = 'Yes'
                self.save()
            except:
                pass

    def __unicode__(self):
        return self.label

    class Meta:
        verbose_name = gettext_lazy('Issue')
        verbose_name_plural = gettext_lazy('Issues')


class Comment(models.Model):
    text = models.TextField(max_length=1000, verbose_name=gettext_lazy('Text'))
    type = models.TextField(max_length=10, blank=True, null=True, verbose_name=gettext_lazy('Type'))
    date = models.DateTimeField(verbose_name=gettext_lazy('Occurrence time'))
    trad = models.ForeignKey(Trad)
    author = models.ForeignKey(User)

    def get_text(self):
        def __init__(self):
            if self.type == 'status_cmt':
                self.status_attrs = status_attrs[self.text]

        text_messages = {
            'done' : gettext_lazy('The task is done, send for check'),
            'success': gettext_lazy('Done successfully'),
            'closed':  gettext_lazy('Closed'),
            'refused': gettext_lazy('Refused'),
            'taken': gettext_lazy( 'Accepted'),
            'new': gettext_lazy( 'Given again'),
            'deleted': gettext_lazy( 'Deleted'),
        }

        self.status_attr = status_attrs[self.text]
        self.text = text_messages[self.text]
        return self.text

    def add(self, data, request_user, related_trad_id):
        self = Comment(text = escape(data['text']), date = datetime.datetime.now(), trad_id = related_trad_id,  author = request_user)
        self.save()

    def __unicode__(self):
        return self.text

    class Meta:
        verbose_name = gettext_lazy('Comment')
        verbose_name_plural = gettext_lazy('Comments')


class InviteLink(models.Model):
    link = models.CharField(max_length=100, verbose_name=gettext_lazy('Link'))
    valid_status = models.CharField(max_length=10, verbose_name=gettext_lazy('Is valid'))
    delegated_time = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Delegated at'))

    def generate(self):
        hash = md5.md5(str(random.getrandbits(128))).hexdigest() # Генерируем хеш
        self.link = hash
        self.valid_status = 'valid'
        self.save()
        return self

    #def __unicode__(self):
        #return self.id

    class Meta:
        verbose_name = gettext_lazy('Invite link')
        verbose_name_plural = gettext_lazy('Invite links')
