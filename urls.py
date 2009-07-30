# deprecated

from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^(?:\.(?P<type_name>.*))?$', 'djata.views.models'),
    (r'^(?P<model_name>[^/\.]*)(?:/|\.(?P<type_name>.*))?$', 'djata.views.model'),
    (r'^(?P<model_name>[^/\.]*)/(?P<pk>[^/&\.]+)(?:\.(?P<type_name>.*))?$', 'djata.views.record'),
    (r'^(?P<model_name>[^/\.]*)/(?P<pks>(?:[^/&\.]&?)+)(?:\.(?P<type_name>.*))?$', 'djata.views.records'),
)

