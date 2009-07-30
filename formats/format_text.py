
from djata.formats import ObjectFormat, ModelFormat, TemplateFormat

class TextModelFormat(ModelFormat, TemplateFormat):
    name = 'text'
    content_type = 'text/plain'
    template = 'djata/model.text'

    def process(self, request, view):
        objects = view.get_objects()
        fields = view.get_fields()

        capitalize = 'capitalize' in request.GET
        display_header = request.GET.get('display_header', 'yes')
        if display_header not in ('yes', 'no'):
            raise ValueError()
        display_header = display_header == 'yes'

        field_names = [
            field.name
            for field in fields
        ]

        # transform list of dictionaries and column names to a lines in cells in rows
        rows = list(
            list(
                unicode(
                    default_if_none(field.value_from_object(object), "")
                ).expandtabs(4).replace(
                    u"\r", u""
                ).split(
                    u"\n"
                )
                for field in fields
            )
            for object in objects
        )

        # normalize the number of lines in each row
        rows = list(
            list(
                list_pad(cell, row_height)
                for cell in row
            )
            for row, row_height in rows_and_heights(rows)
        )

        # transpose lines in cells in rows to cell lines in rows
        rows = list(
            line
            for row in rows
            for line in zip(*row)
        )

        # calculate the width of each column based on the
        # widths of each column name and the widest line in each column
        if display_header:
            column_widths = list(
                max(len(column_name), len(rows) and max(
                    len(unicode(row[column_index]))
                    for row in rows
                ) or 1)
                for column_name, column_index in zip(
                    field_names,
                    range(len(field_names))
                )
            )
        else:
            column_widths = list(
                len(rows) and max(
                    len(unicode(row[column_index]))
                    for row in rows
                ) or 1
                for column_name, column_index in zip(
                    field_names,
                    range(len(field_names))
                )
            )


        # convert lines in rows to lines delimited by double spaces
        lines = list(
            u"  ".join(
                string_pad(row[column_index], column_width)
                for column_width, column_index in
                zip(column_widths, range(len(field_names)))
            )
            for row in rows
        )

        # add headings
        if display_header:
            lines = [
                u"  ".join(
                    string_pad(
                        capitalize and
                        column_name.upper() or
                        column_name,
                        column_width
                    )
                    for column_width, column_name in
                    zip(column_widths, field_names)
                ),
                u"  ".join(
                    u"-" * column_width
                    for column_width
                    in column_widths
                ),
            ] + lines

        request.context['content'] = u"".join(
            u"%s\n" % line for line in lines
        )

class TextObjectFormat(ObjectFormat, TemplateFormat):
    name = 'text'
    content_type = 'text/plain'
    template = 'djata/object.text'

    def process(self, request, view):
        context = request.context
        object = view.get_object()
        fields = view.get_fields()
        context['items'] = [
            [field.name, field.value_from_object(object)]
            for field in fields
        ]

def string_pad(cell, cell_width):
    if isinstance(cell, int) or isinstance(cell, long):
        return ("%s" % cell).rjust(cell_width)
    else:
        string = unicode(cell)
        return ("%s" % cell).ljust(cell_width)

def list_pad(cell, height):
    return cell + [u"" for n in range(height - len(cell))]

def rows_and_heights(rows):
    for row in rows:
        yield row, max(
            len(cell)
            for cell in row
        )

def default_if_none(value, default):
    if value is None: return default
    return value

