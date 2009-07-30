
from djata.formats import ModelFormat, ModelParser
import csv
from cStringIO import StringIO

class Csv(object):
    content_type = 'text/csv'
    name = 'csv'

class CsvModelFormat(ModelFormat, Csv):

    def __call__(self, request, view):
        fields = view.get_fields()
        objects = view.get_objects()

        kws = {}
        if 'excel' in request.GET:
            kws['dialect'] = 'excel'

        string = StringIO()
        writer = csv.writer(string, **kws)
        writer.writerow([
            field.name
            for field in fields
        ])
        writer.writerows([
            ([
                field.value_from_object(object)
                for field in fields
            ])
            for object in objects
        ])

        return string.getvalue()

class CsvModelParser(ModelParser, Csv):

    def __call__(self, request, view):
        fields = view.get_fields()

        kws = {}
        if 'excel' in requestGET:
            kws['dialect'] = 'excel'

        reader = csv.reader(StringIO(request.raw_post_data))

        if 'noheaders' in request.GET:
            headers = [
                field.name
                for field in fields
            ]
        else:
            headers = reader.next()

        return list(
            dict(zip(headers, row))
            for row in reader
        )

class CsvObjectParser(object):
    pass

