
from django.db.models import Model
from datetime import datetime
from django.utils.simplejson import *
from djata.python.wrap import wrap

def complex(data):
    if data is None:
        return data
    if not isinstance(data, type) and hasattr(data, 'json'):
        return data.json()
    if isinstance(data, type) and Model in data.__mro__:
        return data._meta.object_name
    if isinstance(data, list) or isinstance(data, tuple):
        return list(
            complex(datum)
            for datum in data
        )
    elif isinstance(data, dict):
        return dict(
            (complex(key), complex(value))
            for key, value in data.items()
        )
    elif isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, int):
        return data
    elif isinstance(data, long):
        return data
    elif isinstance(data, float):
        return data
    elif isinstance(data, basestring):
        return data
    else:
        return unicode(data)

dumps = wrap(dumps)(complex)

def json_base(request, rows):

    column_names = request.column_names

    use_meta = 'meta' in request.GET or request.JSON.get('meta', False)
    use_table = 'table' in request.GET or request.JSON.get('table', False)
    use_map = 'map' in request.GET or request.JSON.get('map', False)
    use_index = 'index' in request.GET or request.JSON.get('index', False)
    id = 'id'

    meta = {
        'length': len(rows),
        'column_names': request.column_names,
    }

    range = None
    if 'range' in request.GET:
        range = (int(n) for n in request.GET['range'].split(','))
    elif 'range' in request.JSON:
        range = request.JSON['range']

    start = 0
    if range is not None:
        start, stop = range
        rows = rows[start:stop]

    if use_index:
        use_meta = True
        meta['index'] = dict(
            (offset + start, row[id])
            for offset, row in enumerate(rows)
        )

    if request.limit is not None:
        rows = rows[:request.limit]

    rows = tuple(dict(
        (column_name, row[column_name])
        for column_name in request.column_names
    ) for row in rows)
    
    if use_table:
        if use_map:
            rows = dict(
                (row[id], tuple(
                    row[column_name]
                    for column_name in request.column_names
                ))
                for row in rows
            )
        else:
            rows = tuple(
                tuple(
                    row[column_name]
                    for column_name in request.column_names
                )
                for row in rows
            )
        use_meta = True
    else:
        if use_map:
            rows = dict(
                (row[id], row)
                for row in rows
            )

    meta['rows'] = rows

    if not use_meta:
        meta = rows

    content = dumps(meta)
    content_type = 'text/javascript'
    return content_type, content

def json(request, rows):
    content_type, content = json_base(request, rows)
    #content = "while(1);%s" % content
    return content_type, content

def jsonp(request, rows):
    content_type, content = json_base(request, rows)
    if 'callback' in request.GET:
        content = '%s(%s)' % (request.GET['callback'], content)
    elif 'callback' in request.JSON:
        content = '%s(%s)' % (request.JSON['callback'], content)
    return content_type, content

