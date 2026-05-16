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

        merchant_id = '309948200492609'
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
<a href="/buy"> [ buy ] </a>
<a href="/sell"> [ sell ] </a>
<a href="/invest"> [ invest ] </a>
        ''')

        self.response.out.write('<br><br>currently priced at <b>'+str(btc_price)+'0</b> USD per coin<br><br>')
        self.response.out.write('Sorry, google has screwed me over again by suspending my account, so it might be a few days<br>')
        self.response.out.write('before I am able to get online again.  If you want to show support, please help out by emailing<br>')
        self.response.out.write('REDACTED@google.com with the subject line "[#901067099] Your Google Checkout Account"<br>')
        self.response.out.write('and let them know that they should either stop trying to prevent their merchants from selling<br>')
        self.response.out.write('bitcoins, or they should forbid it in the terms of service, the community needs to know.<br><br>')

        self.response.out.write('For some background information, this is the 8th time I have had my account suspended.  Every time<br>')
        self.response.out.write('the only thing they say is that they have determined that my business model is "incompatible" with<br>')
        self.response.out.write('''google checkout, and that they can't tell me anything else about the suspension for "security reasons".<br><br>''')

        self.response.out.write('For now you can try accesscoin.com or get-bitcoin.com<br>')

        if 1 == 1 :
          return
        user = users.get_current_user()
        if user:
          if in_whitelist(user.email()) :
            self.response.out.write("<br>hey there %s, welcome to the cool kids club" % user.nickname())
          else :
            self.response.out.write("<br>sorry %s, you are not on the list<br><br>" % user.nickname())
            self.response.out.write("I hate to do this, but from now on, I need to verify the physical identity of<br>")
            self.response.out.write("btcnow.net users.  Please write the following note on a piece of paper, and sign it:<br><br>")

            self.response.out.write("<i>My name is $FIRSTNAME $LASTNAME, and I want to buy bitcoins from btcnow.net</i><br><br>")

            self.response.out.write("Then you need to place a valid government ID next to the note and take a picture.<br>")
            self.response.out.write("Email me the picture, and a quick message about why you are interested in bitcoin.<br><br>")

            self.response.out.write("So, a photo with the signed note and your ID, and I will add you to the whitelist.<br>")
            self.response.out.write("Of course these photos will <b>only</b> be used to fight chargebacks.<br><br>")

            self.response.out.write("Again, I'm sorry about this.  Bitcoins may be safe for merchants, but credit cards<br>")
            self.response.out.write("still are not.  I hope we see a future where we can rely on secure online transactions,<br>")
            self.response.out.write("but all the chargebacks are threatening to kill the site, and I can't let that happen.<br>")

            return
              
        else:
          self.response.out.write("<br><br>you are not <a href=\"%s\">logged in</a>, you get nothing" % users.create_login_url("/buy"))
          return

        self.response.out.write('<br><br><noscript><style> .jsonly { display: none }</style><font color="red"><b>please enable javascript, it makes stuff just that much cooler</b></font><br><br></noscript>')

        self.response.out.write('''
<form class="jsonly" action="https://checkout.google.com/api/checkout/v2/checkoutForm/Merchant/'''+merchant_id+'''" id="BB_BuyButtonForm" method="post" name="BB_BuyButtonForm" target="_top">
    <input name="item_name_1" type="hidden" value="BTC"/>
    btc address 
    <input type="text" name="shopping-cart.buyer-messages.delivery-instructions-1" value="" maxlength="60" /><br>
    <input type="hidden" name="shopping-cart.buyer-messages.delivery-instructions-1.max-chars" value="100" />
    <input name="item_description_1" type="hidden" value="BitCoin"/>
    quantity
    <input name="item_quantity_1" type="text" value="1" width="5em"/>
    <br><small>(whole numbers only please)</small><br>
    <!-- mess with the best, die like the rest -->
    <input name="item_price_1" type="hidden" value="'''+str(btc_price)+'''" />
    <input name="item_currency_1" type="hidden" value="USD"/>
    <input name="shopping-cart.items.item-1.digital-content.key" type="hidden" value="diHPDbJj4jyrp3CEaEx6nGREDACTED"/>
    <input name="shopping-cart.items.item-1.digital-content.key.is-encrypted" type="hidden" value="true"/>
    <input name="shopping-cart.items.item-1.digital-content.url" type="hidden" value="http://blockexplorer.com"/>
    <input name="_charset_" type="hidden" value="utf-8"/>
    <input alt="" src="https://checkout.google.com/buttons/buy.gif?merchant_id='''+merchant_id+'''&amp;w=121&amp;h=44&amp;style=white&amp;variant=text&amp;loc=en_US" type="image"/>
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
              address_form = document.forms[0].elements[1];
              quantity_form = document.forms[0].elements[4];

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

class Order(db.Model):
   ident = db.StringProperty() # other place to store id
   amount = db.StringProperty() # total amount paid
   coins = db.StringProperty() # number of coins they want
   paid = db.BooleanProperty()  # has paid for or not
   sketchy = db.BooleanProperty() # is this a sketchy order?
   email  = db.StringProperty()  # email address of buyer
   ipaddr = db.StringProperty()  # email address of buyer
   payout = db.StringProperty() # btc payout address
   items = db.StringListProperty()  # just for fun
   financial  = db.StringProperty()  # chargable / charged / declined
   fufillment = db.StringProperty() # new / processing / delivered / no deliver
   ctime = db.DateTimeProperty(auto_now_add=True)
   mtime = db.DateTimeProperty(auto_now=True)

application = webapp.WSGIApplication([('/buy', MainPage)])

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
