#!/usr/bin/env python

from logging import basicConfig, DEBUG
from argparse import ArgumentParser

from ce.wsgi import app

if __name__ == "__main__":
    parser = ArgumentParser(description='Start a development CE instance')
    parser.add_argument('-p', '--port', type=int, required=True,
                        help='Indicate the port on which to bind the application')
    parser.add_argument('-t', '--threaded',
                        default=False, action='store_true',
                        help='Flag to specify use of Flask in threaded mode')
    args = parser.parse_args()

    app.run('0.0.0.0', args.port, use_reloader=True, debug=True, use_debugger=True, threaded=args.threaded)
