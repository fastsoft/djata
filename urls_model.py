
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^(?:\.(?P<format>[^/]*)|/|)$', 'djata.views.respond'),
    (r'^/', include('djata.urls_model_root')),
)

