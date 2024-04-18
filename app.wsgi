#!/usr/bin/env python

import sys
#import logging
#logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '/var/www/gpt/')

from app import app as application

#def wsgi(environ, start_response):
#    return application(environ, start_response)
