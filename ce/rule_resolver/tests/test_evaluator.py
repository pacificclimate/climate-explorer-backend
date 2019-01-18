import pytest
from decimal import Decimal

from rule_resolver.scripts.evaluator import sub_str_value, cond_operand, \
    evaluate_parse_tree


@pytest.mark.parametrize(('data', 'filename', 'pt_d', 'expected'), [
    ('rule_ten', None, {'rule_ten': 10}, 10),
    ('temp_djf_iamean_s0p_hist', 'tests/test_data.json', None, -10)
])
def test_sub_str_value(data, filename, pt_d, expected):
    assert expected == sub_str_value(data, filename, pt_d)


@pytest.mark.parametrize(('data', 'filename', 'pt_d'), [
    ('rule_ten', None, {'rule_nine': 9}),
    ('not_a_variable', 'tests/test_data.json', None)
])
def test_sub_str_value_dict_error_handle(data, filename, pt_d):
    with pytest.raises(KeyError):
        sub_str_value(data, filename, pt_d)


@pytest.mark.parametrize(('data', 'filename', 'pt_d'), [
    ('temp_djf_iamean_s0p_hist', 'tests/not_a_file.json', None),
])
def test_sub_str_value_file_error_handle(data, filename, pt_d):
    with pytest.raises(FileNotFoundError):
        sub_str_value(data, filename, pt_d)


@pytest.mark.parametrize(('cond', 't_val', 'f_val', 'expected'), [
    (True, 1, 0, 1),
    (False, 1, 0, 0)
])
def test_cond_operand(cond, t_val, f_val, expected):
    assert expected == cond_operand(cond, t_val, f_val)


@pytest.mark.parametrize(('pt', 'filename', 'pt_d', 'expected'), [
    (('>', Decimal(5), Decimal(6)), None, None, False),
    (('+', 'temp_djf_iamean_s100p_hist', Decimal(6)),
     'tests/test_data.json', None, 26),
    (('&&', True, False), None, None, False),
    (('||', True, False), None, None, True),
    (('?', True, 1, 0), None, None, 1),
    (('!', True), None, None, False)
])
def test_evaluate_parse_tree(pt, filename, pt_d, expected):
    assert expected == evaluate_parse_tree(pt, filename, pt_d)
