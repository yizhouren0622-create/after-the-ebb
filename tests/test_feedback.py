"""Regression checks for visible receipts, real deltas and save migration."""
import copy
import json
import pickle
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'game' / 'python-packages'))
import survival as g
import journey_feedback as f

checks = 0


def check(ok, message):
    global checks
    checks += 1
    assert ok, message


def receipt(s):
    check(bool(s.get('feedback')), 'No persisted outcome')
    r = s['feedback']
    check(bool(r['description']) and bool(r['selected']), 'Missing response')
    check(s['last_feedback'] == r, 'Outcome cannot be revisited')
    check(any(r['description'] in x['text'] for x in s['log']), 'Journal lacks response')
    check(pickle.loads(pickle.dumps(s)) == s, 'Result cannot survive save/restore')
    return f.plain_text(r)


def fresh():
    return g.new_game(seed=916)


# Every authored branch must have its own connected first-person response.
events = list(g.DISCOVERIES.values()) + [e for pool in g.POOLS.values() for e in pool]
for e in events:
    check(e['title'] in f.RESPONSES, 'Missing response: ' + e['title'])
    check(len(f.RESPONSES[e['title']]) == len(e['choices']), 'Wrong branch count')
    for i, c in enumerate(e['choices']):
        q = fresh()
        q['inv'] = dict.fromkeys(g.ITEMS, 25)
        q['gear'] = list(g.EQUIPMENT)
        q['pending'] = copy.deepcopy(e)
        q['crew'][0]['hp'] = 96
        check(g.dispatch(q, ('choose', i)), 'Authored choice failed')
        text = receipt(q)
        check(f.RESPONSES[e['title']][i] in text, 'Wrong authored continuation')
        check(c['text'] in text, 'Selected option not shown')
        for k, name in g.ITEMS.items():
            delta = c['effect'].get('items', {}).get(k, 0) - c['cost'].get(k, 0)
            if delta:
                check(name in text, 'Missing material delta')
                check(('（%s%s）' % ('+' if delta > 0 else '', f.number(delta))) in text, 'Incorrect material amount')

for title, _ in g.TALKS:
    check(title in f.RESPONSES, 'Missing camp response')
check('海消失的早晨' in f.RESPONSES and '不是回声' in f.RESPONSES, 'Missing story response')

# Exploration has one receipt including the paid action and the chosen reward.
q = fresh()
check(g.dispatch(q, ('explore',)), 'Explore failed')
check(q['feedback'] is None and q['action_origin']['ap'] == 3, 'Intermediate receipt interrupted event')
check(g.dispatch(q, ('choose', 0)), 'Explore choice failed')
text = receipt(q)
for expected in ['行动  3 → 2（-1）', '体力  85 → 75（-10）', '生食  0 → 3（+3）', '盐蚀街区']:
    check(expected in text, 'Exploration omitted ' + expected)
before = f.snapshot(q)
g.acknowledge_feedback(q)
check(f.snapshot(q) == before and q['feedback'] is None, 'Dismissal changed gameplay')
check(q['last_feedback'] is not None, 'Dismissal destroyed review')

# Resource exchanges must list both costs and gains, not only the reward.
q = fresh()
q['pending'] = copy.deepcopy(g.POOLS['town'][0])
check(g.dispatch(q, ('choose', 0)), 'Trade failed')
text = receipt(q)
check('口粮  6 → 4（-2）' in text and '废金属  3 → 6（+3）' in text, 'Trade omitted costs')

# Clamp at 100: describe actual +2, not the advertised theoretical +28.
q = fresh()
q['inv']['med'] = 1
q['crew'][0]['hp'] = 98
q['crew'][0]['hurt'] = True
check(g.dispatch(q, ('use', 'med', 0)), 'Treatment failed')
text = receipt(q)
check('生命  98 → 100（+2）' in text, 'Treatment overstates recovery')
check('受伤状态已解除' in text and '药品  1 → 0（-1）' in text, 'Missing treatment effect')
check(q['feedback']['figures'] and q['feedback']['cue'] == 'cloth', 'Wrong treatment presentation')

# Full health/energy/sanity really means no change, not a fabricated bonus.
q = fresh()
for p in q['crew']:
    for k in ['hp', 'energy', 'sanity']: p[k] = 100
check(g.dispatch(q, ('use', 'food', 1)), 'Food failed')
check('生命、体力、精神均未改变' in receipt(q), 'Clamped food fabricated effects')

# Every recipe has a complete narrative, consumed materials and equipment/output.
for key, (_, cost, _, _) in g.RECIPES.items():
    q = fresh()
    q['inv'] = dict.fromkeys(g.ITEMS, 30)
    q['knowledge'] = 20
    if key == 'shelter2': q['gear'].append('shelter')
    if key == 'cook': q['gear'].append('stove')
    check(g.dispatch(q, ('craft', key)), 'Recipe failed: ' + key)
    text = receipt(q)
    check(f.CRAFT_TEXT[key] in text, 'Missing crafting narrative')
    check('行动  3 → 2（-1）' in text, 'Recipe omitted action cost')
    check(all(g.ITEMS[k] in text for k in cost), 'Recipe omitted materials')
    if key in g.EQUIPMENT: check('新增装备' in text, 'Equipment not listed')

# Night combines rations, fire, spoilage, trap loot, injuries and a new day.
q = fresh()
q.update(day=6, ap=1)
q['inv'].update(food=20, fuel=2)
q['gear'] = ['trap']
q['crew'][0]['hurt'] = True
check(g.dispatch(q, ('night', .5, 1, True)), 'Night failed')
text = receipt(q)
for expected in ['口粮  20 → 16.5（-3.5）', '燃料  2 → 1（-1）', '生食  0 → 2（+2）', '损坏', '失温', '伤口', '新一天恢复', '第 7 日']:
    check(expected in text, 'Night omitted ' + expected)
check(q['feedback']['figures'] and q['feedback']['cue'] == 'fire', 'Wrong night presentation')

# Invalid/cancelled actions must not replace an outcome or make sound.
q = fresh()
before = copy.deepcopy(q)
check(not g.dispatch(q, ('craft', 'horn')) and q == before, 'Invalid action mutated feedback')
check(not g.dispatch(q, ('choose', 99)) and q == before, 'Invalid choice mutated feedback')

# Already published journeys have no new fields: they still load and act safely.
q = fresh()
for key in ['feedback', 'last_feedback', 'action_origin']: q.pop(key)
g.upgrade_state(q)
check(g.dispatch(q, ('rest',)), 'Old save cannot act')
receipt(q)

# Final night: receipt must remain available before the ending is shown.
q = fresh(); q['day'] = 18
check(g.dispatch(q, ('night', 1, 1, False)), 'Final night failed')
check(q['ending'] == 'silent' and bool(q['feedback']), 'Ending swallowed receipt')

result = {'checks': checks, 'event_branches': sum(len(e['choices']) for e in events),
          'all_recipes': len(g.RECIPES), 'old_save_migration': True,
          'actual_clamped_deltas': True, 'night_receipt': True}
(ROOT / 'tests' / 'feedback-validation.json').write_text(json.dumps(result, indent=2) + '\n', 'utf-8')
print(json.dumps(result, indent=2))
