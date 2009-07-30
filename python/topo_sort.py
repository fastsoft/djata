"""\
"""

from djata.python.iterkit import any, chain
from djata.python.wrap import wrap

def _topo_sorted(key, gt_dict_set, visited, inner_visited = None):

    if inner_visited is None:
        inner_visited = set()

    if key in inner_visited:
        raise Exception("cycle")

    visited.add(key)
    inner_visited.add(key)

    if key in gt_dict_set:
        for inner in gt_dict_set[key]:
            if inner in visited:
                continue
            for item in _topo_sorted(
                inner,
                gt_dict_set,
                visited,
                inner_visited
            ):
                yield item

    yield key

def _gt_dict_set(
    # you can provide any one of these arguments
    lt_dict = None,
    gt_dict = None,
    lt_pairs = None,
    gt_pairs = None,
    lt_dict_set = None,
    gt_dict_set = None,
    lt_matrix = None,
    gt_matrix = None,
    matrix_headers = None,
    inverse = False,
):
    if matrix_headers is not None:
        if lt_matrix is not None:
            lt_pairs = tuple(
                (matrix_headers[x], matrix_headers[y])
                for x in range(len(matrix_headers))
                for y in range(len(matrix_headers))
                if lt_matrix[x][y]
            )
        if gt_matrix is not None:
            gt_pairs = tuple(
                (matrix_headers[x], matrix_headers[y])
                for x in range(len(matrix_headers))
                for y in range(len(matrix_headers))
                if gt_matrix[x][y]
            )
    if lt_dict is not None:
        lt_pairs = lt_dict.items()
    if gt_dict is not None:
        gt_pairs = gt_dict.items()
    if lt_pairs is not None:
        lt_dict_set = dict_set_from_pairs(lt_pairs)
    if gt_pairs is not None:
        gt_dict_set = dict_set_from_pairs(gt_pairs)
    if lt_dict_set is not None:
        gt_dict_set = inverse_dict_set(lt_dict_set)
    if gt_dict_set is None:
        gt_dict_set = {}
    if inverse:
        gt_dict_set = inverse_dict_set(gt_dict_set)
    return gt_dict_set

def topo_sorted_iter(
    items,
    lt_dict = None,
    gt_dict = None,
    lt_pairs = None,
    gt_pairs = None,
    lt_dict_set = None,
    gt_dict_set = None,
    lt_matrix = None,
    gt_matrix = None,
    matrix_headers = None,
    inverse = False,
):
    """\
    """

    gt_dict_set = _gt_dict_set(
        lt_dict = lt_dict,
        gt_dict = gt_dict,
        lt_pairs = lt_pairs,
        gt_pairs = gt_pairs,
        lt_dict_set = lt_dict_set,
        gt_dict_set = gt_dict_set,
        lt_matrix = lt_matrix,
        gt_matrix = gt_matrix,
        matrix_headers = matrix_headers,
        inverse = inverse,
    )

    visited = set()

    for key in items:
        if key not in visited:
            for line in _topo_sorted(key, gt_dict_set, visited):
                yield line

topo_sorted = wrap(list)(topo_sorted_iter)

def classify_iter(
    items,
    lt_dict = None,
    gt_dict = None,
    lt_pairs = None,
    gt_pairs = None,
    lt_dict_set = None,
    gt_dict_set = None,
    lt_matrix = None,
    gt_matrix = None,
    matrix_headers = None,
    inverse = False,
):
    """\
    """

    gt_dict_set = _gt_dict_set(
        lt_dict = lt_dict,
        gt_dict = gt_dict,
        lt_pairs = lt_pairs,
        gt_pairs = gt_pairs,
        lt_dict_set = lt_dict_set,
        gt_dict_set = gt_dict_set,
        lt_matrix = lt_matrix,
        gt_matrix = gt_matrix,
        matrix_headers = matrix_headers,
        inverse = inverse,
    )

    visited = set()

    for key in items:
        if key not in visited:
            yield list(_topo_sorted(key, gt_dict_set, visited))

classify = wrap(list)(classify_iter)

def dict_set_from_pairs(pairs):
    result = {}
    for a, b in pairs:
        if not a in result:
            result[a] = set()
        result[a].add(b)
    return result

@wrap(dict)
def dict_set_from_dict(pairs):
    for a, b in pairs.items():
        yield a, set((b,))

@wrap(dict_set_from_pairs)
def inverse_dict_set(pairs):
    for a, bs in pairs.items():
        for b in bs:
            yield b, a

class relation(object):
    def __init__(self, function):
        self.function = function
    def __getitem__(self, key):
        return self.function(key)

if __name__ == '__main__':
    print topo_sorted([1,2,3])
    print topo_sorted([1,2,3], {1: 2, 2: 3})
    print topo_sorted([1,2,3], gt_dict = {3: 2, 2: 1})
    print topo_sorted([1,2,3], lt_pairs = [(1, 2), (2, 3)])
    print topo_sorted([1,2,3], gt_pairs = [(2, 1), (3, 2)])
    print topo_sorted([1,2,3], lt_dict_set = {1: [2, 3], 2: [3]})
    print topo_sorted([1,2,3], gt_dict_set = {3: (2, 1), 2: (1,)})
    print topo_sorted([1,2,3], lt_dict_set = {3: (2, 1), 2: (1,)}, inverse = True)
    print topo_sorted([1,2,3], matrix_headers = [1, 2, 3], lt_matrix = (
        (0, 1, 0),
        (0, 0, 1),
        (0, 0, 0),
    ))

