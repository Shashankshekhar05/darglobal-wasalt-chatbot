import requests, json, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
url = 'https://wasalt.sa/en/property/rent/apartment-11917-sqm-with-3-bedrooms-5879383'
r = requests.get(url, headers={'User-Agent': 'DarGlobal-Assignment-Research'}, timeout=40)
print('STATUS', r.status_code)
m = re.search(r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
d = json.loads(m.group(1))
p = d['props']['pageProps']['propertyDetailsV3']
if isinstance(p, list):
    p = p[0]
pi = p['propertyInfo']
for k in ('title', 'city', 'propertySubType', 'propertyFor', 'salePrice', 'expectedRent',
          'rentFreq', 'conversionPrice', 'conversionUnit'):
    print(k, '=', pi.get(k))
for a in p['attributes']:
    print('attr', a)
