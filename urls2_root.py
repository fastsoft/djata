# deprecated

from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'djata.views2.respond'),
    (r'^(?P<model_name>[^/\.]*)(?=/|\.)', include('djata.urls2_model')),
)

