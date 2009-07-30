"""\
provides tools for exposing a restful data API
to Django tables.
"""

from django.conf.urls.defaults import include

def djata(name, module_name, model_name = None):
    if model_name is not None:
        return (r'%s(?=/|\.)' % name, include('djata.urls2_model'), {
            'module_name': module_name,
            'model_name': model_name,
        })
    else:
        return (r'%s(?=/|\.)' % name, include('djata.urls2'), {
            'module_name': module_name,
        })

