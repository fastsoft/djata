
from djata.formats import TemplateFormat, ModelFormat, ObjectFormat, ObjectPage
from django.forms import ModelForm
from django.db.models import ForeignKey

def form_for_model(model):
    return type(model.__class__.__name__ + 'Form', (ModelForm,), {
        "Meta": type("Meta", (object,), {
            "model": model,
        })
    })

class RawHtmlFormat(TemplateFormat):
    name = 'raw.html'
    content_type = 'text/html'

class HtmlFormat(RawHtmlFormat):
    name = 'html'

class RawHtmlObjectFormat(ObjectFormat, RawHtmlFormat):
    template = 'djata/object.raw.html'
    name = 'raw.html'
    label = 'Raw HTML'

    def process(self, request, view):
        context = request.context
        object = view.get_object()
        fields = view.get_fields()
        parent_fields = None # XXX
        child_fields = view.get_child_fields()
        related_fields = view.get_related_fields()
        context['view'] = view
        context['object'] = object
        context['fields'] = fields
        context['related_fields'] = related_fields
        context['child_fields'] = related_fields
        context['items'] = [
            {
                'name': field.name,
                'value': cell(field, object, view)
            }
            for field in fields
        ]
        context['child_items'] = [
            {
                'name': field.var_name,
                'items': [
                    ChildCell(item, view)
                    for item in
                    field.model.objects.filter(**{
                        field.field.name: object,
                    })
                ]
            }
            for field in child_fields
        ]
        context['related_items'] = [
            {
                'name': field.name,
                'items': [
                ]
            }
            for field in related_fields
        ]

class HtmlObjectFormat(RawHtmlObjectFormat):
    template = 'djata/object.html'
    name = 'html'
    label = 'HTML'

    def process(self, request, view):
        formats = [
            view._object_formats_lookup[name]
            for name in view._object_formats
        ]
        request.context['formats'] = [
            format for format in formats
            if not getattr(format, 'is_action', False)
        ]
        request.context['actions'] = [
            format for format in formats
            if getattr(format, 'is_action', False)
        ]
        return super(HtmlObjectFormat, self).process(request, view)

class RawHtmlModelFormat(ModelFormat, HtmlFormat):
    template = 'djata/model.raw.html'
    name = 'raw.html'
    label = 'Raw HTML'

    def process(self, request, view):
        context = request.context
        objects = view.get_objects()
        fields = view.get_fields()
        context['objects'] = objects
        context['fields'] = fields
        context['table'] = [
            [
                cell(field, object, view)
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
    label = 'HTML'
    template = 'djata/model.html'

    def process(self, request, view):
        formats = [
            view._model_formats_lookup[name]
            for name in view._model_formats
        ]
        request.context['formats'] = [
            format for format in formats
            if not getattr(format, 'is_action', False)
        ]
        request.context['actions'] = [
            format for format in formats
            if getattr(format, 'is_action', False)
        ]
        return super(HtmlModelFormat, self).process(request, view)


class UploadHtmlModelFormat(ModelFormat, TemplateFormat):
    template = 'djata/model.upload.html'
    name = 'upload.html'
    label = 'Upload'
    content_type = 'text/html'
    is_action = True
    def process(self, request, view):
        request.context['formats'] = view._model_parsers

class EditHtmlObjectFormat(HtmlObjectFormat):
    template = 'djata/object.edit.html'
    name = 'edit.html'
    label = 'Edit'
    is_action = True
    def process(self, request, view):
        object = view.get_object()
        Form = form_for_model(view.model)
        request.context['form'] = Form(instance = object)
        super(EditHtmlObjectFormat, self).process(request, view)

class AddHtmlObjectFormat(HtmlModelFormat):
    template = 'djata/object.add.html'
    name = 'add.html'
    label = 'Add'
    is_action = True
    def process(self, request, view):
        Form = form_for_model(view.model)
        request.context['form'] = Form()
        super(AddHtmlObjectFormat, self).process(request, view)

def cell(field, object, view):
    value = get_object_field_value(object, field)
    if value is None:
        return
    else:
        return Cell(field, object, view, value)
    
class Cell(object):
    def __init__(self, field, object, view, value):
        self.field = field
        self.object = object
        self.view = view
        self.value = value
    def __unicode__(self):
        return unicode(self.value)
    @property
    def url(self):
        if self.field.primary_key:
            return self.view.get_url_of_object(self.object)
        elif isinstance(self.field, ForeignKey):
            return self.view.get_url_of_object(self.value)

class ChildCell(object):
    def __init__(self, object, view):
        self.object = object
        self.view = view
    def __unicode__(self):
        return unicode(self.object)
    @property
    def url(self):
        return self.view.get_url_of_object(self.object)

def get_object_field_value(object, field):
    value = field.value_from_object(object)
    if isinstance(field, ForeignKey) and value is not None:
        value = field.rel.to.objects.get(pk = value)
    return value

