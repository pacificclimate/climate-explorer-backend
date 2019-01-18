from argparse import ArgumentParser
import csv

from resolver import build_parse_tree
from evaluator import evaluate_parse_tree


def read_csv(filename):
    rules_dict = {}
    with open(filename, 'r') as rules_file:
        csv_reader = list(csv.DictReader(rules_file, delimiter=';'))
        for row in csv_reader:
            # make sure we are only getting the id and condition
            # add rule prefix
            rule = 'rule_{}'.format(list(row.values())[0])
            cond = list(row.values())[1]
            rules_dict[rule] = cond

    return rules_dict


def print_dict(d):
    for key, value in d.items():
        print('Key: {0}\nValue: {1}\n'.format(key, value))


def main():
    # I expect this will be reworked into method params
    parser = ArgumentParser()
    parser.add_argument('-c', '--csv', help='CSV file containing rules',
                        required=True)
    parser.add_argument('-f', '--filename', help='JSON file containing data',
                        required=True)
    args = parser.parse_args()

    # read csv
    rules_dict = read_csv(args.csv)

    # create parse tree dictionary
    parse_tree_dict = {}
    for rule, condition in rules_dict.items():
        # exclude
        try:
            parse_tree_dict[rule] = build_parse_tree(condition)
        except SyntaxError as e:
            print('{}, rule will be excluded'.format(e))

    # evaluate parse trees
    result_dict = {}
    for rule, pt in parse_tree_dict.items():
        result_dict[rule] = evaluate_parse_tree(pt, args.filename,
                                                parse_tree_dict)

    # print for now
    print_dict(result_dict)


if __name__ == '__main__':
    main()
