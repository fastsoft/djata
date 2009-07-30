
from xml.sax.saxutils import escape
from django.db.models import *
from django.template import Context, Template, loader
from os.path import dirname, join
from djata.python.names import lower

def cell(request, cell):
    models = request.models
    if (
        isinstance(cell, type) and
        Model in cell.__mro__ and
        models[lower(cell._meta.object_name, '-')] == cell
    ):
        return '<a href="%s.html">%s</a>' % (
            escape(lower(cell._meta.object_name, '-')),
            escape(lower(cell._meta.object_name, '-')),
        )
    return escape(
        ("%s" % cell)
        .replace("\r", "")
    ).replace("\n", "<br/>")

def html(request, rows):
    display_header = request.display_header
    column_names = request.column_names
    context = Context({
        'display_header': display_header,
        'column_names': column_names,
        'table': [
            [
                cell(request, row[column_name])
                for column_name in column_names
            ]
            for row in rows
        ],
    })
    if hasattr(request, 'template_name'):
        template = loader.get_template(request.tempalte_name)
    else:
        template = Template(file(join(dirname(__file__), 'html.html')).read())
    content = template.render(Context(context, False))
    return 'text/html', content

