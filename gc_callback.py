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

from btcnow_common import *

class CheckoutCallback(NotificationHandler):

   def merchant_details(self):
     return ("309948200492609", "j5loVPmVORxREDACTED")  # REDACTED@gmail.com
   #  return ("470919806430253", "K5YhG8dz5N0REDACTED") # REDACTED@gmail.com
   #  return ("332824704870237", "EmK744psD2IREDACTED") # REDACTED@gmail.com
   #  return ("510290633535501", "KrjW8yqM21CREDACTED") # REDACTED@gmail.com
   #  return ("105176666328421", "tM4jfa_BD9xREDACTED") # REDACTED@btcnow.net

   # create the new order in the db
   # verify that the payout address is proper
   def new_order(self):
      # first check if we already created this order (maybe the notification can in twice
      order = Order.get_by_key_name(self.notification.google_order_number)
      if order:
         return

      btc_price = btcnow_price()

      try:
         payout = self.notification.shopping_cart.buyer_messages.delivery_instructions
      except:
         payout = "unknown"

      try:
         order = Order(
            key_name = self.notification.google_order_number,
            ident = self.notification.google_order_number,
            email = self.notification.buyer_shipping_address.email,
            paid = False,
            payout = payout,
            amount = self.notification.order_total,
            coins = str(float(self.notification.order_total)/(btc_price)))
      except:
         mail.send_mail("REDACTED@gmail.com","REDACTED@gmail.com","order error","there was an error creating an order")
         return

      order.currency = self.notification.order_total_currency
      order.put()

      message1 = order.email+" paid "+order.amount+" "+order.currency+" and want "+str(float(order.amount)/btc_price)+" coins sent to "+payout
      message2 = "you paid "+order.amount+" and want " + str(float(order.amount)/btc_price) + " coins sent to "+payout+"    your coins will be sent as soon as your payment card is successfuly charged."

      mail.send_mail("REDACTED@gmail.com","REDACTED@gmail.com","btcnow.net order",message1)
      mail.send_mail("REDACTED@gmail.com",order.email,"btcnow.net order",message2)

   def risk_information(self):
      order = Order.get_by_key_name(self.notification.google_order_number)
      if order == None :
         mail.send_mail("REDACTED@gmail.com","REDACTED@gmail.com","risk oops","risk callback for non existant order : "+self.notification.google_order_number)
         return

      # get new information
      order.addr    = self.notification.risk_information.billing_address.address1
      order.city    = self.notification.risk_information.billing_address.city
      order.region  = self.notification.risk_information.billing_address.region
      order.postal  = self.notification.risk_information.billing_address.postal_code
      order.country = self.notification.risk_information.billing_address.country_code

      order.ipaddr = self.notification.risk_information.ip_address
      eligible = self.notification.risk_information.eligible_for_protection

      # check if they are eligible for chargeback protection
      if eligible == 'true' :
         order.sketchy = False
      else :
         order.sketchy = True
         order.put()
         mail.send_mail("REDACTED@gmail.com","REDACTED@gmail.com","risk information","google thinks "+order.email+" was sketchy")
         mail.send_mail("REDACTED@gmail.com",order.email,"risk information","Your payment didn't qualify for google's chargeback protection.")
         self.remote_order.cancel()
         return
      
      order.put()

      # make sure they are in the whitelist of approved vendors
      if not in_whitelist(order.email):
         mail.send_mail("REDACTED@gmail.com",order.email,"whitelist fail","This email address, "+order.email+", is not in the whitelist.")
         mail.send_mail("REDACTED@gmail.com","REDACTED@gmail.com","whitelist fail",order.email+" tried to buy coins, but they are not in the whitelist")
         self.remote_order.cancel()
         return

      # make sure they don't buy more than 10 coins per day
      if ( float(get_coin_count(order.email)) + float(order.coins)) > 10 :
         mail.send_mail("REDACTED@gmail.com",order.email,"greed alert from btcnow.net","You tried to buy too many coins at once.  You are only allowed to buy 10 coins in a 24 hours period of time.  I will refund your order when I get around to it.  Come back tomorrow if you want more coins.")
         mail.send_mail("REDACTED@gmail.com","REDACTED@gmail.com","greed alert",order.email+" tried to buy too many coins ("+order.coins+")")
         self.remote_order.cancel()
         return

      # make sure we have enough coins to send
      balance=btc.connection.getbalance()
      if float(balance) < (float(order.coins)) :
         mail.send_mail("REDACTED@gmail.com",order.email,"sorry from btcnow.net","Sorry, I don't have enough coins to fill your order now.  Please check the number of coins in the vault before purchasing.  Your order will be canceled and no coins will be sent.")
         mail.send_mail("REDACTED@gmail.com","REDACTED@gmail.com","fill more coins","dude, fill more coins "+str(balance)+" < "+order.coins)
         self.remote_order.cancel()
         return

      # verify that the address is good
      #if not btc.connection.validateaddress(order.payout).isvalid() :
      if order.payout == "unknown" :
         mail.send_mail("REDACTED@gmail.com",order.email,"sorry from btcnow.net","Sorry, but the btc address you submitted didn't look valid.")
         mail.send_mail("REDACTED@gmail.com","REDACTED@gmail.com","invalid address",order.email+" had a strange address "+order.payout)
         self.remote_order.cancel()
         return

      #if order.currency != "USD" :
      #   mail.send_mail("REDACTED@gmail.com",order.email,"sorry from btcnow.net","Sorry, but you can only buy coins in USD, not "+order.currency)
      #   mail.send_mail("REDACTED@gmail.com","REDACTED@gmail.com","currency error",order.email+" tried to buy with "+order.currency)
      #   self.remote_order.cancel()
      #   return

      # charge the card
      try :
         self.remote_order.charge_and_ship(order.amount)
         return
      except :
         return

   def charge_amount(self):
      order = Order.get_by_key_name(self.notification.google_order_number)
      if order == None :
         mail.send_mail("REDACTED@gmail.com","REDACTED@gmail.com","charge oops","charge callback for non existant order : "+self.notification.google_order_number)
         return

      if order.paid :
         return

      try:
         btc.connection.sendtoaddress(order.payout,float(order.coins))
         order.paid = True
         order.put()
         # clear the memcached price to the price gets recalculated
         memcache.set("btc_price", None)
      except:
         mail.send_mail("REDACTED@gmail.com",order.email,"invalid btc address","Sorry, but the payout address you submitted did not look legitimate.  Make sure you carefully entered a single bitcoin payment address into the field on the btcnow.net website.  Without this address attached to the order, payouts can not be processed.  Your order will be refunded maunally and coins will not be sent.  Thank you.")
         mail.send_mail("REDACTED@gmail.com","REDACTED@gmail.com","invalid btc address",order.email + " has a strange payout address "+order.payout+" "+order.coins)
         #self.remote_order.cancel()
         return
      
      balance=btc.connection.getbalance()
      mail.send_mail("REDACTED@gmail.com","REDACTED@gmail.com","coins sent!",order.coins+" coins sent to "+order.email+" at "+order.payout+".  "+str(balance)+" coins remain")
      mail.send_mail("REDACTED@gmail.com",order.email,"coins sent!",order.coins+" coins sent to you at "+order.payout)


application = webapp.WSGIApplication([('/callback',CheckoutCallback)])

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
