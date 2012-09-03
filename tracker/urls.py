#coding: utf-8
from django.conf.urls.defaults import patterns, include, url
from desk.views import index, show_trad, edit_trad, register, generate_link
from django.conf import settings
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.views import login
from desk.views import logout

urlpatterns = patterns('',
    # Examples:
    url('^$', index),
    url('^/$', index),
    url('(\d{0,6})/edit$', edit_trad),
    url('^current$', index, {'fltr' : 'current'}),
    url('^failed$', index, {'fltr' : 'error'}),
    url('^done$', index, {'fltr' : 'done'}),
    url('^check$', index, {'fltr' : 'check'}),
    url('^success$', index, {'fltr' : 'success'}),
    url('^new$', index, {'fltr' : 'new'}),
    url('^taken$', index, {'fltr' : 'taken'}),
    url('^givenbyme$', index, {'fltr' : 'givenbyme'}),
    url('^add_task$', index, {'add_task' : True}),
    url(r'^(\d{0,6})$', show_trad),
    url(r'^accounts/login/',  login),
    url(r'^logout/',  logout),
    #url(r'^register/$',  register),
    url(r'^register/(\w{0,32})$',  register),
    url(r'^register_link/$',  generate_link),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin', include(admin.site.urls)),
)