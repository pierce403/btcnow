import cgi

import urllib
import urllib2

from google.appengine.ext import webapp,db
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import taskqueue, mail, memcache

import sys
import btc
import math
from datetime import datetime
import time
import traceback
import logging

# to get the mtgox data
from django.utils import simplejson as json
#from django.http import HttpResponse, HttpResponseServerError
from google.appengine.api import urlfetch
from btcnow_common import *

class AuthNetCallback(webapp.RequestHandler):

  def post(self):

    parameters = self.request.POST.copy() 
    logging.info("authorize.net receipt : "+str(parameters));
    return

application = webapp.WSGIApplication([('/an_callback',AuthNetCallback)])

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
