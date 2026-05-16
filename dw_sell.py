import cgi

from google.appengine.ext import webapp,db
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import taskqueue, mail, users

from googlecheckout import NotificationHandler
      # verify the greed check by email rather than ip for those crafty bastards
import btc
import math
from datetime import datetime
import time
import traceback

from btcnow_common import *

# to get the mtgox data
from django.utils import simplejson as json
from google.appengine.api import urlfetch
import urllib
import logging

class MainPage(webapp.RequestHandler):
    def get(self):

        btc_price = btcnow_ok_price()

        self.response.out.write('<html><head><title>btcnow.net : instantly buy bitcoins with google checkout</title>')
        self.response.out.write('''<meta name="description=" content="With btcnow.net, anyone can instantly buy bitcoins with a google checkout account.">''')

        self.response.out.write('</head><body><center><br>')
        self.response.out.write('''
<style type="text/css">
body {font-family: monospace}
A:link {text-decoration: none}
A:visited {text-decoration: none}
A:active {text-decoration: none}
A:hover {text-decoration: none; color: red;}
</style>

<a href="/about"> [ about ] </a>
<a href="/ok"> [ okpay ] </a>
<a href="/dw">[ dwolla ] </a>
<a href="/rules"> [ rules ] </a>
        ''')

        self.response.out.write('<br><br>!! this is not working yet !!')
        self.response.out.write('<br><br>currently priced at <b>'+str(btc_price)+'0</b> USD per coin')

        self.response.out.write('<br><br><noscript><style> .jsonly { display: none }</style><font color="red"><b>please enable javascript, it makes stuff just that much cooler</b></font><br><br></noscript>')

        self.response.out.write('''

<form action="dw" method="post">
  dwolla id
  <input type="text" name="did" maxlength="127"><br>
  <button type="submit">sell with dwolla</button>
</form>

''')

        self.response.out.write('''
           <script type="text/javascript">
              var _gaq = _gaq || [];
              _gaq.push(['_setAccount', 'UA-255REDACTED']);
              _gaq.push(['_trackPageview']);

              (function() {
              var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
              ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
              var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
              })();
           </script>''')

    def post(self):
      addr = self.request.get('addr')
      quantity = self.request.get('quantity')

      btc_price = btcnow_ok_price()
      json_data = '''{
        "Key": "OiU2xd7PFq+BuWpklbvp764kgREDACTED",
        "Secret": "ulIkUZTxREAbBq/hreNdR/pfTREDACTED",
        "PurchaseOrder": {
          "DestinationId": "812-55REDACTED",
          "Discount": 0.00,
          "OrderItems": [
            {
                "Name": "bitcoin",
                "Price": '''+str(btc_price)+''',
                "Quantity": '''+str(quantity)+'''
            }],
          "Shipping": 0.00,
          "Tax": 0.00,
          "Total": +'''+str(btc_price*(int(quantity)))+'''
        }
      }'''

      ret = urlfetch.fetch("https://www.dwolla.com/payment/request",json_data,method=urlfetch.POST,headers={'Content-Type': 'application/json'})

      logging.info(ret.content)
      cid = json.loads(ret.content)['CheckoutId']
      if not cid:
        self.response.write("boo")
        return

      o = DwollaOrder(checkoutid=cid,btcaddr=addr)
      o.put()

      self.redirect("https://www.dwolla.com/payment/checkout/"+cid)



application = webapp.WSGIApplication([('/.*',MainPage),('/dw', MainPage)])

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
