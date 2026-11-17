# btcnow

Archival source for **btcnow.net**, an early Bitcoin buying service from around
2011. The code is preserved as historical material, not as a maintained payment
application.

## What It Was

btcnow was a small Google App Engine application that made it possible to buy
Bitcoin through familiar web payment systems and then receive coins directly to
a wallet address. The code in this repository includes old handlers for Google
Checkout, Dwolla, OKPAY, PayPal, and Authorize.Net, plus a simple Bitcoin RPC
integration used to check inventory and send payouts.

The public record is sparse, but a few contemporary and later references line
up with the code:

- The Bitcoin Wiki describes Btcnow as a discontinued exchange that supported
  OKPAY and Dwolla, and previously accepted Google Checkout.
- A Bitcointalk thread from August 2011 discusses "Buy bitcoins using Google
  Checkout - btcnow.net" and includes users reporting very fast delivery.
- A 2020 Hacker News comment by the operator describes btcnow as launching
  around June or July 2011, "gluing" a Google Checkout widget to a Bitcoin
  dispenser, and moving roughly a hundred bitcoins a day at times despite
  fraud and chargeback problems.
- A later Bitcoin Stack Exchange answer mentions that btcnow.net used to sell
  Bitcoin through Google Checkout before that path was shut down.

## Repository State

This is old Python 2 / Google App Engine code. It is not expected to run on
modern App Engine without significant porting work, and several services used
by the app no longer exist in the same form.

Before publishing, obvious private data was scrubbed:

- Email local parts were replaced with `REDACTED`.
- Payment and API-like credentials were partially mangled by keeping enough of
  the prefix to show the original shape and replacing the remainder with
  `REDACTED`.
- Compiled Python artifacts are ignored and should not be committed.

This repository should be treated as a historical snapshot. Do not use it as a
template for handling payments, user identity, fraud prevention, or Bitcoin key
management.

## External References

- Bitcoin Wiki: https://en.bitcoin.it/wiki/Btcnow
- Bitcointalk thread: https://bitcointalk.org/index.php?topic=37436.0
- Hacker News retrospective: https://news.ycombinator.com/item?id=25580637
- Bitcoin Stack Exchange mention: https://bitcoin.stackexchange.com/questions/7177/buy-bitcoins-using-google-checkout

## Licensing scope

Original code and documentation authored for this project by Dean Pierce are licensed under the [Apache License 2.0](LICENSE).
Third-party dependencies, assets, and quoted material retain their respective licenses and notices. This grant does not relicense third-party work.

The bundled `bitcoin/` library (including its LGPL-licensed proxy) and `googlecheckout.py` are third-party material excluded from this grant; their existing licenses and notices remain in effect.
