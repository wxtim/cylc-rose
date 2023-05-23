

from hypothesis import given
from hypothesis.strategies import *

from cylc.rose.jinja2_parser import _strip_leading_zeros, Parser

@given(value=integers(max_value=1000), pad=integers(min_value=1, max_value=15))
def test__strip_leading_zeros(value, pad):
    testval = f'\'{value:0{pad}d}\''
    _strip_leading_zeros(testval) == str(value)



@given(input_=one_of(
    integers(),
    floats(allow_nan=False, allow_infinity=False),
    text(min_size=1, alphabet=characters(
        blacklist_characters=''
    ))
))
def test_literal_eval_ints(input_):
    if isinstance(input_, str):
        x = f'"{input_}"'
    else:
        x = f'"{str(input_)}"'

    Parser().literal_eval(x)
