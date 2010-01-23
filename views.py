
# select
# where
# order
#.limit
#.ranges

# pagination
# interpolated page numbers
# read
# write
# authentication/authorization
#.django field declarations
# multiple customized views
# multiple customized parsers
# multiple customized formatters
#.json/get input
#.application keys
#.field links
#.field filters
#.grouping
#.bordered text format

# html table no display headers

import string
from types import ModuleType, FunctionType
from urllib import quote
from urllib2 import unquote
from os.path import join
from itertools import chain

from django.db.models import Model
from django.template import RequestContext, loader, TemplateDoesNotExist
from django.http import HttpResponse, HttpResponseServerError, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotAllowed
from django.core.exceptions import ObjectDoesNotExist, FieldError
import django.forms as forms
from django.conf import settings

from djata.python.names import *
from djata.python.orderedclass import \
     OrderedClass, OrderedProperty, OrderedMetaclass
from djata.paginate import page_groups
from djata.rules import *
from djata.exceptions import *
from djata.formats import *
from djata.fields import *

class ViewOptions(object):
    pass

class ViewMetaclass(OrderedMetaclass):

    def __init__(self, name, bases, attys):
        super(ViewMetaclass, self).__init__(name, bases, attys)

        if (
            self.__name__ == 'View' or
            self.__name__ == 'ViewBase' or (
                hasattr(self, 'Meta') and 
                hasattr(self.Meta, 'abstract') and
                self.Meta.abstract
            )
        ):
            return

        # discover the module that contains the model view
        if self.__module__ is None:
            module = None
        else:
            module = self.module = __import__(
                self.__module__,
                {}, {}, [self.__name__]
            )

        if hasattr(self, 'Meta'):
            class Meta(ViewOptions):
                pass
            for name, value in vars(self.Meta).items():
                if not name.startswith('__'):
                    setattr(Meta, name, value)
        else:
            self.Meta = ViewOptions
        meta = self.meta = self.Meta()
        meta.module = module

        meta.name = self.__name__
        # default to True if not yet defined
        meta.visible = getattr(meta, 'visible', True)

        # attempt to grab a model from the containing module's "models"
        #  value
        if not hasattr(meta, 'model') and hasattr(module, 'models'):
            model = meta.model = getattr(module.models, self.__name__)

        # objects

        # the user naturally has the option of defining their
        #  own objects and fields class values, but if they have
        #  a model, we use it as a source of those properties.
        if hasattr(meta, 'model'):
            model = meta.model
            if not hasattr(self, 'objects'):
                self.objects = model.objects
            if not hasattr(self, 'fields'):
                fields = model._meta._fields()
            if not hasattr(meta, 'verbose_name'):
                meta.verbose_name = str(model._meta.verbose_name)
            if not hasattr(meta, 'verbose_name_plural'):
                meta.verbose_name_plural = str(model._meta.verbose_name_plural)
        else:
            if not hasattr(meta, 'verbose_name'):
                meta.verbose_name = lower(self.__name__, '-')
            if not hasattr(meta, 'verbose_name_plural'):
                meta.verbose_name_plural = meta.verbose_name + 's'

        if not hasattr(self, 'objects'):
            raise Exception("View %s does not define its 'objects' "
                "property nor provide a model to obtain them from" % self)
        if not hasattr(meta, 'verbose_name'):
            raise Exception("Model view has no verbose name")
        if not hasattr(meta, 'verbose_name_plural'):
            meta.verbose_name_plural = '%ss' % meta.verbose_name


        # fields

        exclude_fields = set(getattr(meta, 'exclude_fields', ()))
        self.fields = [
            field for field in fields
            if field.name not in exclude_fields
        ]
        self.fields.extend([
            value.dub(self, name)
            for (name, value) in self._properties
            if isinstance(value, Field)
        ])
        if hasattr(meta, 'fields'):
            fields = dict(
                (field.name, field)
                for field in self.fields
            )
            self.fields = [
                fields[field_name]
                for field_name in meta.fields
            ]

        # build dictionaries for looking up properties
        for prefix, property in (
            ('action', 'actions'),
            ('method', 'methods'),
        ):
            pairs = [
                (name.split('_', 1)[1], value)
                for base in self.__mro__[::-1]
                for name, value in vars(base).items()
                if name.startswith('%s_' % prefix) and
                name.split('_', 1)[1] not in
                getattr(meta, 'exclude_%s' % property, ())
            ]
            setattr(self, '_%s' % property, [name for name, value in pairs])
            setattr(self, '_%s_lookup' % property, dict(pairs))

        # formatters
        for variable, type in (
            ('model_formats', ModelFormat),
            ('object_formats', ObjectFormat),
            ('model_parsers', ModelParser),
            ('object_parsers', ObjectParser),
            ('model_pages', ModelPage),
            ('object_pages', ObjectPage),
        ):
            exclude = getattr(meta, 'exclude_%s' % variable, ())
            pairs = [
                value.dub(self, name)
                for name, value in self._classes
                if issubclass(value, type)
            ]
            setattr(self, '_%s' % variable, [name for name, value in pairs])
            setattr(self, '_%s_lookup' % variable, dict(pairs))

        # index
        self.index = model._meta.pk
        if hasattr(meta, 'index'):
            self.index, ingore, ignore, ignore = \
                    model._meta.get_field_by_name(meta.index)

        # connect to a models view in the module
        if module is None:
            # if the views object is being created dynamically
            # (with views_from_models), there is no module associated
            # with the view instance; use the one provided on the
            # Meta class
            views = meta.views
        else:
            # otherwise, the views variable on the views module
            if not hasattr(module, 'views'):
                module.views = module.Views()
            views = module.views
        views.object_views[meta.verbose_name] = self
        name = meta.verbose_name_plural
        views.model_views[meta.verbose_name_plural.__str__()] = self
        self.views = views

