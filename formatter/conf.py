
import re

def conf(request, rows):
    column_names = request.column_names
    key_name = None
    value_name = None
    if len(column_names) == 2:
        key_name, value_name = column_names
    elif len(column_names) > 2:
        key_name = column_names[0]
        value_name = list(column_names[1:])
    if 'key' in request.JSON or 'key' in request.GET:
        key_name = request.JSON.get('key', request.GET['key'])
    if 'value' in request.JSON or 'value' in request.GET:
        value_name = request.JSON.get('value', request.GET['value'])
    assert key_name is not None, 'The column name of the key must be either impled from the first column name of the table, the first column name specified in select, or specified.'
    delimiter = request.JSON.get('delimiter', request.GET.get('delimiter', ':'))
    return 'text/plain', "".join([
        "%s=%s\n" % (
            namify(row[key_name]),
            format(row, value_name, delimiter)
        )
        for row in rows
    ])

def format(row, value_name, delimiter):

    if isinstance(value_name, list):
        cell = [
            row[key]
            for key in value_name
        ]
    else:
        cell = row[value_name]

    if isinstance(cell, tuple) or isinstance(cell, list):
        cell = delimiter.join("%s" % cell for cell in cell)

    return shenquote("%s" % cell)

def namify(name):
    return re.sub(r'[^\w]', '_', str(name)).upper()

shenquote_illegal = """'"${}\\\r\n"""

def shenquote(value):
    if any(letter in value for letter in shenquote_illegal):
        raise ValueError(
            "Characters in %s are not enquoteable in rc.conf files" %
            shenquote_illegal
        )
    if ' ' in value:
        return '"%s"' % value
    else:
        return value

def any(values):
    for value in values:
        if value:
            return value
