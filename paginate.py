
from itertools import chain
from decimal import Decimal
from django.core.paginator import Paginator
from djata.python.topo_sort import classify

page_range = xrange(1, 1000)
page_number = 1

speed = 1

def pairs(values):
    values = iter(values)
    at = values.next()
    try:
        while True:
            prev = at
            at = values.next()
            yield (prev, at)
    except StopIteration:
        pass

def magnitudes(number):
    n = 1
    while n < number:
        yield n
        yield n * 5
        n *= 10

def _page_range_iter(start, at, stop):
    yield [start, at, stop]
    yield [
        number for number in range(at - 2, at + 3, 1)
        if number > start and number < stop
    ]
    for magnitude in reversed(list(magnitudes(stop))):
        values = range(
            start // magnitude * magnitude,
            (stop + magnitude + 1) // magnitude * magnitude,
            magnitude
        )
        maxes = list(n for n in values if n < at)
        mins = list(n for n in values if n > at)
        yield [value for value in values if value > start and value < stop]
        if maxes: start = max(maxes)
        if mins: stop = min(mins)

def _page_range_set(start, at, stop):
    return set(reduce(lambda x, y: x + y, _page_range_iter(start, at, stop)))

def page_range(start, at, stop):
    return sorted(_page_range_set(start, at, stop))

def page_groups(start, at, stop):
    page_numbers = _page_range_set(start, at, stop)
    adjacency = (
        (a, b)
        for a in page_numbers
        for b in page_numbers
        if a == b + 1 or a == b - 1
    )
    return sorted(
        sorted(row) for row in
        classify(page_numbers, gt_pairs = adjacency)
    )

def paginate(request, context, objects, default_length = 10, dimension = None):
    page_length = request.GET.get('page_length', default_length)
    paginator = Paginator(objects, page_length)
    page_number = request.GET.get('page_number', paginator.num_pages)
    page = paginator.page(page_number)
    context['paginator'] = paginator
    context['page'] = page
    return page.object_list

__all__ = ('page_range', 'page_groups', 'paginate')

if __name__ == '__main__':
    print page_range(1, 284, 15830)
    print page_groups(1, 284, 15830)

