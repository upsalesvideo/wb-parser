import sys
import os
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.exceptions import NotFound

sys.path.insert(0, os.path.dirname(__file__))

from app import app

app.config['APPLICATION_ROOT'] = '/wb'
app.config['PREFERRED_URL_SCHEME'] = 'https'

application = DispatcherMiddleware(NotFound(), {'/wb': app})
