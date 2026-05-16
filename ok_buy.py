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

class MainPage(webapp.RequestHandler):
    def get(self):

        btc_price = btcnow_ok_price()

        self.response.out.write('<html><head><title>btcnow.net : buy bitcoins with okpay!</title>')
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

        self.response.out.write('<br><br>currently priced at <b>'+str(btc_price)+'0</b> USD per coin')

        self.response.out.write('<br><br><noscript><style> .jsonly { display: none }</style><font color="red"><b>please enable javascript, it makes stuff just that much cooler</b></font><br><br></noscript>')

        self.response.out.write('''

<form  method="post" action="https://www.okpay.com/process.html">
   <input type="hidden" name="ok_receiver" value="OK572REDACTED"/>
   <input type="hidden" name="ok_item_1_name" value="bitcoin"/>
   <input type="hidden" name="ok_item_1_price" value="'''+str(btc_price)+'''"/>
   <input type="hidden" name="ok_currency" value="USD"/>
   btc address
   <input type="text" name="ok_item_1_custom_1_value" maxlength="127"><br>
   quantity
   <input type="text" name="ok_item_1_quantity" maxlength="127"><br><br>
   <input type="image" name="submit" alt="OKPAY Payment" src="https://www.okpay.com/img/buttons/x02.gif"/>
</form>
''')

        try:
          balance=btc.connection.getbalance()
          if balance < 1:
            self.response.out.write("sorry, I am currently out of coins, please try again later")
            self.response.out.write(" ")

          else:
            # -0.01 coins to make sure we can cover the tx fees
            self.response.out.write(int(math.floor(float(balance-0.01))))
            self.response.out.write(" BTC in the vault")
        except:
          balance=0;
          self.response.out.write("not connected to backend")

        #   field vefifier
        self.response.out.write('''
        <script type="text/javascript">
          window.onload = function()
          {
            document.forms[0].onsubmit=function()
            {
              address_form = document.forms[0].elements[4];
              quantity_form = document.forms[0].elements[5];

              var len = address_form.value.length
              var coin_count=0

              if( len < 25 || len > 34 )
              {
                alert('that does not look like a btc address ..');
                return false;
              }

              if(quantity_form.value != Math.round(quantity_form.value) )
              {
                alert('that is not a whole number ..');
                return false;
              }

              if(quantity_form.value > 10 )
              {
                alert('please limit yourself to 10 coins at a time');
                return false;
              }

              if((parseInt(quantity_form.value) + parseInt(coin_count)) > 10 )
              {
                alert('you have already purchased '+coin_count+' coins\\nyou can buy '+(10-coin_count)+' more today\\nplease give others a chance to buy coins as well :-)' );
                return false;
              }

              if(quantity_form.value > '''+str(math.floor(float(balance)))+''')
              {
                alert('I do not have that many coins ..');
                return false;
              }

              return true;
            }
          }
        </script>
        ''');


        #   analytics code
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

application = webapp.WSGIApplication([('/.*',MainPage),('/ok', MainPage)])

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
