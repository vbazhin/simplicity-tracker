#author: v.bazhin
#coding: utf-8

from django import forms
from markitup.widgets import MarkItUpWidget
from django.contrib.auth.models import User

class IssueForm(forms.Form):
    label = forms.CharField(max_length = 120, widget=forms.TextInput(attrs={
                                                'class': 'form-issue-label'}))
    text = forms.CharField(min_length=1, max_length=500, required=False,
                           widget=MarkItUpWidget())
    receiver = forms.ModelMultipleChoiceField(required=False,
                                              queryset=User.objects.all(),
                                              widget=forms.SelectMultiple(attrs=
                                              {'class': 'form-receivers'}))
    expdate = forms.DateField(required=False)
    exptime = forms.TimeField(required=False)
    timezone_offset = forms.CharField(required=False)


class CommentForm(forms.Form):
    text = forms.CharField(required=True,
                           widget=MarkItUpWidget(attrs={
                               'style': 'width: 99%; height:105px;'}))