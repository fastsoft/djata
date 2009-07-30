
from djata.formats.format_html import HtmlModelFormat
from math import ceil

class HtmlChartModelFormat(HtmlModelFormat):
    name = 'chart.html'
    content_type = 'text/html'
    template = 'djata/model.chart.html'
    height = 400
    width = 600

    def process(self, request, view):
        context = request.context
        objects = view.get_objects()
        model_options = view.meta.model._meta

        height = self.height
        width = self.width
        x = model_options.get_field_by_name(self.x)[0]
        y = model_options.get_field_by_name(self.y)[0]
        series = model_options.get_field_by_name(self.series)[0]

        chart = [
            {
                'x': x.value_from_object(object),
                'y': y.value_from_object(object),
                'series': series.value_from_object(object),
                'object': object,
            }
            for object in objects
        ]
        max_y = chart and max(point['y'] for point in chart) or 0
        column_count = len(chart)
        column_width = int(ceil(width / column_count))
        width = column_width * column_count
        for point in chart:
            bottom_height = max_y == 0 and height or int(round(
                height * point['y'] / max_y
            ))
            top_height = height - bottom_height
            point.update({
                'top_height': top_height,
                'bottom_height': bottom_height,
            })

        context['max_y'] = max_y
        context['x'] = x
        context['y'] = y
        context['series'] = series
        context['chart'] = chart
        context['height'] = height
        context['width'] = width
        context['column_width'] = column_width

        super(HtmlChartModelFormat, self).process(request, view)

