import re, json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
html = open('wasalt_debug.html', encoding='utf-8').read()

# All cms.wasalt.com or /api occurrences with context
hits = []
for m in re.finditer(r'(cms\.wasalt\.com[^"\'\\\s<>]*|/api/[A-Za-z0-9_\-/\.]*)', html):
    hits.append(m.group(0))
print('API HITS', len(hits))
for h in list(dict.fromkeys(hits))[:40]:
    print(h)

# Next.js build id + data
m = re.search(r'"buildId"\s*:\s*"([^"]+)"', html)
print('buildId', m.group(1) if m else None)

# look for __NEXT_DATA__
m = re.search(r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
if m:
    data = json.loads(m.group(1))
    print('NEXT_DATA keys', list(data.keys()))
    props = data.get('props', {}).get('pageProps', {})
    print('pageProps keys', list(props.keys())[:30])
    # dump shallow structure
    def walk(o, path='', depth=0):
        if depth > 3:
            return
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, (dict, list)):
                    print(path + '/' + k, type(v).__name__, (len(v)))
                    walk(v, path + '/' + k, depth + 1)
        elif isinstance(o, list) and o:
            walk(o[0], path + '[0]', depth + 1)
    walk(props, 'pageProps')
    open('next_data.json', 'w', encoding='utf-8').write(json.dumps(props, indent=2, ensure_ascii=False))
    print('saved next_data.json')
