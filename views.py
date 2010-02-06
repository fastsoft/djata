
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
from django.http import HttpResponse, HttpResponseServerError, \
    HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotAllowed
from django.core.exceptions import ObjectDoesNotExist, FieldError
import django.forms as forms
from django.conf import settings

from djata.python.names import *
from djata.python.orderedclass import \
     OrderedClass, OrderedProperty, OrderedMetaclass
from djata.python.iterkit import unique
from djata.paginate import page_groups
from djata.rules import *
from djata.exceptions import *
from djata.formats import *
from django.db.models import ForeignKey

class ViewOptions(object):
    visible = True

class ViewMetaclass(OrderedMetaclass):

    def __init__(self, name, bases, attys):
        super(ViewMetaclass, self).__init__(name, bases, attys)

        if self.abstract:
            return

        # module
        self.init_module()
        # meta
        self.init_meta()
        # model
        self.init_model()
        # views, module.views
        self.init_views()

        # fields, objects, verbose_name, verbose_name_plural
        self.init_objects_fields_names()

        # pertaining to include_fields, exclude_fields, and
        # custom Field views
        self.init_fields() # fields
        self.init_actions_methods()
        self.init_formats_parsers()
        self.init_default_format()
        self.init_index()

        self.base_url = self.get('base_url')
        self.insecure = self.get('insecure', False)

        self.update_views()

    def get(self, name, value = None):
        # places to check, in priority order:
        # view, view.meta
        # views
        # model, model.meta
        # module
        model = self.model
        meta = self.meta
        model_meta = getattr(model, '_meta')
        views = getattr(self, 'views', None)
        return getattr(self, name,
            getattr(meta, name,
                getattr(views, name,
                    getattr(model, name,
                        getattr(model_meta, name,
                            getattr(self.module, name,
                                value
                            )
                        )
                    )
                )
            )
        )

    @property
    def abstract(self):
        return (
            hasattr(self, 'Meta') and 
            hasattr(self.Meta, 'abstract') and
            self.Meta.abstract
        )

    def get_module(self):
        # discover the module that contains the model view
        if self.__module__ is None:
            return
        return __import__(
            self.__module__,
            {}, {}, [self.__name__]
        )

    def init_module(self):
        self.module = self.get_module()

    @property
    def Views(self):
        return self.get('Views')

    def init_views(self):
        self.views = self.get_views()

    def get_views(self):
        views = getattr(self.meta, 'views', getattr(self.module, 'views', None))
        assert views is not None or self.module is not None, \
            'View %s does not reference its parent views.  ' \
            'The containing module is %s.' % (self, self.module)
        if views is None:
            Views = self.Views
            views = Views()
            if self.module is not None:
                # memoize
                self.module.views = views
        return views

    def update_views(self):
        views = self.views
        views.add_object_view(self.verbose_name, self)
        views.add_model_view(self.verbose_name_plural.__str__(), self)

    def init_meta(self):
        if 'Meta' in self.__dict__:
            class Meta(ViewOptions):
                pass
            for name, value in vars(self.__dict__['Meta']).items():
                if not name.startswith('__'):
                    setattr(Meta, name, value)
        else:
            Meta = ViewOptions
        self.meta = Meta()

    def get_model(self):
        # attempt to grab a model from the containing module's "models"
        #  value
        if hasattr(self.meta, 'model'):
            return self.meta.model
        if hasattr(self.module, 'models'):
            return getattr(self.module.models, self.__name__, None)

    def init_model(self):
        self.model = self.get_model()

    def init_objects_fields_names(self):
        model = self.model
        meta = self.meta
        model_meta = getattr(model, '_meta')

        self.objects = self.get('objects')
        self.fields = self.get('fields')

        assert model is not None or hasattr(meta, 'objects') or hasattr(self,
        'objects'), 'View %s does not define its "objects" property, a '\
        '"meta.objects" property, a "meta.model.objects" property, and the '\
        'containing module does not provide a "models" property with a model '\
        'with the same name' % self

        self.verbose_name = self.get('verbose_name')
        assert self.verbose_name is not None, 'View %s does not define a'\
        '"verbose_name", "Meta.verbose_name", provide a model with a'\
        '"verbose_name"'

        self.verbose_name_plural = self.get('verbose_name_plural') or\
        "%ss" % self.verbose_name

    def init_fields(self):
        meta = self.meta
        fields = self.fields

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
        if hasattr(meta, 'include_fields'):
            fields = dict(
                (field.name, field)
                for field in self.fields
            )
            self.fields = [
                fields[field_name]
                for field_name in meta.include_fields
            ]

    def init_actions_methods(self):
        meta = self.meta

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

    def init_formats_parsers(self):
        meta = self.meta

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
                if issubclass(value, type) and name not in exclude
            ]
            setattr(self, '_%s' % variable, tuple(unique(name for name, value in pairs)))
            setattr(self, '_%s_lookup' % variable, dict(pairs))

    def init_default_format(self):
        self.default_format = self.get('default_format')

    def init_index(self):
        model = self.model
        meta = self.meta

        # index
        self.index = model._meta.pk
        if hasattr(meta, 'index'):
            self.index, ingore, ignore, ignore = \
                    model._meta.get_field_by_name(meta.index)

