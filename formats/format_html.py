
from djata.formats import TemplateFormat, ModelFormat, ObjectFormat, ObjectPage
from django.db.models import ForeignKey

class RawHtmlFormat(TemplateFormat):
    name = 'raw.html'
    content_type = 'text/html'

class HtmlFormat(RawHtmlFormat):
    name = 'html'

class RawHtmlObjectFormat(ObjectFormat, RawHtmlFormat):
    template = 'djata/object.raw.html'
    name = 'raw.html'

    def process(self, request, view):
        context = request.context
        object = view.get_object()
        fields = view.get_fields()
        context['object'] = object
        context['fields'] = fields
        context['items'] = [
            {
                'name': field.name,
                'value': field.value_from_object(object)
            }
            for field in fields
        ]

class HtmlObjectFormat(RawHtmlObjectFormat):
    template = 'djata/object.html'
    name = 'html'

class RawHtmlModelFormat(ModelFormat, HtmlFormat):
    template = 'djata/model.raw.html'
    name = 'raw.html'

    def process(self, request, view):
        context = request.context
        objects = view.get_objects()
        fields = view.get_fields()
        context['objects'] = objects
        context['fields'] = fields
        context['table'] = [
            [
                cell(field, object)
                for field in fields
            ]
            for object in objects
        ]
        context['field_names'] = [
            field.verbose_name
            for field in fields
        ]

class HtmlModelFormat(RawHtmlModelFormat):
    name = 'html'
    template = 'djata/model.html'

class UploadHtmlModelFormat(ModelFormat, TemplateFormat):
    template = 'djata/model.upload.html'
    name = 'upload.html'
    content_type = 'text/html'
    def process(self, request, view):
        request.context['formats'] = view._model_parsers

class HtmlAddPageMetaclass(getattr(ObjectPage, '__metaclass__', type)):
    def __init__(self, name, bases, attys):
        super(HtmlAddPageMetaclass, self).__init__(name, bases, attys)

class HtmlAddPage(ObjectPage):
    __metaclass__ = HtmlAddPageMetaclass
    name = 'add.html'
    template = 'djata/form.html'
    def process(self, request, view):
        context = request.context
        from django.forms import form_for_model
        context['form'] = form_for_model(view.meta.model)()
        super(HtmlAddPage, self).process(request, view)

class HtmlChangePage(ObjectPage):
    name = 'edit.html'
    template = 'djata/form.html'
    def process(self, request, view):
        context = request.context
        object = view.get_object()
        from django.forms import form_for_model
        context['form'] = form_for_model(view.meta.model)(instance = object)
        super(HtmlAddFormat, self).process(request, view)

def cell(field, object):
    value = field.value_from_object(object)
    if value is None:
        return
    else:
        return Cell(field, object, value)
    
class Cell(object):
    def __init__(self, field, object, value):
        self.field = field
        self.object = object
        self.value = value
    def __unicode__(self):
        return unicode(self.value)
    @property
    def url(self):
        if not isinstance(self.field, ForeignKey):
            return
        return '#'

