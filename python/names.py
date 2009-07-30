
# from https://cixar.com/svns/javascript/trunk/src/base.js
# by Kris Kowal

from re import compile as re

__all__ = (
    'lower',
    'upper',
    'camel',
    'title',
    'sentence',
    'split_name',
    'join_name',
)

split_name_expression = re(r'[a-z]+|[A-Z](?:[a-z]+|[A-Z]*(?![a-z]))|[.\d]+')

def split_name(name):
    return split_name_expression.findall(name)

digit_expression = re(r'\d')

def join_name(parts, delimiter = None):
    parts = list(parts)
    if delimiter is None: delimiter = '_';
    def reduction(parts, part):
        if (
            digit_expression.search(part) and
            parts and digit_expression.search(parts[-1])
        ):
            return parts + [delimiter + part]
        else:
            return parts + [part]
    return "".join(reduce(reduction, parts, []))

def lower(value, delimiter = None):
    if delimiter is None: delimiter = '_'
    return delimiter.join(
        part.lower()
        for part in split_name(value)
    )

def upper(value, delimiter = None):
    if delimiter is None: delimiter = '_'
    return delimiter.join(
        part.upper() for part in
        split_name(value)
    )

def camel(value, delimiter = None):
    return join_name(
        (
            n and part.title() or part.lower()
            for n, part in enumerate(split_name(value))
        ),
        delimiter
    )

def title(value, delimiter = None):
    return join_name(
        (
            part.title() for part in 
            split_name(value)
        ),
        delimiter
    )

def sentence(value, delimiter = None):
    if delimiter is None: delimiter = ' '
    return delimiter.join(
        n and part.lower() or part.title()
        for n, part in enumerate(split_name(value))
    )

def main():

    samples = (
        'CaseCase1_2',
        'caseCase1_2',
        'caseCase1_2',
        'case_case1_2',
        'case_case_1_2',
        'CASE_CASE1_2',
        'CASE_CASE1_2',
        'CASE_CASE_1_2',
        'case case 1 2',
    )

    oracles = (
        (lower, None, 'case_case_1_2'),
        (camel, None, 'caseCase1_2'),
        (title, None, 'CaseCase1_2'),
        (upper, None, 'CASE_CASE_1_2'),
    )

    for function, delimiter, oracle in oracles:
        for sample in samples:
            result = function(sample, delimiter) == oracle
            if not result:
                print function, sample, delimiter, function(sample, delimiter)

if __name__ == '__main__':
    main()

