#!/usr/bin/env python3
import json, os, collections, datetime, re
D = os.path.dirname(os.path.abspath(__file__))
load = lambda n: json.load(open(os.path.join(D, n), encoding='utf-8'))
ts = lambda ms: datetime.datetime.fromtimestamp(ms/1000, datetime.timezone(datetime.timedelta(hours=8))).strftime('%m-%d %H:%M')

m = load('market.json')['data']
print('=== 全部行情符号 ===')
for q in m['marketQuotes']['quotes']:
    print('%-10s %-10s %-12s %+7.2f%%' % (q['symbol'], q.get('display', '')[:10], q.get('price'), q.get('change', 0)))
print('\n=== shippingStress ===')
print(json.dumps(m.get('shippingStress'), ensure_ascii=False)[:1200])

news = load('news.json')
items = []
for c, body in news['categories'].items():
    for it in body.get('items', []):
        it['_cat'] = c
        items.append(it)

THEMES = {
 '乌克兰/俄罗斯': r'ukrain|russia|moscow|kyiv|putin|donbas|drone strike',
 '伊朗战争': r'\biran|tehran|hormuz|irgc',
 '中东/加沙/也门': r'gaza|israel|houthi|yemen|lebanon|hezbollah|syria|aden',
 '朝鲜半岛': r'north korea|pyongyang|kim jong|south korea|seoul',
 '委内瑞拉/拉美': r'venezuela|maduro|bolsonaro|brazil|argentina|mexico|caracas',
 '台海/中国': r'taiwan|beijing|china|xi jinping|pla\b',
 '美国内政/选举': r'trump|congress|senate|white house|midterm|democrat|republican',
 '通胀/美联储': r'inflation|cpi|fed\b|fomc|rate cut|rate hike|powell|treasur',
 'AI/芯片': r'\bai\b|openai|nvidia|chip|semiconductor|anthropic|data cent',
 '能源/油价': r'\boil\b|opec|brent|crude|refiner|gas price|pipeline',
 '黄金/避险': r'\bgold\b|bullion|safe haven',
 '供应链/航运': r'shipping|tanker|freight|red sea|suez|port|container',
 '网络攻击': r'cyber|ransomware|hack(ed|ing)?|breach|malware',
 '灾害/气候': r'wildfire|flood|cyclone|hurricane|earthquake|drought|heatwave',
 '制裁': r'sanction',
 '关税/贸易': r'tariff|trade war|export control',
}
now = max(i['publishedAt'] for i in items)
print('\n=== 主题分布（条目数，含重复 feed）===')
rows = []
for name, pat in THEMES.items():
    rx = re.compile(pat, re.I)
    hit = [i for i in items if rx.search(i['title'] or '') or rx.search(i.get('snippet') or '')]
    top = sorted(hit, key=lambda x: -x['importanceScore'])[:2]
    rows.append((len(hit), name, top))
for n, name, top in sorted(rows, reverse=True):
    print('\n## %s  %d 条' % (name, n))
    for t in top:
        print('   [%s] %s | %s | score=%s' % (ts(t['publishedAt']), t['source'], t['title'][:110], t['importanceScore']))