class ViewBase(OrderedClass):

    __metaclass__ = ViewMetaclass

    content_types = {
        'application/x-www-urlencoded': 'urlencoded',
    }

    def __init__(self, request, view, pk, pks, format):
        self._request = request
        self._view = view
        self._pk = pk
        self._pks = pks
        self._format = format

    @classmethod
    def respond(
        self,
        request,
        view,
        pk = None,
        pks = None,
        format = None,
        more = None,
        responder = None,
        meta_page = None,
    ):

        pk, pks = self.normalize_pks(pk, pks)
        responder = self(request, view, pk, pks, format,)

        request.context['view'] = responder

        action = responder.negotiate_action()
        if action is not None:
            if action not in self._actions:
                raise NoSuchActionError(action)
            return self._actions_lookup[action](responder)
        method = request.method.lower()
        if method not in self._methods:
            raise NoSuchMethodError(
                "No action specified in the query-string, "
                "nor method provided for %s (from %s)" % (
                    repr(method),
                    repr(self._methods),
                )
            )
        return self._methods_lookup[method](responder)

    @classmethod
    def normalize_pks(self, pk = None, pks = None):
        to_python = self.index.to_python
        if pk is not None:
            pk = to_python(unquote(pk))
        if pks is not None:
            pks = [
                to_python(unquote(key))
                for key in pks.rstrip('&').split('&')
            ]
        return pk, pks

    def negotiate_action(self):
        request = self._request
        if 'action' in request.GET:
            return request.GET['action']
        for action in self._actions:
            if action in request.GET:
                return action


    # METHODS

    def method_get(self):
        return self.action_read()

    def method_put(self):
        return self.action_write()

    def method_post(self):
        # XXX django template for error with inspection
        #  of the available methods and actions.
        raise PostActionError(self._actions)


    # ACTIONS

    def action_read(self):
        self.authorize_read()
        request = self._request
        if request.method == 'POST':
            # allow JSON queries for read (eventually other formats too)
            request.JSON = json.loads(request.raw_post_data)
        return self.format()

    def action_write(self):
        if self._view == 'model':
            raise NotYetImplemented('write model (try the singular version).')
        elif self._view == 'object':
            try:
                object = self.get_object()
                # change
                self.authorize_change()
                fields = self.get_fields()
                updates = self.parse_object()
                for field in fields:
                    if field.attname in updates:
                        setattr(object, field.attname, updates[field.attname])
                object.save()
                self._object = object
            except self.meta.model.DoesNotExist:
                # add
                self.authorize_add()
                object = self.parse_object()
                object = self.meta.model.objects.create(**object)
                object.save()
                self._object = object
            return self.format()

    def action_add(self):
        self.authorize_add()
        if self._view == 'model':
            raise NotYetImplemented('cannot add object to model (try the singular version).')
        elif self._view == 'object':
            object = self.parse_object()
            object = self.meta.model.objects.create(**object)
            object.save()
            self._object = object
        return self.format()

    def action_change(self):
        self.authorize_change()
        if self._view == 'model':
            raise NotYetImplemented()
        elif self._view == 'object':
            object = self.get_object()
            fields = self.get_fields()
            updates = self.parse_object()
            for field in fields:
                if field.attname in updates:
                    setattr(object, field.attname, updates[field.attname])
            object.save()
            self._object = object
        return self.format()

    def action_delete(self):
        self.authorize_delete()
        if self._view == 'model':
            objects = self.get_objects()
            for object in objects:
                object.delete()
            return HttpResponse("they're gone", mimetype = 'text/plain')
        elif self._view == 'object':
            object = self.get_object()
            object.delete()
            return HttpResponse("it's gone", mimetype = 'text/plain')


    # FORMAT RESPONSES

    def format(self):
        format = self.negotiate_format()
        if self._view == 'model':
            if format not in self._model_formats:
                raise ModelFormatNotAvailable(format)
            formatter = self._model_formats_lookup[format]
        elif self._view == 'object':
            if format not in self._object_formats:
                raise ObjectFormatNotAvailable(format)
            formatter = self._object_formats_lookup[format]
        content_type = self.negotiate_format_content_type(formatter)
        content = formatter(self._request, self)
        return HttpResponse(content, mimetype = content_type)

    def negotiate_format(self):
        request = self._request
        format = self._format
        if hasattr(self.meta, 'format'):
            if format is not None and format != self.meta.format:
                raise NotExactSupportedFormatError(format, self.meta.format)
            return self.meta.format
        elif 'format' in request.JSON:
            format = request.JSON['format']
        elif 'format' in request.GET:
            format = request.GET['format']
        elif format is None:
            if 'ACCEPT' in request.META:
                self.content_types
                # XXX content negotiation
            format = getattr(self.meta, 'default_format', None)
            if format is None:
                format = getattr(self.meta.module, 'default_format', None)
            if format is None:
                raise NoFormatSpecifiedError()
        return format

    def negotiate_format_content_type(self, format):
        request = self._request
        content_type = format.content_type
        if 'content_type' in request.GET:
            content_type = str(request.GET['content_type'])
        if content_type is None:
            raise NoFormatContentTypeError(format.name)
        return content_type


    # PARSE REQUESTS

    def parse_object(self):
        parser = self.negotiate_parser()
        if parser not in self._object_parsers:
            raise ObjectParserNotAvailable(parser)
        parser = self._object_parsers_lookup[parser]
        return parser(self._request, self)

    def parse(self):
        parser = self.negotiate_parser()
        if self._view == 'model':
            if parser not in self._model_parsers:
                raise ModelParserNotAvailable(parser)
            parser = self._model_formats_lookup[format]
        elif self._view == 'object':
            if format not in self._object_formats:
                raise ObjectFormatNotAvailable(format)
            formatter = self._object_formats_lookup[format]
        raise ModelParserNotAvailable(format)

    def negotiate_parser(self):
        request = self._request
        parser = self.negotiate_format()
        if hasattr(self.meta, 'parser'):
            parser = self.meta.parser
        elif 'parser' in request.JSON:
            parser = reuqest.JSON['parser']
        elif 'parser' in request.GET:
            parser = request.GET['parser']
        elif 'CONTENT_TYPE' in request.META and request.META['CONTENT_TYPE']:
            parser = self.content_types[request.META['CONTENT_TYPE']]
        if parser is None:
            raise NoParserSpecifiedError()
        return parser


    # TABLE STUFF

    def select(self, objects):
        return objects

    def get_fields(self):
        request = self._request
        fields = self.fields

        fields = self.select(fields)

        select = None
        if 'select' in request.JSON:
            select = request.JSON['select']
        if 'select' in request.GET:
            select = request.GET['select'].split(',')
        if select is not None:
            field_dict = dict((field.name, field) for field in fields)
            non_existant_fields = [
                name for name in select
                if name not in field_dict
            ]
            if non_existant_fields:
                raise NonExistantFieldsError(non_existant_fields)
            fields = list(field_dict[name] for name in select)

        return fields

    def get_objects(self):
        if hasattr(self, '_objects'):
            return self._objects
        objects = self.__get_objects()
        objects = objects.all()
        objects = self.paginate_for_request(objects)
        return objects

    def get_object(self):
        request = self._request
        if hasattr(self, '_object'):
            return self._object
        try:
            return self.__get_objects().get()
        except ObjectDoesNotExist, exception:
            raise NoSuchObjectError()

    def __get_objects(self):
        request = self._request
        objects = self.objects

        if self._pk is not None:
            objects = objects.filter(**{
                '%s__exact' % self.index.name: self._pk
            })
        if self._pks is not None:
            objects = objects.filter(**{
                '%s__in' % self.index.name: self._pks
            })

        objects = self.order(objects)
        objects = self.filter(objects)
        objects = self.filter_for_user(objects)
        
        return objects

    def filter(self, objects):
        request = self._request

        for field in self.fields:

            name = field.name
            foreign = hasattr(field, 'rel') and hasattr(field.rel, 'to')

            if name in request.GET:
                value = field.to_python(request.GET[name])
                objects = objects.filter(**{name: value})

                # for foreign keys
                if foreign:
                    object = field.rel.to.objects.get(pk = value)

                    # add the field's object to the list of filters
                    #  for the rendering context
                    filters = request.context.get('filters', [])
                    filters.append(object)
                    request.context['filters'] = filters

                    request.context[name] = object

            if foreign:
                attname = field.attname
                if attname in request.GET:
                    value = field.to_python(request.GET[attname])
                    objects = objects.filter(**{name: value})

            if foreign:
                plural = field.rel.to._meta.verbose_name_plural.__str__()
            else:
                plural = field.name + 's'

            if plural in request.GET:
                values = [
                    field.to_python(unquote(value))
                    for value in request.GET[plural].split(",")
                ]
                objects = objects.filter(**{
                    '%s__in' % name: values
                })

        if 'where' in request.JSON:
            objects = objects.filter(R(request.JSON['where']))
        if 'where' in request.GET:
            objects = objects.filter(parse_rules(*request.GET.getlist('where')))

        return objects

    def filter_for_user(self, objects):
        return objects

    def paginate(self, objects, page_number, page_length):
        request = self._request
        from django.core.paginator import Paginator
        paginator = Paginator(objects, page_length)
        if page_number == 0:
            raise EmptyPageError(0)
        elif page_number < 1:
            page_number = paginator.num_pages + page_number + 1
        try:
            page = paginator.page(page_number)
        except:
            raise EmptyPageError(page_number)
        request.context['paginator'] = paginator
        request.context['page'] = page
        request.context['page_groups'] = page_groups(
            1,
            page.number,
            paginator.num_pages
        )
        return page.object_list

    @classmethod
    def page_ranges(self, paginator, page):
        page_range = paginator.page_range
        if len(page_ranges) < 10:
            return [page_range]
        elif page_number in page_ranges[:10]:
            return [page_range]
        elif page_number in page_ranges[-10:]:
            return [page_range]
        else:
            return [range(page_range - 2, page_range + 3)]


    def paginate_for_request(self, objects):
        request = self._request

        if hasattr(self.meta, 'page_length'):
            page_length = self.meta.page_length
            request.context['fixed_page_length'] = True
        else:
            default_page_length = getattr(self.meta, 'default_page_length', None)
            page_length = request.JSON.get(
                'pageLength',
                request.GET.get('page_length', default_page_length)
            )
            if page_length == '':
                page_length = None
            elif isinstance(page_length, basestring):
                try:
                    page_length = long(page_length) 
                except ValueError:
                    raise PageLengthMustBeNumberError(page_length)

        default_page_number = getattr(self.meta, 'default_page_number', 1)
        page_number = request.JSON.get(
            'page',
            request.GET.get('page', default_page_number)
        )
        if page_number == '':
            page_number = default_page_number
        if isinstance(page_number, basestring):
            try:
                page_number = long(page_number)
            except ValueError:
                raise PageNumberMustBeNumberError(page_number)

        require_pagination = getattr(self.meta, 'require_pagination', False)
        if page_length is None and require_pagination:
            raise PaginationRequiredError()

        if page_length is not None:
            if hasattr(self.meta, 'max_page_length'):
                if page_length > self.meta.max_page_length:
                    raise Exception("")
            objects = self.paginate(
                objects,
                page_number,
                page_length
            )

        return objects


    def order(self, objects):
        request = self._request

        field_names = []
        if 'order' in request.GET:
            field_names.extend(
                field_name
                for field_names in request.GET.getlist('order')
                for field_name in field_names.split(',')
            )
        if 'order' in request.JSON:
            field_names.extend(request.JSON['order'])

        if field_names:
            field_names = [
                "__".join(field_name.split('.'))
                for field_name in field_names
            ]
            objects = objects.order_by(*field_names)

        return objects


    # AUTHORIZATION

    def authorize_read(self):
        request = self._request
        if getattr(self.meta, 'insecure', False):
            return True
        if hasattr(self.meta.model._meta, 'get_read_permission'):
            if not user.is_authenticated():
                raise NotAuthenticatedError()
            if not request.user.has_permission('%s.%s' % (
                meta.app_label,
                meta.get_read_permission()
            )):
                raise PermissionDeniedError('read')
        elif 'can_read' in self.meta.model._meta.permissions:
            if not user.is_authenticated():
                raise NotAuthenticatedError()
            if not request.user.has_permission('%s.%s' % (
                meta.app_label,
                 'can_read',
            )):
                raise PermissionDeniedError('read')

    def authorize_add(self):
        request = self._request
        if getattr(self.meta, 'insecure', False):
            return True
        if not request.user.is_authenticated():
            raise NotAuthenticatedError()
        if not request.user.has_permission('%s.%s' % (
            meta.app_label,
            meta.get_add_permission()
        )):
            raise Exception("You cannot pass!")

    def authorize_change(self):
        request = self._request
        if getattr(self.meta, 'insecure', False):
            return True
        if not request.user.is_authenticated():
            raise NotAuthenticatedError()
        if not request.user.has_permission('%s.%s' % (
            meta.app_label,
            meta.get_change_permission()
        )):
            raise Exception("You cannot pass!")

    def authorize_delete(self):
        request = self._request
        if getattr(self.meta, 'insecure', False):
            return True
        if not request.user.is_authenticated():
            raise NotAuthenticatedError()
        if not request.user.has_permission('%s.%s' % (
            meta.app_label,
            meta.get_delete_permission()
        )):
            raise Exception("You cannot pass!")


    # stubs for TemplateFormats

    def process(self, request):
        pass

    def process_extra(self, request):
        pass


