
import csv as basecsv
from cStringIO import StringIO

def csv(request, rows):
    column_names = request.column_names

    kws = {}
    if 'excel' in request.GET:
        kws['dialect'] = 'excel'

    string = StringIO()
    writer = basecsv.writer(string, **kws)
    writer.writerow(column_names)
    writer.writerows(
        tuple(
            row[column_name]
            for column_name in column_names
        ) for row in rows
    )

    content = string.getvalue()
    content_type = 'text/csv'
    return content_type, content

