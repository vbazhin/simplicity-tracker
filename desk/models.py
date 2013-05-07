#author: v.bazhin
#coding: utf-8

from django.contrib.auth.models import User
from django.utils.translation import pgettext
from django.utils.translation import gettext_lazy
from django.db import models
from django.utils.html import escape
import filter_manager
import datetime
import md5
import random


STATUS_ATTRS = {
    'done' : {'icon' : 'ok', 'alert' : 'success'},
    'success': {'icon' : 'ok', 'alert' : 'success'},
    'closed': {'icon' : 'minus-sign', 'alert' : 'none'},
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

    label = models.CharField(max_length=100,
                             verbose_name=gettext_lazy('Label'))
    text = models.TextField(blank=True,
                            max_length=5000,
                            verbose_name=gettext_lazy('Description'))
    given = models.DateTimeField(auto_now_add=True,
                                 verbose_name=gettext_lazy('Occurrence time'))
    is_expiration = models.BooleanField(blank=True,
                                        max_length=3,
                                        verbose_name=gettext_lazy('Expiration'))
    expiration = models.DateTimeField(blank=True,
                                      null=True,
                                      verbose_name=gettext_lazy('Expiration date'))
    change_date = models.DateTimeField(auto_now=True,
                                       verbose_name=gettext_lazy('Change date'))
    status = models.CharField(blank=True,
                              max_length=10,
                              choices=status_dict,
                              verbose_name=gettext_lazy('Current status'))
    receiver = models.ManyToManyField(User,
                                      blank=True,
                                      null=True,
                                      related_name = 'receiver',
                                      verbose_name=gettext_lazy('Receiver') )
    author = models.ForeignKey(User,
                               related_name = 'author',
                               verbose_name = gettext_lazy('Author'))


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
        self._save_new_data(data, request_user)
        self._add_status_comment('edited', request_user)

    def renew_status(self, new_data, request_user):
        self.status = new_data
        self.save()
        self._add_status_comment(self.status, request_user)

    def define_condition (self):
        """
        This function manages condition of issue
        defines how the issue will be displayed
        and compares expiration time and current time and automatically update it status
        """
        unactive_statuses = {
            'done' : 'On check',
            'success': 'Success',
            'closed': 'Closed',
            'refused': 'Rejected',
            'deleted': 'Deleted',
        }
        active_statuses = {
            'new': 'New',
            'taken': 'In progress',
        }
        if self.status in unactive_statuses:
            self.condition = pgettext('issue condition', unactive_statuses[self.status])
        elif self.is_expiration == True:
            # Do i really need this?
            self.time_left = self.expiration - datetime.datetime.now()
            self.leftdays = self.time_left.days
            self.lefthours = self.time_left.seconds/3600
            self.leftminutes = self.time_left.seconds/60
            # If time is not expired
            if self.time_left > datetime.timedelta(0) and self.status in active_statuses:
                time_total = self.expiration - self.given
                time_passed = datetime.datetime.now() - self.given
                self.time = (time_passed.total_seconds()/time_total.total_seconds())*100
                self.given_time = self.given.time()
                self.condition = pgettext('issue condition', active_statuses[self.status])
            else:
                self.condition = pgettext('issue condition', 'Failed')
                if self.status != 'error': self.status = 'error'
        elif self.status in active_statuses:
            self.condition = pgettext('issue condition', active_statuses[self.status])
        self.attrs = STATUS_ATTRS[self.status]
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
    text = models.TextField(max_length=1000,
                            verbose_name=gettext_lazy('Text'))
    date = models.DateTimeField(verbose_name=gettext_lazy('Occurrence time'))
    issue = models.ForeignKey(Issue)
    author = models.ForeignKey(User)
    is_status_comment = models.BooleanField(default=False,
                                            verbose_name=gettext_lazy('Is status comment'))

    def get_text(self):
        text_messages = {
            'done' : '<i class="icon-check"></i>' + str(gettext_lazy('The task is done, sent for check')),
            'success': '<i class="icon-ok"></i>' + str(gettext_lazy('Completed')),
            'closed':  '<i class="icon-minus-sign"></i>' + str(gettext_lazy('Closed')),
            'refused': '<i class="icon-ban-circle"></i>' + str(gettext_lazy('Refused')),
            'taken': '<i class="icon-cog"></i>' + str(gettext_lazy('Accepted')),
            'new': '<i class="icon-refresh"></i>' + str(gettext_lazy('Given again')),
            'deleted': '<i class="icon-remove"></i>' + str(gettext_lazy('Deleted')),
            'edited': '<i class="icon-edit"></i>' + str(gettext_lazy('Edited')),
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
    link = models.CharField(max_length=100,
                            verbose_name=gettext_lazy('Link'))
    valid_status = models.CharField(max_length=10,
                                    verbose_name=gettext_lazy('Is valid'))
    delegated_time = models.DateTimeField(auto_now_add=True,
                                          verbose_name=gettext_lazy('Delegated at'))

    def generate(self):
        # Generate hash
        self.link = md5.md5(str(random.getrandbits(128))).hexdigest()
        self.valid_status = 'valid'
        self.save()
        return self

    def __unicode__(self):
        return self.id

    class Meta:
        verbose_name = gettext_lazy('Invite link')
        verbose_name_plural = gettext_lazy('Invite links')
