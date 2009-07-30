
from os.path import join
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from djata.python.names import *

class UserError(Exception):

    @property
    def template(self):
        return join('djata', 'errors',
            lower(self.__class__.__name__, '_') + '.html'
        )

    response_class = HttpResponseBadRequest

class PostActionError(UserError):
    def __init__(self, actions):
        UserError.__init__(self)
        self.actions = actions

class ModelFormatNotAvailable(UserError): pass

class ObjectFormatNotAvailable(UserError): pass

class ModelParserNotAvailable(UserError): pass

class ObjectParserNotAvailable(UserError): pass

class NoFormatSpecifiedError(UserError): pass

class NoParserSpecifiedError(UserError): pass

class NoSuchObjectError(UserError): pass

class NoSuchMethodError(UserError): pass

class NoSuchActionError(UserError): pass

class NoFormatContentTypError(UserError): pass

class NotExactSupportedFormatError(UserError):
    def __init__(self, request_format, response_format):
        UserError.__init__(self, request_format)
        self.request_format = request_format
        self.response_format = response_format

class NoSuchViewError(UserError): pass

class PaginationRequiredError(UserError): pass

class PageLengthMustBeNumberError(UserError): pass

class PageNumberMustBeNumberError(UserError): pass

class EmptyPageError(UserError): pass

class NonExistantFieldsError(UserError):
    def __init__(self, fields):
        UserError.__init__(self)
        self.fields = fields

class NotAuthenticatedError(UserError):
    response_class = HttpResponseForbidden

class PermissionDeniedError(UserError):
    response_class = HttpResponseForbidden

class InvalidSortFieldError(UserError):
    def __init__(self, invalids, valids):
        UserError.__init__(self)
        self.invalids = invalids
        self.valids = valids

class TooManyObjectsError(UserError):
    pass

class NotYetImplemented(UserError):
    pass

class PageNotFoundError(UserError):
    pass


