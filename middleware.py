
from django.utils import simplejson
from django.http import HttpResponse

class Middleware(object):
    """\
    An optional base class for Middleware that permits but does not require
    a Middleware class to be used as a view function decorator.  Middleware
    can be used as a mixin to transform other middleware types into
    decorators.
    """

    def __init__(self, view = None):
        if view is not None:
            self.view = view

    def __call__(self, request, *args, **kws):

        if not hasattr(request, 'middleware'):
            request.middleware = set()
        if type(self) in request.middleware:
            return self.view(request, *args, **kws)
        request.middleware.add(type(self))

        has_process_request = hasattr(self, 'process_request')
        has_process_view = hasattr(self, 'process_view')
        has_process_response = hasattr(self, 'process_response')
        has_process_exception = hasattr(self, 'process_exception')

        try:
            if has_process_request:
                self.process_request(request)

            if has_process_view:
                response = self.process_view(request, self.view, *args, **kws)
                if response is not None:
                    return response

            response = self.view(request, *args, **kws)

        except Exception, exception:
            if has_process_exception:
                return self.process_exception(request, exception)
            else:
                raise

        if has_process_response:
            response_new = self.process_response(request, response)
            if response_new is not None:
                response = response_new

        if not isinstance(response, HttpResponse):
            raise ValueError("%s did not return an HttpResponse." % self.view)

        return response

class JsonRequestMiddleware(Middleware):
    """\
    a middleware or view decorator that adds a JSON attribute to
    the request that contains either JSON post data in Python
    form, or JSON data from a JSON attribute in a GET query parameter.
    guarantees that a JSON attribute will exist for any requests,
    falling back to an empty dictionary if nothing is specified.
    """

    def process_request(self, request):
        if (
            request.method == 'POST' and
            'json_post' in request.GET
        ):
            JSON = request.raw_post_data
        elif 'json' in request.GET:
            JSON = request.GET['json']
        else:
            JSON = '{}'
        JSON = simplejson.loads(JSON)
        request.JSON = JSON