class ViewBase(OrderedClass):

    __metaclass__ = ViewMetaclass

    class Meta:
        abstract = True

    content_types = {
        'application/x-www-urlencoded': 'urlencoded',
        'application/x-www-form-urlencoded': 'urlencoded',
    }

    def __init__(self, request, view, pk, pks, format):
        self._request = request
        self._view = view
        self._pk = pk
        self._pks = pks
        self._format = format

    def get_url_of_object(self, object):
        #return self.views.get_view_of_object(object).get_object_url(object)
        return self.views.get_url_of_object(object)

    def get_url_of_model(self, model):
        views = self.views
        view = views.get_view_of_model(model)
        return view.get_model_url()

    @classmethod
    def get_objects_url(self):
        return self.get_model_url()

    @classmethod
    def get_model_url(self):
        return '%s/%s.%s' % (
            self.base_url,
            self.verbose_name_plural,
            'html'
        )

    @classmethod
    def get_models_url(self):
        return '%s/' % self.base_url

    @classmethod
    def respond(
        self,
        request,
        view,
        pk = None,
        pks = None,
        format = None,
        field_name = None,
        responder = None,
        meta_page = None,
    ):

        pk, pks = self.normalize_pks(pk, pks)
        responder = self(request, view, pk, pks, format,)

        if field_name is not None:
            raise NotYetImplemented("Individual field names.")

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
            raise NotYetImplemented('write model (try writing the objects individually).')
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
            except self.model.DoesNotExist:
                # add
                self.authorize_add()
                object = self.parse_object()
                object = self.model.objects.create(**object)
                object.save()
                self._object = object
            return HttpResponseRedirect(self.get_url_of_object(object))

    def action_add(self):
        self.authorize_add()
        object = self.parse_object()
        object = self.model.objects.create(**object)
        object.save()
        self._object = object
        return HttpResponseRedirect(self.get_url_of_object(object))

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
        return HttpResponseRedirect(self.get_url_of_object(object))

    def action_delete(self):
        self.authorize_delete()
        if self._view == 'model':
            objects = self.get_objects()
            for object in objects:
                object.delete()
            return HttpResponseRedirect(self.get_url_of_model(self.model))
        elif self._view == 'object':
            object = self.get_object()
            object.delete()
            return HttpResponseRedirect(self.get_url_of_model(self.model))


    # FORMAT RESPONSES

    def format(self):
        format = self.negotiate_format()
        if self._view == 'model':
            if format not in self._model_formats:
                raise ModelFormatNotAvailable(format)
            formatter = self._model_formats_lookup[format]
        elif self._view == 'object':
            if format not in self._object_formats:
                raise ObjectFormatNotAvailable(format, self._object_formats)
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
                format = getattr(getattr(self, 'module', None), 'default_format', None)
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

    def get_fields(self):
        request = self._request
        fields = self.fields

        # eclude fields that refer to models that are
        # have no corresponding view
        fields = [
            field for field in fields
            if not isinstance(field, ForeignKey)
            or field.rel.to in self.meta.views.view_of_model
        ]

        select = None
        if 'select' in request.JSON:
            select = request.JSON['select']
        if 'select' in request.GET:
            select = request.GET['select'].split(',')
        if select is not None:
            field_dict = dict(
                (field.name, field)
                for field in fields
            )
            non_existant_fields = [
                name for name in select
                if name not in field_dict
            ]
            if non_existant_fields:
                raise NonExistantFieldsError(non_existant_fields)
            fields = list(field_dict[name] for name in select)

        return fields

    def get_child_fields(self):
        model = self.model
        model_meta = model._meta
        return [
            field
            for field, model, direct, m2m in (
                model_meta.get_field_by_name(name)
                for name in model_meta.get_all_field_names()
            ) if not direct and not m2m
        ]

    def get_related_fields(self):
        model = self.model
        model_meta = model._meta
        return [
            field
            for field, model, direct, m2m in (
                model_meta.get_field_by_name(name)
                for name in model_meta.get_all_field_names()
            ) if m2m
        ]

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
                plural = field.rel.to._meta.verbose_name_plural[:]
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

        field_names.append(self.model._meta.pk.name)

        field_names = [
            "__".join(field_name.split('.'))
            for field_name in field_names
        ]
        objects = objects.order_by(*field_names)

        return objects


    # AUTHORIZATION

    def authorize_read(self):
        request = self._request
        if self.insecure:
            return True
        if hasattr(self.model._meta, 'get_read_permission'):
            if not user.is_authenticated():
                raise NotAuthenticatedError()
            if not request.user.has_permission('%s.%s' % (
                meta.app_label,
                meta.get_read_permission()
            )):
                raise PermissionDeniedError('read')
        elif 'can_read' in self.model._meta.permissions:
            if not user.is_authenticated():
                raise NotAuthenticatedError()
            if not request.user.has_permission('%s.%s' % (
                meta.app_label,
                 'can_read',
            )):
                raise PermissionDeniedError('read')

    def authorize_add(self):
        request = self._request
        if self.insecure:
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
        if self.insecure:
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
        if self.insecure:
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

    default_format = 'html'

    class Meta:
        abstract = True

    # model formats
    class JsonModelFormat(JsonModelFormat):
        label = 'JSON'
        description = 'A data serialization format based on JavaScript'
    class JsonpModelFormat(JsonpModelFormat):
        label = 'JSONP'
        description = 'JSON with callbacks for cross domain script injection'
    class HtmlModelFormat(HtmlModelFormat):
        label = 'HTML'
    class BasicHtmlModelFormat(HtmlModelFormat):
        name = 'basic.html'
        label = 'Basic HTML'
        description = 'Normal HTML is often overridden to expose a more focused view; basic HTML hides nothing and exposes nothing extra.'
    class RawHtmlModelFormat(RawHtmlModelFormat):
        label = 'Raw HTML'
        description = 'An HTML fragment for AJAX or proxies'
    class UploadHtmlModelFormat(UploadHtmlModelFormat):
        label = 'Upload'
    class TextModelFormat(TextModelFormat):
        label = 'Formatted Text (<tt>text</tt>)'
    class TxtModelFormat(TextModelFormat):
        name = 'txt'
        label = 'Formatted Text (<tt>txt</tt>)'
    class CsvModelFormat(CsvModelFormat):
        label = 'Comma Separated Values Spreadsheet'
    try:
        class XlsModelFormat(XlsModelFormat):
            label = 'Excel Spreadsheet'
    except NameError:
         pass

    # object formats
    class HtmlObjectFormat(HtmlObjectFormat):
        label = 'HTML'
    class BasicHtmlObjectFormat(HtmlObjectFormat):
        name = 'basic.html'
        label = 'Basic HTML'
        description = 'Normal HTML is often overridden to expose a more focused view; basic HTML hides nothing and exposes nothing extra.'
    class RawHtmlObjectFormat(RawHtmlObjectFormat):
        label = 'Raw HTML'
        description = 'An HTML fragment for AJAX or proxies'
    class JsonObjectFormat(JsonObjectFormat):
        label = 'JSON'
        description = 'A data serialization format based on JavaScript'
    class JsonpObjectFormat(JsonpObjectFormat):
        label = 'JSONP'
        description = 'JSON with callbacks for cross domain script injection'

    class TextObjectFormat(TextObjectFormat):
        label = 'Formatted text (<tt>text</tt>)'
    class TxtObjectFormat(TextObjectFormat):
        name = 'txt'
        label = 'Formatted text (<tt>txt</tt>)'
    class UrlencodedObjectFormat(UrlencodedObjectFormat):
        label = 'URL encoded data'

    class AddHtmlObjectFormat(AddHtmlObjectFormat): pass
    class EditHtmlObjectFormat(EditHtmlObjectFormat): pass

    class VerifyDeleteHtmlObjectFormat(HtmlObjectFormat):
        name = 'verify-delete.html'
        template = 'djata/object.verify-delete.html'
        label = 'Delete&hellip;'
        is_action = True

    # model parsers
    class CsvModelParser(CsvModelParser): pass

    # object parsers
    class UrlencodedObjectParser(UrlencodedObjectParser): pass
    class UrlqueryObjectParser(UrlqueryObjectParser): pass

