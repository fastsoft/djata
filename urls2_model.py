
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^(?:\.(?P<format>[^/]*)|/|)$', 'djata.views2.respond'),
    (r'^/', include('djata.urls2_model_root')),
)

