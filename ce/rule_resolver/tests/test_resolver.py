import pytest
from decimal import Decimal

from rule_resolver.scripts.resolver import build_parse_tree


@pytest.mark.parametrize(('data', 'expected'), [
    ('''(test_var_1 > rule_test_1)''', ('>', 'test_var_1', 'rule_test_1')),
    (
        '''!rule_2b && 5 > 6''',
        ('&&', ('!', 'rule_2b'), ('>', Decimal(5), Decimal(6)))
    ),
    ('''rule_3c ? 1:0''', ('?', 'rule_3c', Decimal(1), Decimal(0)))
])
def test_build_parse_tree(data, expected):
    assert expected == build_parse_tree(data)


@pytest.mark.parametrize(('data', 'expected'), [
    (
        ['''rule_1a and rule_1b''', '''rule_1a && rule_1b'''],
        [('&&', 'rule_1a', 'rule_1b')]
    )
])
def test_build_parse_tree_error_handle(data, expected):
    test_output = []
    for rule in data:
        try:
            test_output.append(build_parse_tree(rule))
        except SyntaxError as e:
            print('Error has occured: {}'.format(e))
    assert test_output == expected