class View(ViewBase):

    # model formats
    class JsonModelFormat(JsonModelFormat): pass
    class JsonpModelFormat(JsonpModelFormat): pass
    class HtmlModelFormat(HtmlModelFormat): pass
    class BasicHtmlModelFormat(HtmlModelFormat): name = 'basic.html'
    class RawHtmlModelFormat(RawHtmlModelFormat): pass
    class UploadHtmlModelFormat(UploadHtmlModelFormat): pass
    class TextModelFormat(TextModelFormat): pass
    class TxtModelFormat(TextModelFormat): name = 'txt'
    class CsvModelFormat(CsvModelFormat): pass
    try:
        class XlsModelFormat(XlsModelFormat): pass
    except NameError:
         pass

    # object formats
    class HtmlObjectFormat(HtmlObjectFormat): pass
    class BasicHtmlObjectFormat(HtmlObjectFormat): name = 'basic.html'
    class VerifyDeleteHtmlObjectFormat(HtmlObjectFormat):
        name = 'verify-delete.html'
        template = 'djata/object.verify-delete.html'
    class RawHtmlObjectFormat(RawHtmlObjectFormat): pass
    class TextObjectFormat(TextObjectFormat): pass
    class TxtObjectFormat(TextObjectFormat): name = 'txt'
    class UrlencodedObjectFormat(UrlencodedObjectFormat): pass

    # model parsers
    class CsvModelParser(CsvModelParser): pass

    # object parsers
    class UrlencodedObjectParser(UrlencodedObjectParser): pass
    class UrlqueryObjectParser(UrlqueryObjectParser): pass


