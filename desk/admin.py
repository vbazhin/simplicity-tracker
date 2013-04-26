#author: v.bazhin
#coding: utf-8

from django.contrib import admin
from desk.models import Issue, Comment, InviteLink


admin.site.register(Issue)
admin.site.register(Comment)
admin.site.register(InviteLink)

