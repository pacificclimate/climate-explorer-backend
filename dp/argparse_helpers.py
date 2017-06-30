"""
Helpers for setting up argument parsing
"""


def strtobool(string):
    return string.lower() in {'true', 't', 'yes', '1'}


log_level_choices = 'NOTSET DEBUG INFO WARNING ERROR CRITICAL'.split()
