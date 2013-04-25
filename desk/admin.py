#author: v.bazhin
#coding: utf-8

from django.contrib import admin
from desk.models import Trad, Comment, InviteLink


admin.site.register(Trad)
admin.site.register(Comment)
admin.site.register(InviteLink)

