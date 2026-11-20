import requests, json, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
url = 'https://wasalt.sa/en/property/sale/apartment-675-sqm-with-3-bedrooms-5879365'
r = requests.get(url, headers={'User-Agent': 'DarGlobal-Assignment-Research'}, timeout=40)
print('STATUS', r.status_code, 'LEN', len(r.text))
m = re.search(r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
if m:
    d = json.loads(m.group(1))
    props = d.get('props', {}).get('pageProps', {})
    print('pageProps keys:', list(props.keys()))
    open('one_listing.json', 'w', encoding='utf-8').write(json.dumps(props, indent=2, ensure_ascii=False))
    print('saved one_listing.json')
else:
    print('NO NEXT DATA')
    print(r.text[:500])
