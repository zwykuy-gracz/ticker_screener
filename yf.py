import yfinance as yf
from pprint import pprint

dat = yf.Ticker("INTC")

ticker = dat.info
pprint(dat.news[0]["content"]["title"])
print(dat.news[0]["content"]["clickThroughUrl"]["url"])
print("=====================================")
pprint(dat.news[1]["content"]["title"])
print(dat.news[1]["content"]["clickThroughUrl"]["url"])
print("=====================================")
pprint(dat.news[2]["content"]["title"])
print(dat.news[2]["content"]["canonicalUrl"]["url"])
# pprint(dat.news[2]["content"])
