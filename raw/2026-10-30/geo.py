#!/usr/bin/env python3
"""地缘冲突 + 政治变化 专题抽取（给日报用）"""
import json, os, re, datetime, collections, textwrap

D = os.path.dirname(os.path.abspath(__file__))
CST = datetime.timezone(datetime.timedelta(hours=8))
news = json.load(open(os.path.join(D, 'news.json'), encoding='utf-8'))
ts = lambda ms: datetime.datetime.fromtimestamp(ms/1000, CST).strftime('%m-%d %H:%M')

items = []
for c, b in news['categories'].items():
    for it in b.get('items', []):
        it['_cat'] = c
        items.append(it)

THEATERS = {
    '霍尔木兹/伊朗战争': r'hormuz|strait|tanker|\biran\b|tehran|irgc|persian gulf|mine\b',
    '以色列/黎巴嫩/加沙': r'israel|netanyahu|gaza|lebanon|hezbollah|west bank|idf\b',
    '也门/红海': r'houthi|yemen|aden|red sea|bab el',
    '俄乌战争': r'ukrain|russia|moscow|kyiv|putin|donbas|zaporizh|crimea|drone strike',
    '朝鲜半岛': r'north korea|pyongyang|kim jong|south korea|seoul|kospi',
    '台海/南海/中日': r'taiwan|south china sea|beijing|pla\b|senkaku|diaoyu|japan.*china|china.*japan',
    '南亚（印巴阿）': r'pakistan|india.*border|kashmir|afghan|taliban|bangladesh|sri lanka|nepal',
    '非洲冲突（萨赫勒/苏丹/埃塞）': r'\bsudan|sahel|mali|burkina|niger\b|tigray|ethiopia|somali|darfur|el fasher|congo|mozambiq',
    '拉美（委内瑞拉/墨/巴西）': r'venezuela|maduro|machado|caracas|mexico|bolsonaro|brazil|colombia|haiti|ecuador',
    '欧洲政治与安全': r'\beu\b|european union|nato|brussels|\buk\b|parliament|germany|france|poland|hungary|italy',
    '美国内政与选举': r'trump|congress|senate|house race|midterm|democrat|republican|white house|pentagon|state dept|supreme court',
}
POLITICS_RX = re.compile(r'elect|coalition|vote|parliament|coup|protest|sanction|resign|appoint|treaty|summit|ceasefire|talk|minister|president|prime minister|policy|bill\b|regulation|tariff|ban\b|censor|arrest|corrupt|referendum|impeach', re.I)
CONFLICT_RX = re.compile(r'strike|attack|missile|drone|bomb|killed|casualt|troop|offensive|raid|clash|militan|insurg|ceasefire|front( line)?|shell|air ?defen|artillery|IED\b|hostage|blockade|sanction|mobiliz|conscription', re.I)

buckets = collections.defaultdict(list)
uncat = []
for it in items:
    txt = (it['title'] or '') + ' ' + (it.get('snippet') or '')
    hit = [name for name, pat in THEATERS.items() if re.search(pat, txt, re.I)]
    if hit:
        for h in hit:
            buckets[h].append(it)
    else:
        uncat.append(it)

cov = news['coverage']
mx = max(i['publishedAt'] for i in items)
print('覆盖率: items=%s publishers=%s feeds=%s/%s' % (cov['itemsServed'], cov['publisherCount'], cov['feedCompleted'], cov['feedTotal']))
print('时间窗: %s → %s CST' % (ts(min(i['publishedAt'] for i in items)), ts(mx)))
print('总条目 %d ；被战区归类 %d ；未归类 %d' % (len(items), len(items) - len(uncat), len(uncat)))
print()

order = sorted(buckets.items(), key=lambda kv: -max(i['importanceScore'] for i in kv[1]))
for name, lst in order:
    uniq = {}
    for i in lst:
        k = re.sub(r'\W+', '', (i['title'] or '')[:45]).lower()
        if k not in uniq or i['importanceScore'] > uniq[k]['importanceScore']:
            uniq[k] = i
    lst2 = sorted(uniq.values(), key=lambda x: -x['publishedAt'])
    hi = max(x['importanceScore'] for x in lst2)
    print('=' * 10, '%s  条目 %d（去重 %d），最高分 %d' % (name, len(lst), len(lst2), hi))
    for i in sorted(lst2, key=lambda x: (-x['importanceScore'], -x['publishedAt']))[:14]:
        th = i.get('threat') or {}
        print('  [%s] %-16s sc=%-3s %s' % (ts(i['publishedAt']), str(i['source'])[:16], i['importanceScore'], (i['title'] or '')[:104]))
        s = (i.get('snippet') or '').strip().replace('\n', ' ')
        if s and len(s) > 60:
            print('        ' + textwrap.shorten(s, 230))
    print()

print('=' * 10, '政治/治理类信号（跨战区，按政治动作关键词筛）')
pol = [i for i in items if POLITICS_RX.search((i['title'] or '') + ' ' + (i.get('snippet') or ''))]
seen = set()
for i in sorted(pol, key=lambda x: -x['publishedAt'])[:30]:
    k = (i['title'] or '')[:40]
    if k in seen:
        continue
    seen.add(k)
    print('  [%s] %-16s %-10s %s' % (ts(i['publishedAt']), str(i['source'])[:16], i['_cat'], (i['title'] or '')[:100]))

print()
print('=' * 10, '冲突类信号（最新 20 条）')
con = [i for i in items if CONFLICT_RX.search(i['title'] or '')]
for i in sorted(con, key=lambda x: -x['publishedAt'])[:20]:
    print('  [%s] %-16s sc=%-3s %s' % (ts(i['publishedAt']), str(i['source'])[:16], i['importanceScore'], (i['title'] or '')[:100]))