class Views(object):

    def __init__(self):
        self.model_views = {}
        self.model_view_names = {}
        self.object_views = {}
        self.object_view_names = {}
        self.view_of_model = {}

    def add_model_view(self, name, view):
        self.model_views[name] = view
        self.model_view_names[view] = name
        self.view_of_model[view.model] = view

    def add_object_view(self, name, view):
        self.object_views[name] = view
        self.object_view_names[view] = name
        self.view_of_model[view.model] = view

    def get_view_of_object(self, object):
        model = object._base_manager.model
        return self.view_of_model[model]

    def get_view_of_model(self, model):
        return self.view_of_model[model]

    def get_url_of_object(self, object, format = None):
        model = object._base_manager.model
        if model not in self.view_of_model:
            return
        view = self.view_of_model[model]
        index = view.index.value_from_object(object)
        view_name = self.object_view_names[view]
        url = view.base_url
        if url is None:
            return '#'
        if format is None and view.default_format:
            format = view.default_format
        if format is None:
            return '%s/%s/%s/' % (url, view_name, index,)
        else:
            return '%s/%s/%s.%s' % (url, view_name, index, format,)

    def respond(
        self,
        request,
        view_name = None,
        pk = None,
        pks = None,
        format = None,
        field_name = None,
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
                    field_name = field_name,
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

class ViewsFromModelsMetaclass(type):

    def __init__(self, name, bases, attys):
        super(ViewsFromModelsMetaclass, self).__init__(name, bases, attys)
        if self.__module__ == ViewsFromModelsMetaclass.__module__:
            return
        self.module = self.get_module()
        self.exclude = getattr(self, 'exclude', set())
        models = self.models = self.module.models
        views = self.module.views = self()
        views.init_views_from_models()

    def get_module(self):
        # discover the module that contains the model view
        if self.__module__ is None:
            return
        return __import__(
            self.__module__,
            {}, {}, [self.__name__]
        )

class ViewsFromModels(Views):
    __metaclass__ = ViewsFromModelsMetaclass

    def init_views_from_models(self):
        for model_name, model in vars(self.models).items():
            if model_name in self.exclude:
                continue
            if (
                not isinstance(model, type) or
                not issubclass(model, Model)
            ):
                continue
            ViewMetaclass(model_name, (View,), {
                "Meta": type('Meta', (object,), {
                    "model": model,
                    "views": self,
                    "verbose_name": lower(model_name, '-'),
                    "verbose_name_plural": lower(model_name, '-') + 's',
                }),
                "__module__": self.__module__
            })

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
    field_name = None,
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
        field_name = field_name,
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
                field_name = field_name,
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

