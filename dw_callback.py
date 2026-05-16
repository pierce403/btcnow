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
import hmac, hashlib
from btcnow_common import *

#PP_URL = "https://www.sandbox.paypal.com/cgi-bin/webscr"
VERIFY_URL = "https://www.okpay.com/ipn-verify.html"

class DwollaCallback(webapp.RequestHandler):

  def post(self):

    # parse in json
    logging.info(self.request.body)
    callback = json.loads(self.request.body)

    if callback['Status'] != "Completed":
      logging.info("callback is not 'Completed' : "+callback['Status'])
      return

    # look up order from before
    q = DwollaOrder.all()
    q.filter("checkoutid =",callback['CheckoutId'])
    r = q.fetch(1)

    for result in r:
      order = result

    if not order:
      logging.info("I don't know about this order..")
      return

    if order.paid:
      logging.info("This order has already been paid for!")
      return

    # TODO verify hmac!!
    
    if callback['Signature'] != hmac.new("ulIkUZTxREAbBq/hreNdR/pfTREDACTED",callback['CheckoutId']+"&%.2f"%callback['Amount'],hashlib.sha1).hexdigest():
      logging.info("boo, sig didn't verify")
      return

    # update order
    order.orderid = callback['OrderId']
    order.total = str(callback['Amount'])
    order.paid = True
    order.put()

    balance=float(btc.connection.getbalance())
    total = float(order.total) / btcnow_ok_price()

    if balance < total:
      logging.info("damn, not enough coins")
      return

    # deliver order
    btc.connection.sendtoaddress(order.btcaddr,total)
    memcache.set("btc_ok_price", None)

application = webapp.WSGIApplication([('/dw_callback',DwollaCallback)])

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
