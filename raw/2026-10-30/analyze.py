#!/usr/bin/env python3
"""把 worldmonitor 原始快照压成可读摘要（tools: 日报用）"""
import json, collections, datetime, os

D = os.path.dirname(os.path.abspath(__file__))
def load(n):
    with open(os.path.join(D, n), encoding='utf-8') as f:
        return json.load(f)

def ts(ms):
    return datetime.datetime.fromtimestamp(ms/1000, datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M')

news = load('news.json')
print('=== NEWS coverage ===')
cov = news['coverage']
print('state=%s items=%s publishers=%s feeds=%s/%s categories=%s/%s generatedAt=%s' % (
    cov['state'], cov['itemsServed'], cov['publisherCount'], cov['feedCompleted'], cov['feedTotal'],
    cov['categoryCompleted'], cov['categoryTotal'], cov.get('generatedAt')))
print('dropped(cap/fresh/undated)=%s/%s/%s' % (cov.get('droppedCategoryCap'), cov.get('droppedFreshness'), cov.get('droppedUndated')))

CATCN = {'politics':'政治','us':'美国','europe':'欧洲','middleeast':'中东','tech':'科技','ai':'AI',
         'finance':'金融','commodities':'商品','gov':'政府','africa':'非洲','latam':'拉美','asia':'亚洲',
         'energy':'能源','thinktanks':'智库','crisis':'危机','layoffs':'裁员','science':'科学','intel':'情报'}

items = []
for c, body in news['categories'].items():
    for it in body.get('items', []):
        it['_cat'] = c
        items.append(it)
print('\n=== 分类条目数 ===')
cnt = collections.Counter(i['_cat'] for i in items)
for c, n in cnt.most_common():
    print('%-12s %-6s %3d' % (c, CATCN.get(c, c), n))
print('total items:', len(items))

tsall = [i['publishedAt'] for i in items if i.get('publishedAt')]
print('\n发布时间范围: %s → %s (CST)' % (ts(min(tsall)), ts(max(tsall))))
now = max(tsall)
buckets = collections.Counter()
for t in tsall:
    h = (now - t)/3.6e6
    buckets['<6h' if h<6 else '6-24h' if h<24 else '24-48h' if h<48 else '48-96h' if h<96 else '>96h'] += 1
print('按龄期分布:', dict(buckets))

print('\n=== 高重要度条目 (score>=50, 按分数) ===')
hi = sorted([i for i in items if i.get('importanceScore',0) >= 50], key=lambda x: -x['importanceScore'])
for i in hi[:40]:
    th = i.get('threat') or {}
    print('%3d | %s | %-12s | %-18s | %s' % (i['importanceScore'], ts(i['publishedAt']), CATCN.get(i['_cat'], i['_cat']),
          i['source'][:18], i['title'][:95]))
    print('      alert=%s threat=%s/%s conf=%.1f cred=%s corr=%s phase=%s' % (
        i.get('isAlert'), th.get('level'), th.get('category'), th.get('confidence', 0),
        i.get('credibilityScore'), i.get('corroborationCount'), (i.get('storyMeta') or {}).get('phase')))

print('\n=== 最新 24h 内 alert 条目 ===')
al = sorted([i for i in items if i.get('isAlert') and (now - i['publishedAt']) < 24*3.6e6], key=lambda x: -x['publishedAt'])
for i in al[:25]:
    print('%s | %-12s | %-16s | %s' % (ts(i['publishedAt']), CATCN.get(i['_cat'], i['_cat']), i['source'][:16], i['title'][:90]))

print('\n=== 多源同一事件 (corroboration>=2) ===')
multi = sorted([i for i in items if (i.get('corroborationCount') or 0) >= 2], key=lambda x: -(x.get('corroborationCount') or 0))
seen=set()
for i in multi[:20]:
    key=i['title'][:40]
    if key in seen: continue
    seen.add(key)
    print('corr=%s src=%s | %s | %s' % (i['corroborationCount'], i['sourceCount'] if 'sourceCount' in i else '-', ts(i['publishedAt']), i['title'][:95]))

print('\n=== feed 状态异常 ===')
fs = news.get('feedStatuses')
if isinstance(fs, list):
    bad = [f for f in fs if (f.get('state') or f.get('status')) not in ('ok','OK','complete',None)]
    print('feeds total', len(fs), 'bad', len(bad))
    for f in bad[:15]: print(' ', json.dumps(f, ensure_ascii=False)[:160])

print('\n\n=== MARKET ===')
m = load('market.json')
print('missing:', m.get('missing'))
for grp, body in m['data'].items():
    lst = body.get('quotes') or body.get('items') or body.get('sectors') or []
    if isinstance(body, dict) and not lst:
        print('--', grp, 'keys', list(body)[:8])
        continue
    print('--', grp, len(lst))
    for q in lst[:40]:
        if not isinstance(q, dict): continue
        sp = q.get('sparkline') or []
        rng = ''
        if len(sp) > 1:
            rng = ' [range %.2f→%.2f]' % (min(sp), max(sp))
        print('   %-22s %-10s last=%-12s chg=%-8s%s' % (
            (q.get('symbol') or '')[:22], (q.get('display') or q.get('name') or '')[:10],
            q.get('price', q.get('value', q.get('changePercent'))), round(q.get('change', 0), 3) if isinstance(q.get('change'), (int,float)) else q.get('change'), rng))

print('\n\n=== RISK (CII) ===')
r = load('risk.json')
print('degraded=%s stale=%s' % (r.get('degraded'), r.get('stale')))
sc = r['ciiScores']
print('countries:', len(sc))
for s in sorted(sc, key=lambda x: -x['combinedScore'])[:15]:
    print('%-4s combined=%-5s static=%-5s dyn=%-6s advisory=%-14s %s' % (
        s['region'], s['combinedScore'], s['staticBaseline'], s['dynamicScore'], s.get('advisoryLevel'), s.get('advisoryProvenance')))
print('\nstrategicRisks:')
print(json.dumps(r['strategicRisks'], ensure_ascii=False)[:1500])

print('\n\n=== NATURAL ===')
n = load('natural.json')
print('dataAvailable=', n.get('dataAvailable'), 'events=', len(n.get('events', [])))

print('\n=== HEALTH ===')
h = load('health.json')
print(json.dumps(h, ensure_ascii=False)[:1500])
