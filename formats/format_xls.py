
from pyExcelerator.Workbook import Workbook
from pyExcelerator import XFStyle
from cStringIO import StringIO
from datetime import *

def any(values):
    for value in values:
        if value:
            return value

def xls(request, rows):
    column_names = request.column_names

    string = StringIO()
    workbook = Workbook()
    worksheet = workbook.add_sheet('Data')
    for row_number, row in enumerate(rows):
        for column_number, column_name in enumerate(column_names):
            style = XFStyle()
            cell = row[column_name] or ''

            if any(isinstance(cell, type) for type in (date, time, datetime)):
                cell = str(cell)

            if not any(isinstance(cell, type) for type in (
                basestring,
                int, long, float,
                datetime, date, time,
            )):
                cell = str(cell)

            if isinstance(cell, basestring):
                cell = cell.replace("\r", "")

            worksheet.write(row_number, column_number, cell, style)
    workbook.save(string)
    
    content = string.getvalue()
    content_type = 'application/vnd.ms-excel'
    return content_type, content

