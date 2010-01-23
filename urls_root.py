# deprecated

from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'djata.views.respond'),
    (r'^(?P<view_name>[^/\.]*)(?=/|\.)', include('djata.urls_model')),
)

