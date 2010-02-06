
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'djata.views.respond'),
    (r'^~(?P<meta_page>.*)$', 'djata.views.respond'),
    (r'^(?P<pk>[^/&\.]+)/(?P<field_name>.*)$', 'djata.views.respond'),
    (r'^(?P<pk>[^/&\.]+)(?:\.(?P<format>[^/]*))?$', 'djata.views.respond'),
    (r'^(?P<pks>(?:[^/&\.]&?)+)(?:\.(?P<format>[^/]*))?$', 'djata.views.respond'),
)