class Views(object):

    def __init__(self):
        self.model_views = {}
        self.object_views = {}

    def respond(
        self,
        request,
        view_name = None,
        pk = None,
        pks = None,
        format = None,
        more = None,
        meta_page = None,
    ):
        if view_name is not None:
            lookup = dict(
                (name, (view, responder))
                for responders, view in (
                    (self.model_views, 'model'),
                    (self.object_views, 'object'),
                )
                for name, responder in responders.items()
            )
            if view_name in lookup:
                view, responder = lookup[view_name]
                return responder.respond(
                    request,
                    view = view,
                    pk = pk,
                    pks = pks,
                    format = format,
                    more = more,
                    meta_page = meta_page,
                )
            raise NoSuchViewError(view_name)
        else:
            return self(request)

    template = 'djata/models.html'
    response_class = HttpResponse

    def __call__(self, request):
        self.process(request)
        self.process_extra(request)
        context = request.context
        template = loader.get_template(self.template)
        response = template.render(context)
        return self.response_class(response)

    def process(self, request):
        request.context['views'] = [
            view.meta
            for view in sorted(
                self.model_views.values(),
                key = lambda view: view._creation_counter
            )
            if view.meta.visible
        ]

    def process_extra(self, request):
        pass

def views_from_models(models, exclude = ()):
    views = Views()
    for model_name, model in vars(models).items():
        if model_name in exclude:
            continue
        if (
            not isinstance(model, type) or
            not issubclass(model, Model)
        ):
            continue
        ViewMetaclass(model_name, (View,), {
            "Meta": type('Meta', (object,), {
                "model": model,
                "views": views,
                "verbose_name": lower(model_name, '-'),
                "verbose_name_plural": lower(model_name, '-') + 's',
            }),
            "__module__": None
        })
    return views

