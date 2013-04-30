#author: v.bazhin
#coding: utf-8

from django_select2.fields import Select2MultipleWidget
from markitup.widgets import MarkItUpWidget
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy
from django import forms

class IssueForm(forms.Form):
    label = forms.CharField(max_length = 120, widget=forms.TextInput(attrs={
                                                'class': 'form-issue-label',
                                                'tabindex': '1'}))
    text = forms.CharField(min_length=1, max_length=500, required=False,
                           widget=MarkItUpWidget(attrs={'tabindex': '2'}))
    receiver = forms.ModelMultipleChoiceField(required=False,
                                              queryset=User.objects.all(),
                                              widget=Select2MultipleWidget(attrs=
                                                {'class': 'form-receivers',
                                                 'placeholder': gettext_lazy('leave empty for a common task',),
                                                 'tabindex': '3'
                                                },
                                               select2_options={
                                                  'closeOnSelect': True,}))
    expdate = forms.DateField(required=False)
    exptime = forms.TimeField(required=False)
    timezone_offset = forms.CharField(required=False)


class CommentForm(forms.Form):
    text = forms.CharField(required=True,
                           widget=MarkItUpWidget(attrs={
                               'style': 'width: 99%; height:105px;'}))