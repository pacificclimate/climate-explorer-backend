from datetime import datetime

# Time conversion functions

def s2d(s):
    return datetime.strptime(s, '%Y-%m-%d')


def ss2d(s):
    return datetime.strptime(s, '%Y%m%d')


def d2s(date):
    '''Equivalent of datetime.strftime(d, '%Y-%m-%d'), but
    gets around the idiotic Python 2.7 strftime limitation of year >= 1900'''
    return '{y}-{m}-{d}'.format(y=str(date.year), m=str(date.month).zfill(2), d=str(date.day).zfill(2))


def d2ss(date):
    '''Equivalent of datetime.strftime(d, '%Y%m%d'), but
    gets around the idiotic Python 2.7 strftime limitation of year >= 1900'''
    return '{y}{m}{d}'.format(y=str(date.year), m=str(date.month).zfill(2), d=str(date.day).zfill(2))



