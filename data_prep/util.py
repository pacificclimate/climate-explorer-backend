from datetime import datetime

# Time conversion functions

def s2d(s):
    return datetime.strptime(s, '%Y-%m-%d')


def ss2d(s):
    return datetime.strptime(s, '%Y%m%d')


def d2s(d):
    return datetime.strftime(d, '%Y-%m-%d')


def d2ss(d):
    return datetime.strftime(d, '%Y%m%d')