class Url(object):

    def __init__(self, request = None, path = None, query = None, terminal = None):
        if request is not None:
            self.path = request.path
            self.query = request.GET.copy()
            self.terminal = None
        else:
            self.path = path
            self.query = query.copy()
            if terminal in self.query:
                del self.query[terminal]
            self.terminal = terminal

    def __delitem__(self, key):
        del self.query[key]

    def __getattr__(self, terminal):
        if terminal in self.query:
            del self.query[terminal]
        return Url(
            path = self.path,
            query = self.query,
            terminal = terminal,
        )

    def __unicode__(self):
        from itertools import chain
        return u'%s?%s' % (
            self.path,
            u"&".join(
                part for part in (
                    chain(
                        (
                            u"%s=%s" % (quote(key), quote(value))
                            for key, values in self.query.lists()
                            for value in values
                        ),
                        (
                            self.terminal,
                        )
                    )
                )
                if part is not None
            ),
        )

class Request(object):
    def __init__(self, _parent, **kws):
        super(Request, self).__init__()
        for name, value in kws.items():
            setattr(self, name, value)
        self._parent = _parent
    def __getattr__(self, *args):
        if self._parent is not None:
            return getattr(self._parent, *args)
        else:
            raise AttributeError(args[0])

def respond(request, **kws):
    return respond_kws(request, **kws)

