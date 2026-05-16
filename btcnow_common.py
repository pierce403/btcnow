import cgi

from google.appengine.ext import webapp,db
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import taskqueue, mail, memcache

from googlecheckout import NotificationHandler
      # verify the greed check by email rather than ip for those crafty bastards
import btc
import math
from datetime import datetime
import time
import traceback

# to get the mtgox data
from django.utils import simplejson as json
from google.appengine.api import urlfetch

def btcnow_price():
  data = memcache.get("btc_price")
  if data is not None :
    return data

  # get mtgox dataa
  try:
    ticker_data = urlfetch.fetch("https://mtgox.com/api/0/ticker.php")
    ticker_object = json.loads(ticker_data.content)
    btc_price = float(ticker_object["ticker"]["high"])*1.1
  except:
    return 999
  # get current vault data
  try:
    balance=float(btc.connection.getbalance())
  except:
    return 888
  # poorman multiplier
  #if balance < 100  and balance >1 :
  #  btc_price=btc_price*(2-(balance/100))
  btc_price = round(btc_price,1)
  memcache.add("btc_price", data, 600)
  return btc_price

def btcnow_ok_price():
  data = memcache.get("btc_ok_price")
  if data is not None :
    return data

  # get mtgox dataa
  try:
    ticker_data = urlfetch.fetch("https://mtgox.com/api/0/ticker.php")
    ticker_object = json.loads(ticker_data.content)
    btc_price = float(ticker_object["ticker"]["high"])*1.0
  except:
    return 999
  # get current vault data
  try:
    balance=float(btc.connection.getbalance())
  except:
    return 888
  # poorman multiplier
  #if balance < 100  and balance >1 :
  #  btc_price=btc_price*(2-(balance/100))
  btc_price = round(btc_price,1)
  memcache.add("btc_ok_price", data, 600)
  return btc_price

def get_coin_count(email):
  #q = Order.all()
  q = InstantPaymentNotification.all()
  q.filter("email =", email)
  q.filter("paid =", True)
  q.filter("ctime >", datetime.fromtimestamp(time.time()-60*60*24))
  r = q.fetch(10)
  sold_today=0
  for result in r:
    try :
      sold_today += float(result.coins)
    except :
      continue
  return sold_today

def in_whitelist(email_addr):
  q = Whitelist.all()
  q.filter("email = ", email_addr.lower())
  r = q.fetch(1)
  if not r :
    #wl = Whitelist(email=email_addr)
    #wl.put() # amnesty right here :-D
    return False
  else :
    return True

class DwollaOrder(db.Model):
  checkoutid = db.StringProperty()
  btcaddr = db.StringProperty()
  quantity = db.StringProperty()
  orderid = db.StringProperty()
  total = db.StringProperty()

  ctime = db.DateTimeProperty(auto_now_add=True)
  mtime = db.DateTimeProperty(auto_now=True)
  paid  = db.BooleanProperty(default=False)

class InstantPaymentNotification(db.Expando):
  ctime = db.DateTimeProperty(auto_now_add=True)
  mtime = db.DateTimeProperty(auto_now=True)
  paid  = db.BooleanProperty()

class Order(db.Model):
   ident = db.StringProperty() # other place to store id
   currency = db.StringProperty() # total amount paid
   amount = db.StringProperty() # total amount paid
   coins = db.StringProperty()  # number of coins they want
   paid = db.BooleanProperty()  # has paid for or not

   sketchy = db.BooleanProperty() # is this a sketchy order?
   email  = db.StringProperty()  # email address of buyer
   ipaddr = db.StringProperty()  # email address of buyer

   addr   = db.StringProperty()  # home address
   city   = db.StringProperty()  # home address
   region = db.StringProperty()  # home address
   postal = db.StringProperty()  # home address

   payout = db.StringProperty() # btc payout address
   items = db.StringListProperty()  # just for fun
   financial  = db.StringProperty()  # chargable / charged / declined
   fufillment = db.StringProperty() # new / processing / delivered / no deliver
   ctime = db.DateTimeProperty(auto_now_add=True)
   mtime = db.DateTimeProperty(auto_now=True)

class Whitelist(db.Model):
  name  = db.StringProperty() # email of person
  email = db.StringProperty() # email of person
