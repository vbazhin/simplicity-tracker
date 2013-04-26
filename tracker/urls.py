#author: v.bazhin
#coding: utf-8

from django.conf.urls.defaults import patterns, include, url
from desk.views import index, show_issue, edit_issue, remove_issue, register, generate_link
from django.contrib import admin
from django.contrib.auth.views import login
from desk.views import logout

admin.autodiscover()

urlpatterns = patterns('',
    url('^$', index),
    url('^/$', index),
    url('(\d{0,6})/edit$', edit_issue),
    url('(\d{0,6})/remove$', remove_issue),
    url('^current$', index, {'fltr' : 'current'}),
    url('^failed$', index, {'fltr' : 'error'}),
    url('^done$', index, {'fltr' : 'done'}),
    url('^check$', index, {'fltr' : 'check'}),
    url('^success$', index, {'fltr' : 'success'}),
    url('^new$', index, {'fltr' : 'new'}),
    url('^taken$', index, {'fltr' : 'taken'}),
    url('^givenbyme$', index, {'fltr' : 'givenbyme'}),
    url('^add_task$', index, {'add_task' : True}),
    url(r'^(\d{0,6})$', show_issue),
    url(r'^accounts/login/',  login),
    url(r'^logout/',  logout),
    url(r'^register/(\w{0,32})$',  register),
    url(r'^register_link/$',  generate_link),
    url(r'^admin', include(admin.site.urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),
)