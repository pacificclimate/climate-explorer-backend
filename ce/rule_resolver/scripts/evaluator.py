import operator
import json


def get_json_var(filename, var):
    data = ''
    with open(filename) as json_data:
        data = json.load(json_data)
    return data[var]


def sub_str_value(data, filename, pt_d):
    if 'rule_' in data:
        # rule, return parse tree
        return pt_d[data]
    else:
        # variable, return value
        # this portion will likely change with the introduction of CE data
        return get_json_var(filename, data)


def cond_operand(cond, t_val, f_val):
    if cond:
        return t_val
    else:
        return f_val


def evaluate_parse_tree(pt, filename, pt_d):
    # base case
    if not isinstance(pt, tuple):
        if isinstance(pt, str):
            # string, needs substitution
            return evaluate_parse_tree(sub_str_value(pt, filename, pt_d),
                                       filename,
                                       pt_d)
        else:
            # constant
            return pt

    # operator lookup table
    ops = {'+' : operator.add,
           '-' : operator.sub,
           '*' : operator.mul,
           '/' : operator.truediv,
           '>' : operator.gt,
           '>=': operator.ge,
           '<' : operator.lt,
           '<=': operator.le,
           '==': operator.eq
          }

    # check operation
    op = pt[0]

    if op in ops:
        return ops[op](evaluate_parse_tree(pt[1], filename, pt_d),
                       evaluate_parse_tree(pt[2], filename, pt_d))
    elif op == '&&':
        return evaluate_parse_tree(pt[1], filename, pt_d) and \
               evaluate_parse_tree(pt[2], filename, pt_d)
    elif op == '||':
        return evaluate_parse_tree(pt[1], filename, pt_d) or \
               evaluate_parse_tree(pt[2], filename, pt_d)
    elif op == '!':
        return not evaluate_parse_tree(pt[1], filename, pt_d)
    elif op == '?':
        return cond_operand(evaluate_parse_tree(pt[1], filename, pt_d),
                            evaluate_parse_tree(pt[2], filename, pt_d),
                            evaluate_parse_tree(pt[3], filename, pt_d))
