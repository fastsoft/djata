
from djata.python.orderedclass import OrderedClass, OrderedProperty, OrderedMetaclass
from django.http import HttpResponse
from django.template import RequestContext, loader
from djata.python.names import *

class Format(OrderedClass):

    def __init__(self, view, name):
        self.view = view
        self.name = name

    @classmethod
    def dub(self, view, name):
        name = ".".join([
            part.lower()
            for part in split_name(name)
        ][1:])
        if hasattr(self, 'name'):
            name = self.name
        return name, self(view, name)

class ModelFormat(Format): pass
class ObjectFormat(Format): pass

class ObjectPage(Format): pass
class ModelPage(Format): pass

class TemplateFormat(object):
    response_class = HttpResponse

    def __call__(self, request, view):

        view.process(request)
        view.process_extra(request)
        self.process(request, view)
        self.process_extra(request, view)

        context = request.context
        template = loader.get_template(self.template)
        response = template.render(context)
        return self.response_class(response)

    def process(self, request, view):
        pass

    def process_extra(self, request, view):
        pass


class ParserMetaclass(OrderedMetaclass):
    def __init__(self, name, bases, attys):
        super(ParserMetaclass, self).__init__(name, bases, attys)
        if hasattr(self, 'name'):
            self.objects.append((self.name, self))

class Parser(OrderedClass):
    __metaclass__ = ParserMetaclass
    objects = []

    def __init__(self, view, name):
        self.view = view
        self.name = name

    @classmethod
    def dub(self, view, name):
        name = ".".join([
            part.lower()
            for part in split_name(name)
        ][1:])
        if hasattr(self, 'name'):
            name = self.name
        return name, self(view, name)

class ModelParser(Parser): pass
class ObjectParser(Parser): pass


from djata.formats.format_json import JsonModelFormat, JsonpModelFormat
from djata.formats.format_text import TextModelFormat, TextObjectFormat
from djata.formats.format_html import \
     HtmlObjectFormat, HtmlModelFormat,\
     RawHtmlObjectFormat, RawHtmlModelFormat,\
     UploadHtmlModelFormat
from djata.formats.format_csv import CsvModelFormat, CsvModelParser
try: from djata.formats.format_xls import XlsModelFormat, XlsObjectFormat
except ImportError: pass

from djata.formats.format_url import \
     UrlencodedObjectParser, UrlqueryObjectParser,\
     UrlencodedObjectFormat
from djata.formats.format_json import JsonObjectParser

