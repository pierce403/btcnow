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

#PP_URL = "https://www.sandbox.paypal.com/cgi-bin/webscr"
VERIFY_URL = "https://www.okpay.com/ipn-verify.html"

class OkPayCallback(webapp.RequestHandler):

  def post(self):

    parameters = None
    parameters = self.request.POST.copy()
    params = self.request.body

    logging.info(str(parameters))

    if parameters['ok_txn_status'] != 'completed':
      logging.info("payment status not 'completed', so don't care")
      return

    # make sure request is legit
    if parameters['ok_receiver_wallet'] != 'OK572REDACTED':
      logging.info("holy cow, that wasn't my wallet")
      return

    # send the params back
    req = urllib2.Request(VERIFY_URL, params+"&ok_verify=true")
    req.add_header("Content-type", "application/x-www-form-urlencoded")
    response = urllib2.urlopen(req)
    status = response.read()
    if not status == "VERIFIED":
      logging.info("order could not be verified.. "+status)
      return

    logging.info("order verified!")

    btcnow_price=btcnow_ok_price()
    ipn = InstantPaymentNotification()
    ipn.reference = parameters['ok_txn_id']
    ipn.btc_addr = parameters['ok_item_1_custom_1_value']
    ipn.currency = parameters['ok_txn_currency']
    ipn.amount =   parameters['ok_txn_amount']
    ipn.email =    parameters['ok_payer_email']
    ipn.quantity = str(float(ipn.amount)/btcnow_price)

    ipn.put()

    # verify that the customer is in the whitelist
    #if not in_whitelist(ipn.email):
    #  mail.send_mail("REDACTED@gmail.com",ipn.email,"whitelist fail","This email address, "+ipn.email+", is not in the whitelist.")
    #  mail.send_mail("REDACTED@gmail.com","REDACTED@gmail.com","whitelist fail",ipn.email+" tried to buy coins, but they are not in the whitelist")
    #  return

    # make sure they don't buy more than 10 coins per day
    #if ( float(get_coin_count(ipn.email)) + float(ipn.quantity)) > 10 :
    #  mail.send_mail("REDACTED@gmail.com",ipn.email,"greed alert from btcnow.net","You tried to buy too many coins at once.  You are only allowed to buy 10 coins in a 24 hours period of time.  I will refund your order when I get around to it.  Come back tomorrow if you want more coins.")
    #  mail.send_mail("REDACTED@gmail.com","REDACTED@gmail.com","greed alert",ipn.email+" tried to buy too many coins ("+ipn.quantity+")")
    #  return

    # make sure we have enough coins to send
    balance=btc.connection.getbalance()
    if float(balance) < (float(ipn.quantity)) :
      mail.send_mail("REDACTED@gmail.com",ipn.email,"sorry from btcnow.net","Sorry, I don't have enough coins to fill your order now.  Please check the number of coins in the vault before purchasing.  Your order will be canceled and no coins will be sent.")
      mail.send_mail("REDACTED@gmail.com","REDACTED@gmail.com","fill more coins","dude, fill more coins "+str(balance)+" < "+ipn.quantity)
      return

    # send the coins
    try:
      total = float(ipn.amount)/btcnow_price
      logging.info(str(ipn.amount)+" / "+str(btcnow_price)+" = "+str(total));
      btc.connection.sendtoaddress(ipn.btc_addr,total)
      memcache.set("btc_ok_price", None)
      ipn.paid=True;
      ipn.put()

    except Exception, e:
      logging.error(e)
      logging.error(e.args)
      mail.send_mail("REDACTED@gmail.com",str(ipn.email),"error processing paymenr","Sorry, but there was an error when I tried to send you your coins.  Make sure you carefully entered a single bitcoin payment address into the field on the btcnow.net website.  Without this address attached to the order, payouts can not be processed.  Your order will be refunded maunally and coins will not be sent.  Thank you.")
      mail.send_mail("REDACTED@gmail.com","REDACTED@gmail.com","invalid btc address",str(ipn.email) + " has a strange payout address "+str(ipn.btc_addr)+" "+str(ipn.quantity))
      return

    balance=btc.connection.getbalance()
    logging.info(str(ipn.quantity)+" coins sent to "+str(ipn.email)+" at "+str(ipn.btc_addr)+".  "+str(balance)+" coins remain")
    mail.send_mail("REDACTED@gmail.com","REDACTED@gmail.com","coins sent!",str(ipn.quantity)+" coins sent to "+str(ipn.email)+" at "+str(ipn.btc_addr)+".  "+str(balance)+" coins remain")
    return

application = webapp.WSGIApplication([('/ok_callback',OkPayCallback)])

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
