# -*- coding: utf-8 -*-

from flask import Flask
import logging

app = Flask(__name__)

@app.route('/')
def render_index():
    return u'等公車也是一種專業'

if __name__ == "__main__":

    import getopt, sys

    port = 5000
    app.debug = False

    try:
        opts, args = getopt.getopt(sys.argv[1:],'p:d',['port=', 'debug'])
    except getopt.GetoptError:
        exit(2)

    for opt, arg in opts:
        if opt in ('-p', '--port'): port = int(arg.strip())
        elif opt in ('-d','--debug'): app.debug = True

    app.run(host='0.0.0.0', port=port)
