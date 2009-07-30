
class TextFormatter(object):
    def format_text(self, request, objects, fields):

        capitalize = False # XXX
        column_names = [
            field.appname
            for field in fields
        ]

        # transform list of dictionaries and column names to a lines in cells in rows
        rows = list(
            list(
                unicode(getattr(row, column_name)).expandtabs(4).replace(u"\r", u"").split(u"\n")
                for column_name in column_names
            )
            for row in objects
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
        column_widths = list(
            max(len(column_name), len(rows) and max(
                len(unicode(row[column_index]))
                for row in rows
            ) or 1)
            for column_name, column_index in zip(
                column_names,
                range(len(column_names))
            )
        )

        # convert lines in rows to lines delimited by double spaces
        lines = list(
            u"  ".join(
                string_pad(row[column_index], column_width)
                for column_width, column_index in
                zip(column_widths, range(len(column_names)))
            )
            for row in rows
        )

        # add headings
        if request.display_header:
            lines = [
                u"  ".join(
                    string_pad(
                        capitalize and
                        column_name.upper() or
                        column_name,
                        column_width
                    )
                    for column_width, column_name in
                    zip(column_widths, column_names)
                ),
                u"  ".join(
                    u"-" * column_width
                    for column_width
                    in column_widths
                ),
            ] + lines

        return u"".join(
            u"%s\n" % line for line in lines
        )

    format_txt = format_text

def text(request, rows):

    capitalize = request.capitalize
    column_names = request.column_names

    # transform list of dictionaries and column names to a lines in cells in rows
    rows = list(
        list(
            unicode(row[column_name]).expandtabs(4).replace(u"\r", u"").split(u"\n")
            for column_name in column_names
        )
        for row in rows
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
    column_widths = list(
        max(len(column_name), len(rows) and max(
            len(unicode(row[column_index]))
            for row in rows
        ) or 1)
        for column_name, column_index in zip(
            column_names,
            range(len(column_names))
        )
    )

    # convert lines in rows to lines delimited by double spaces
    lines = list(
        u"  ".join(
            string_pad(row[column_index], column_width)
            for column_width, column_index in
            zip(column_widths, range(len(column_names)))
        )
        for row in rows
    )

    # add headings
    if request.display_header:
        lines = [
            u"  ".join(
                string_pad(
                    capitalize and
                    column_name.upper() or
                    column_name,
                    column_width
                )
                for column_width, column_name in
                zip(column_widths, column_names)
            ),
            u"  ".join(
                u"-" * column_width
                for column_width
                in column_widths
            ),
        ] + lines

    return "text/plain", u"".join(
        u"%s\n" % line for line in lines
    )

txt = text

def string_pad(cell, cell_width):
    if isinstance(cell, int) or isinstance(cell, long):
        return u"%%%dd" % cell_width % cell
    else:
        string = unicode(cell)
        return u"%s%s" % (string, u" " * (cell_width - len(string)))

def list_pad(cell, height):
    return cell + [u"" for n in range(height - len(cell))]

def rows_and_heights(rows):
    for row in rows:
        yield row, max(
            len(cell)
            for cell in row
        )