def respond_kws(
    request,
    module = None,
    module_name = None,
    model = None,
    view_name = None,
    pk = None,
    pks = None,
    format = None,
    more = None,
    meta_page = None,
):

    context = RequestContext(request)
    context['settings'] = settings
    context['url'] = Url(request = request)
    request = Request(
        request,
        view_name = view_name,
        pk = pk,
        pks = pks,
        format = format,
        more = more,
        meta_page = meta_page,
        context = context,
        JSON = {},
    )

    request.context = RequestContext(request)
    request.context['settings'] = settings
    request.context['url'] = Url(request = request)
    request.JSON = {}

    if model is not None:
        if isinstance(model, basestring):
            pass
        else:
            pass
    if module is not None:
        if isinstance(module, basestring):
            pass
        else:
            pass

    try:
        try:
            module = __import__(module_name, {}, {}, [view_name])
            views = module.views
            return views.respond(
                request,
                view_name = view_name,
                pk = pk,
                pks = pks,
                format = format,
                more = more,
                meta_page = meta_page,
            )
        except Exception, exception:
            # render a text/plain exception for Python's urllib
            if (
                'HTTP_USER_AGENT' in request.META and
                'urllib' in request.META['HTTP_USER_AGENT']
            ):
                import traceback
                HttpResponseClass = HttpResponseServerError
                if isinstance(exception, UserError):
                    HttpResponseClass = exception.response_class
                return HttpResponseClass(traceback.format_exc(), 'text/plain')
            raise

    except UserError, exception:
        request.context['title'] = sentence(exception.__class__.__name__)
        request.context['error'] = exception
        try:
            template = loader.get_template(exception.template)
        except TemplateDoesNotExist:
            template = loader.get_template('djata/errors/base.html')
        response = template.render(request.context)
        return exception.response_class(response)

