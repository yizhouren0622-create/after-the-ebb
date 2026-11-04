"""Player-visible branches, one-time rewards, forecasts and reading migration."""
import copy
import itertools
import json
import pickle
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'game/python-packages'))
import survival as g
import storybook as book
import keepsakes

checks = 0
def check(condition, message):
    global checks
    checks += 1
    assert condition, message

def chinese(text):
    return isinstance(text, str) and any('\u4e00' <= c <= '\u9fff' for c in text)

for collection in [book.TEXT, book.TALKS, book.ENDINGS, book.PARTNER_ENDINGS, book.NIGHTS, book.TALK_RESULTS]:
    for title, text in collection.items():
        check(chinese(text), 'Missing Chinese text: ' + title)
for title, texts in book.RESULTS.items():
    check(all(chinese(text) for text in texts) and bool(texts), 'Missing Chinese response: ' + title)

# Every authored branch has a result, including both choices in the new stories.
for row in book.THREADS:
    for index in range(len(row['options'])):
        s = g.new_game()
        s.update(loc=row['loc'], day=row.get('day', 1), visits={row['loc']: max(1, row.get('visit', 1) - 1)})
        s['inv'] = dict.fromkeys(g.ITEMS, 10)
        if row.get('flag'): s['flags'].append(row['flag'])
        # Disable unrelated earlier threads to isolate the encounter under test.
        s['story_seen'] = [r['id'] for r in book.THREADS if r != row]
        before = g.amt(s, 'food')
        check(g.dispatch(s, ('explore',)), 'Cannot open ' + row['id'])
        check(s['pending']['title'] == row['title'], 'Wrong encounter ' + row['id'])
        check(s['ap'] == 2, 'Encounter charged wrong AP')
        restored = pickle.loads(pickle.dumps(s))
        check(g.dispatch(restored, ('choose', index)), 'Cannot choose branch')
        check(restored['feedback']['description'] == row['options'][index][3], 'Generic result')
        record = keepsakes.merge_records({}, restored['feedback'])
        check(keepsakes.seen(record, row['title'], index), 'Chosen result not recorded')
        check(not keepsakes.seen(record, row['title'], 1-index) if len(row['options']) == 2 else True, 'Invented other result')
        same = keepsakes.merge_records(record, restored['feedback'])
        check(same == record, 'Replaying autosave duplicates reading record')
        state = copy.deepcopy(restored)
        check(not g.dispatch(restored, ('choose', index)) and restored == state, 'Duplicate reward')
        check(book.next_thread(restored, g) is None, 'One-time thread repeated')

# Return story cannot occur before help or the required date.
s = g.new_game(); s.update(loc='town', day=7, visits={'town': 2})
check(book.next_thread(s, g) is None, 'Reward without helping')
s['flags'].append('helped'); s['day'] = 5
check(book.next_thread(s, g) is None, 'Return too early')
s['day'] = 6
check(book.next_thread(s, g)['title'] == '门终于开了一条缝', 'No delayed response')

# Marking the passage changes travel, not just the prose.
for sled in [False, True]:
    a = g.new_game(); a.update(loc='flats', day=14, unlocked=['flats', 'tower'])
    if sled: a['gear'].append('sled')
    b = copy.deepcopy(a); b['flags'].append('safe_crossing')
    check(g.travel(a, 'flats') is False, 'Moved into same location')
    a['loc'] = b['loc'] = 'tower'
    check(g.dispatch(a, ('travel', 'flats')) and g.dispatch(b, ('travel', 'flats')), 'Crossing failed')
    check(b['crew'][0]['energy'] == a['crew'][0]['energy'] + 2, 'Marked crossing did not save energy')
    check(any('减少 2' in n for n in b['feedback']['notes']), 'Unexplained travel effect')

# All 9 portion combinations, fire, weather, injuries, gear and both modes.
for day, mode, equipment, r0, r1, fire in itertools.product(
        [1, 6, 12, 18], ['standard', 'gentle'], [[], ['shelter', 'coats']], [0, .5, 1], [0, .5, 1], [False, True]):
    s = g.new_game(difficulty=mode)
    s.update(day=day, gear=equipment[:])
    s['crew'][0].update(hp=19, hurt=True)
    old = copy.deepcopy(s)
    preview = g.night_preview(s, r0, r1, fire)
    check(s == old, 'Preview changed real save')
    actual = copy.deepcopy(s); check(g.night(actual, r0, r1, fire), 'Night rejected')
    check(preview == {'crew': actual['crew'], 'ending': actual['ending'], 'day': actual['day']}, 'Preview disagrees with rules')

old = g.new_game()
old.pop('story_seen'); old.pop('loadout')
before = copy.deepcopy(old); g.upgrade_state(old)
check(old['story_seen'] == [] and old['seed'] == before['seed'], 'Migration changed random state')
check(len(keepsakes.unlocked([row[0] for row in __import__('achievements').DEFINITIONS])) == 8, 'Cannot collect all objects')
check(not keepsakes.unlocked([]), 'Objects available without achievements')
check(len(book.TALKS) == 18, 'Conversations repeat before the eighteen-day deadline')
for field, key in [('hp', 'lost'), ('sanity', 'drift')]:
    s = g.new_game(); s['crew'][1][field] = 0
    check(g.ending_text(s, key) == book.PARTNER_ENDINGS[key], 'Narrator incorrectly takes partner condition')

result = {'status': 'PASSED', 'checks': checks, 'new_threads': len(book.THREADS),
          'chinese_scene_texts': len(book.TEXT) + len(book.TALKS) + len(book.ENDINGS),
          'night_forecast_scenarios': 4 * 2 * 2 * 3 * 3 * 2,
          'one_time_branch_rewards': True, 'reading_records_survive_replay': True,
          'old_save_migration': True, 'title_objects': 8}
(ROOT / 'tests/storybook-validation.json').write_text(json.dumps(result, indent=2) + '\n', 'utf-8')
print(json.dumps(result, indent=2))
