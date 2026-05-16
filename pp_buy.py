import cgi

from google.appengine.ext import webapp,db
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import taskqueue, mail, memcache, users

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

        btc_price = btcnow_price()

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
<a href="/pp">[ paypal ] </a>
<a href="/rules"> [ rules ] </a>
        ''')

        self.response.out.write("<br><br>banned from paypal<br><br>well, it was fun while it lasted")
        return

        user = users.get_current_user()
        if user:
          if in_whitelist(user.email()) :
            self.response.out.write("<br><br>logged in as %s" % (user.email()))
            self.response.out.write("<br><a href=\"%s\">( logout )</a>" % users.create_logout_url("/pp"))
          else :
            self.response.out.write("<br><br>sorry %s, you are not on the list<br><br>" % user.email())
            self.response.out.write("I am currently accepting new customers.  To apply, I need two things from you :<br><br>")

            self.response.out.write("1. A picture of you holding up state ID.  Text on the ID and your face must be clearly visible.<br><br>")
            #self.response.out.write("You should look like the picture in the ID, and your name should match email and payment methods.<br><br>")

            self.response.out.write("2. You need to create an account on btcnearme.com   Getting bitcoins out there is important, and<br>")
            self.response.out.write("my site can't do it alone, so I would encourage everyone to get involved in promoting bitcoin.<br>")
            self.response.out.write("<br>")
            return
        else :
          self.response.out.write("<br><br>you are not <a href=\"%s\">logged in</a>, you get nothing" % users.create_login_url("/pp"))
          return

        self.response.out.write('<br><br>warning : please do not attempt to buy more than 10 coins per day<br>')
        self.response.out.write('you will not recieve them, and you will be removed from the whitelist<br><br>')

        self.response.out.write('please make sure your paypal email matches your whitelisted email, if<br>')
        self.response.out.write('you need me to change your email in the whitelist, please let me know.<br><br>')

        self.response.out.write('currently priced at <b>'+str(btc_price)+'0</b> USD per coin')

        self.response.out.write('<br><br><noscript><style> .jsonly { display: none }</style><font color="red"><b>please enable javascript, it makes stuff just that much cooler</b></font><br><br></noscript>')

        self.response.out.write('''
<form action="https://www.paypal.com/cgi-bin/webscr" method="post">
<input type="hidden" name="cmd" value="_xclick">
<input type="hidden" name="business" value="L39A4HREDACTED">
<input type="hidden" name="lc" value="US">
<input type="hidden" name="item_name" value="BTC">
<input type="hidden" name="amount" value="'''+str(btc_price)+'''">
<input type="hidden" name="currency_code" value="USD">
<input type="hidden" name="button_subtype" value="services">
<input type="hidden" name="bn" value="PP-BuyNowBF:btn_buynowCC_LG.gif:NonHosted">
<input type="hidden" name="on0" value="btc address">
btc address
<input type="text" name="os0" maxlength="200"><br>
quantity
<input type="text" name="quantity" maxlength="200"><br><br>
<input type="image" src="https://www.paypalobjects.com/en_US/i/btn/btn_buynowCC_LG.gif" border="0" name="submit" alt="PayPal - The safer, easier way to pay online!">
<img alt="" border="0" src="https://www.paypalobjects.com/en_US/i/scr/pixel.gif" width="1" height="1">
</form>''')

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
              address_form = document.forms[0].elements[9];
              quantity_form = document.forms[0].elements[10];

              var len = address_form.value.length
              var coin_count='''+str(get_coin_count(user.email()))+'''

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

application = webapp.WSGIApplication([('/pp', MainPage)])

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
