#author: v.bazhin
#coding: utf-8

from django.db import models
from django.contrib.auth.models import User
import datetime
import random
import md5
from django.utils.translation import pgettext
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.utils.html import escape
import filter_manager

STATUS_ATTRS = {
    'done' : {'icon' : 'ok', 'alert' : 'success'},
    'success': {'icon' : 'ok', 'alert' : 'success'},
    'closed': {'icon' : 'ban-circle', 'alert' : 'none'},
    'refused': {'icon' : 'ban-circle', 'alert' : 'error'},
    'taken': {'icon' : 'cog', 'alert' : 'info'},
    'new': {'icon' : 'exclamation-sign', 'alert' : 'new'},
    'error': {'icon' : 'remove', 'alert' : 'error'},
    'deleted': {'icon' : 'remove', 'alert' : 'error'},
    'edited': {'icon' : 'exclamation-sign', 'alert' : 'new'}
}


class Issue(models.Model):
    # Custom object manager initialization (to use "filter_set" to filter issues in views)
    objects = filter_manager.FilterManager()
    status_dict = (
        ('new', pgettext('issue condition', 'New')),
        ('taken', pgettext('issue condition', 'In progress')),
        ('refused', pgettext('issue condition', 'Rejected')),
        ('closed', pgettext('issue condition', 'Closed')),
        ('done', pgettext('issue condition', 'Done')),
        ('success', pgettext('issue condition', 'Success')),
        ('deleted', pgettext('issue condition', 'Deleted'))
    )

    label = models.CharField(max_length=100, verbose_name=gettext_lazy('Label'))
    text = models.TextField(blank=True, max_length=5000, verbose_name=gettext_lazy('Description'))
    given = models.DateTimeField(auto_now_add=True, verbose_name=gettext_lazy('Occurrence time'))
    is_expiration = models.BooleanField(blank=True,  max_length=3, verbose_name=gettext_lazy('Expiration'))
    expiration = models.DateTimeField(blank=True, null=True, verbose_name=gettext_lazy('Expiration date'))
    change_date = models.DateTimeField(auto_now=True, verbose_name=gettext_lazy('Change date'))
    status = models.CharField(blank=True, max_length=10, choices=status_dict, verbose_name=gettext_lazy('Current status'))
    receiver = models.ManyToManyField(User, blank=True, null=True, related_name = 'receiver', verbose_name=gettext_lazy('Receiver') )
    author = models.ForeignKey(User, related_name = 'author', verbose_name = gettext_lazy('Author'))

    def time_left(self):
        if self.is_expiration == True:
            time_left = self.expiration - datetime.datetime.now()
            return time_left

    def _save_new_data(self, data, request_user):
        receivers = data['receiver']
        if data['expdate'] != None:
            exp_exists = True
            # Join date and time
            exp = datetime.datetime.combine(data['expdate'], data['exptime'])
        else:
            exp_exists = False
            exp = None

        # think up this. Do not like
        issue = Issue(
                     id = self.id,
                     label = data['label'],
                     text = escape(data['text']),
                     given=datetime.datetime.now(),
                     is_expiration = exp_exists,
                     expiration=exp,
                     status='new',
                     author = request_user)
        issue.save()
        receivers = data['receiver']
        issue.receiver = receivers

    def add(self, data, request_user):
        self._save_new_data(data, request_user)

    def _add_status_comment(self, text, request_user):
        comment = Comment(is_status_comment=True,
                          text =text,
                          date = datetime.datetime.now(),
                          issue_id = self.id,
                          author = request_user)
        comment.save()

    def save_edited(self, data, request_user):
        """
        :param data:
        :param request_user:
        """
        self._save_new_data(data, request_user)
        self._add_status_comment('edited', request_user)

    def renew_status(self, new_data, request_user):
        self.status = new_data
        self.save()
        self._add_status_comment(self.status, request_user)

    def define_condition (self):
        if self.status == 'done':
            self.condition = pgettext('issue condition', 'On check')
        elif self.status == 'success':
            self.condition = pgettext('issue condition', 'Success')
        elif self.status == 'closed':
            self.condition = pgettext('issue condition', 'Closed')
        elif self.status == 'refused':
            self.condition = pgettext('issue condition', 'Rejected')
        elif self.status == 'deleted':
            self.condition = pgettext('issue condition', 'Deleted')
        else:
            if self.is_expiration == True:
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
        self.attrs = STATUS_ATTRS[self.status]
        if self.is_expiration == True:
            self.delta0 = self.expiration - self.given
            self.delta1 = datetime.datetime.now() - self.given
            self.time = (self.delta1.total_seconds()/self.delta0.total_seconds())*100
            self.given_time = self.given.time()
        return self.status

    def count_comments(self):
        self.comments_num = Comment.objects.filter(issue = self).count()

    def delete(self):
        self.status = 'deleted'
        self.save()

    def __unicode__(self):
        return self.label

    class Meta:
        verbose_name = gettext_lazy('Issue')
        verbose_name_plural = gettext_lazy('Issues')


class Comment(models.Model):
    text = models.TextField(max_length=1000, verbose_name=gettext_lazy('Text'))
    date = models.DateTimeField(verbose_name=gettext_lazy('Occurrence time'))
    issue = models.ForeignKey(Issue)
    author = models.ForeignKey(User)
    is_status_comment = models.BooleanField(default=False, verbose_name=gettext_lazy('Is status comment'))

    def get_text(self):
        text_messages = {
            'done' : gettext_lazy('The task is done, send for check'),
            'success': gettext_lazy('Completed'),
            'closed':  gettext_lazy('Closed'),
            'refused': gettext_lazy('Refused'),
            'taken': gettext_lazy( 'Accepted'),
            'new': gettext_lazy( 'Given again'),
            'deleted': gettext_lazy( 'Deleted'),
            'edited': gettext_lazy( 'Edited'),
        }
        if self.is_status_comment == True:
            self.status_attrs = STATUS_ATTRS[self.text]
        self.status_attr = STATUS_ATTRS[self.text]
        self.text = text_messages[self.text]
        return self.text

    def add(self, data, request_user, related_trad_id):
        comment = Comment(text = escape(data['text']),
                       date = datetime.datetime.now(),
                       issue_id = related_trad_id,
                       author = request_user)
        comment.save()

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

    def __unicode__(self):
        return self.id

    class Meta:
        verbose_name = gettext_lazy('Invite link')
        verbose_name_plural = gettext_lazy('Invite links')
