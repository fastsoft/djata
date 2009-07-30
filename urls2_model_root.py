
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'djata.views2.respond'),
    (r'^~(?P<meta_page>.*)$', 'djata.views2.respond'),
    (r'^(?P<pk>[^/&\.]+)/(?P<more>.*)$', 'djata.views2.respond'),
    (r'^(?P<pk>[^/&\.]+)(?:\.(?P<format>[^/]*))?$', 'djata.views2.respond'),
    (r'^(?P<pks>(?:[^/&\.]&?)+)(?:\.(?P<format>[^/]*))?$', 'djata.views2.respond'),
)