"""

::

    import app.models as models
    default_format = 'html'

    class Model(View):

        class Meta:

            abstract = False

            # the model object associated with the model view.  By default, this
            # is the model with the same name in the containing modeule's "models"
            # attribute.  See the above import declaration in the modeule, or you
            # can explicitly set each View's model like this
            model = Model

            format = 'json' # forces a format regardless of extension or content-type
            parser = 'json' # forces a parser regardless of content-type

            # if the user does not specify a the format they would like to receive
            default_format = 'json'
            # if the user does not specify the format they sent data with
            default_parser = 'json'

            # the URL component for a single object.  by default, this is inherited
            # from the model
            verbose_name = 'record'
            # the URL component for multiple objects from the model, by default, this
            # is also inherited from the model's plural verbose name.
            verbose_name_plural = 'records'

            fields = ('id', ...)       # expliccate the list of fields to provide
            methods = ('post', ...)    # explicate the list of methods to provide
            actions = ('add', ...)     # explicate the list of actions to provide
            model_parsers = ('json', ...)    # explicate the parsers to provide
            model_parsers = ('json', ...)    # explicate the parsers to provide
            object_formats = ('json', ...)    # explicate the formatters to provide
            object_formats = ('json', ...)    # explicate the formatters to provide

            exclude_fields = ('id', ...)
            exclude_methods = ('post', ...)
            exclude_actions = ('add', ...)
            exclude_model_parsers = ('json', ...)
            exclude_model_formatters = ('json', ...)
            exclude_object_parsers = ('json', ...)
            exclude_object_formatters = ('json', ...)

            index = 'name'           # the field to use instead of the pk for indexing
            start = '1'              # redirects to a record instead of providing
                                     #  a table view.

            # Pagination
            page_length = 10
            default_page = -1        # start from the end or the beginning, 0 by default
            default_page_length = 10
            require_pagination = False
            max_page_length = 100

        class HtmlModelFormat(HtmlModelFormat):
            name = 'html'
            template = 'app/model.html'

            def process_extra(self, request, view):
                pass

"""

