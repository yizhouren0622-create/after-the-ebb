"""Knowledge aid limits, no-penalty guarantees and milestone persistence."""
import copy
import json
import pickle
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'game' / 'python-packages'))
import survival as g
import knowledge_aid as aid
import achievements as awards

checks = 0


def check(ok, message):
    global checks
    checks += 1
    assert ok, message


def world(s):
    keys = ['day', 'ap', 'loc', 'inv', 'crew', 'seed', 'knowledge', 'bond', 'gear',
            'flags', 'unlocked', 'visits', 'pending', 'night_count', 'difficulty']
    return copy.deepcopy({key: s[key] for key in keys})


def dismiss(s):
    g.acknowledge_feedback(s)


def answer_index(s, correct):
    q = aid.BY_ID[s['quiz']['id']]
    return next(i for i, option in enumerate(s['quiz']['order']) if (option == q['correct']) == correct)


def solve(s, item, correct=True):
    dismiss(s)
    check(g.dispatch(s, ('quiz_start', item)), 'Could not request ' + item)
    token = s['quiz']['token']
    check(g.dispatch(s, ('quiz_answer', token, answer_index(s, correct))), 'Answer failed')
    check(s['feedback']['kind'] == 'quiz_answer' and s['quiz'] is None, 'No result')
    return token


# Explicit limits: the feature never provides story components or clues.
check(len(aid.QUESTIONS) == 32 and len(aid.BY_ID) == 32, 'Question IDs are not unique')
check(set(aid.LIMITS) == set(g.ITEMS) - {'core', 'battery'}, 'Story items leaked into aid')
check({q['type'] for q in aid.QUESTIONS} == {'选择题', '判断题'}, 'Missing question format')
for q in aid.QUESTIONS:
    check(bool(q['explanation']) and 0 <= q['correct'] < len(q['answers']), 'Invalid question')
    check(len(set(q['answers'])) == len(q['answers']), 'Ambiguous answer labels')

# Answers are checked against stable IDs, not shuffled positions.
for q in aid.QUESTIONS:
    for correct in [False, True]:
        s = g.new_game(seed=68)
        s['inv']['med'] = 0
        check(g.dispatch(s, ('quiz_start', 'med')), 'Quiz start failed')
        s['quiz']['id'] = q['id']
        s['quiz']['order'] = list(reversed(range(len(q['answers']))))
        before = world(s)
        token = s['quiz']['token']
        check(g.dispatch(s, ('quiz_answer', token, answer_index(s, correct))), 'Question answer failed')
        expected = copy.deepcopy(before)
        if correct: expected['inv']['med'] = 1
        check(world(s) == expected, 'Answer changed world beyond its reward: ' + q['id'])
        check(s['quiz_last_result']['correct'] == correct, 'Wrong correctness')
        check(q['explanation'] in '\n'.join(s['feedback']['notes']), 'Explanation not displayed')
        repeated = copy.deepcopy(s)
        check(not g.dispatch(s, ('quiz_answer', token, 0)) and s == repeated, 'Duplicate reward')

# One success fills the deficit exactly, including fractional food.
for item, limit in aid.LIMITS.items():
    for owned in [0, limit - .5]:
        s = g.new_game(); s['inv'][item] = owned
        before = world(s)
        solve(s, item)
        check(s['inv'][item] == limit, 'Overfilled emergency bundle')
        check(s['feedback']['groups'][0]['title'] == '物资变化', 'Reward not recorded')
        dismiss(s)
        before_full = copy.deepcopy(s)
        check(not g.dispatch(s, ('quiz_start', item)) and s == before_full, 'Unlimited stock farming')
        s['inv'][item] -= .5
        solve(s, item)
        check(s['inv'][item] == limit and s['day'] == before['day'] and s['ap'] == before['ap'], 'Second request was limited')

# No daily attempt quota. Incorrect answers, cancellation and retries cost nothing.
s = g.new_game(seed=31)
for _ in range(40):
    before = world(s)
    solve(s, 'med', False)
    check(world(s) == before, 'Wrong answer imposed a penalty')
dismiss(s)
check(g.dispatch(s, ('quiz_start', 'med')), 'Retry quota appeared')
active = copy.deepcopy(s)
for command in [('rest',), ('explore',), ('night', 0, 0, False), ('quiz_start', 'food'),
                ('quiz_answer', 'stale-token', 0), ('quiz_answer', s['quiz']['token'], True),
                ('quiz_answer', s['quiz']['token'], 99)]:
    check(not g.dispatch(s, command) and s == active, 'Quiz lock or input validation failed')
loaded = pickle.loads(pickle.dumps(s))
check(loaded['quiz'] == active['quiz'], 'Load changed question, answers or reward')
before = world(s)
check(g.dispatch(s, ('quiz_cancel',)) and world(s) == before, 'Cancellation cost something')

# The first deck is non-repeating and cannot alter exploration RNG.
s = g.new_game(seed=71)
ids = []
for _ in range(32):
    check(g.dispatch(s, ('quiz_start', 'med')), 'Deck stopped')
    ids.append(s['quiz']['id'])
    g.dispatch(s, ('quiz_cancel',))
check(len(set(ids)) == 32, 'Questions repeated before the deck was exhausted')
check(s['seed'] == 71, 'Knowledge questions changed exploration RNG')
check(g.dispatch(s, ('quiz_start', 'med')) and s['quiz']['id'] != ids[-1], 'Deck seam repeated same question')
g.dispatch(s, ('quiz_cancel',))

# Gentle mode, story scenes, satisfied bundles and terminal saves refuse aid.
for kind in ['gentle', 'pending', 'ending', 'full']:
    s = g.new_game(difficulty='gentle' if kind == 'gentle' else 'standard')
    if kind == 'pending': g.explore(s)
    if kind == 'ending': s['ending'] = 'lost'
    if kind == 'full': s['inv']['med'] = 1
    original = copy.deepcopy(s)
    check(not g.dispatch(s, ('quiz_start', 'med')) and s == original, 'Aid bypassed ' + kind)
s = g.new_game(); s['crew'][0]['hp'] = 20
check(aid.shortfalls(s)[0]['item'] == 'med', 'Injury not prioritized')
s['crew'][0]['hp'] = 90; s['inv']['food'] = 0
check(aid.shortfalls(s)[0]['item'] == 'food', 'Tonight food not prioritized')
s = g.new_game(); s.update(day=13, ap=0); s['inv']['food'] = .5
before = world(s); solve(s, 'food')
check(s['inv']['food'] == 2 and s['day'] == 13 and s['ap'] == 0, 'Aid blocked during storm or after AP exhaustion')
check(s['seed'] == before['seed'], 'Storm aid changed exploration RNG')

# Talking only counts when the story choice is completed, once per day.
s = g.new_game()
for day in range(1, 6):
    s.update(day=day, ap=3)
    dismiss(s)
    check(g.dispatch(s, ('talk',)), 'Talk could not start')
    if day == 5: check('daily_talk' not in s['earned_achievements'], 'Talk credited before completion')
    check(g.dispatch(s, ('choose', 0)), 'Talk could not finish')
check('daily_talk' in s['earned_achievements'], 'Five-day talk achievement missing')
s.update(day=7, ap=3); dismiss(s); g.dispatch(s, ('talk',)); g.dispatch(s, ('choose', 0))
check(s['milestones']['talk_current'] == 1 and s['milestones']['talk_streak'] == 5, 'Talk gap not handled')

# Near death is credited while alive, then recovery is tracked across actions.
s = g.new_game(); s['crew'][0]['hp'] = 4; s['inv']['med'] = 3
check(g.dispatch(s, ('use', 'food', 1)), 'Could not observe critical survivor')
check('edge' in s['earned_achievements'], 'Near-death achievement missing')
for _ in range(2): dismiss(s); g.dispatch(s, ('use', 'med', 0))
check(s['crew'][0]['hp'] == 60 and 'comeback' in s['earned_achievements'], 'Recovery achievement missing')
s = g.new_game(); s['crew'][0]['hp'] = 0; s['ending'] = 'lost'; awards.update(s)
check('edge' not in s['earned_achievements'], 'Death incorrectly credited as survival')

# Nutrition/fire streaks and actual weather survival.
s = g.new_game(); s['inv'].update(food=50, fuel=20); s['gear'] = ['coats', 'shelter', 'shelter2']
for _ in range(7):
    dismiss(s)
    check(g.dispatch(s, ('night', 1, 1, True)), 'Night setup failed')
check({'first_night', 'warmth', 'full_meals', 'cold', 'hoarder', 'home'} <= set(s['earned_achievements']), 'Night or camp achievements missing')
s['day'] = 13; dismiss(s); g.dispatch(s, ('night', 1, 1, True))
check('storm' in s['earned_achievements'], 'Storm survival missing')

# State milestones, quiz success, true ending and cross-campaign best records.
s = g.new_game(); s['inv'].update(wood=24, med=0)
s['gear'] = ['shelter', 'shelter2', 'stove', 'coats', 'trap', 'knife']
s['visits'] = {'shore': 12}; s['loc'] = 'tower'
awards.update(s)
check({'warehouse', 'maker', 'explorer', 'tower'} <= set(s['earned_achievements']), 'State milestone missing')
for _ in range(5):
    s['inv']['med'] = 0
    solve(s, 'med')
check('quiz' in s['earned_achievements'], 'Quiz achievement missing')
s['ending'] = 'tomorrow'; awards.update(s)
check('tomorrow' in s['earned_achievements'], 'Ending achievement missing')
earned, best, new = awards.merge([], {}, s)
again, same_best, repeated = awards.merge(earned, best, s)
check(again == earned and same_best == best and not repeated, 'Achievement unlocked more than once')
fresh = g.new_game()
next_earned, next_best, _ = awards.merge(earned, best, fresh)
check(next_earned == earned and next_best == best, 'New journey erased old achievements')

# Real old talk journals can migrate; unknown historical statistics are not invented.
s = g.new_game(); s['day'] = 6
s['log'] = [{'day': day, 'title': '录音师', 'text': ''} for day in range(1, 6)]
for key in ['quiz', 'quiz_seen', 'quiz_seed', 'quiz_seq', 'quiz_last_result', 'milestones', 'earned_achievements']:
    s.pop(key, None)
seed = s['seed']; g.upgrade_state(s)
check('daily_talk' in s['earned_achievements'] and s['seed'] == seed, 'Old talks did not migrate safely')
check(s['quiz'] is None and not s['milestones'].get('comeback'), 'Invented old progress')

result = {'checks': checks, 'questions': len(aid.QUESTIONS), 'achievements': len(awards.DEFINITIONS),
          'no_penalty_or_daily_quota': True, 'deficit_only_rewards': True,
          'independent_question_rng': True, 'saved_question_and_duplicate_awards_checked': True,
          'cross_campaign_merge_and_old_journal_migration': True}
(ROOT / 'tests' / 'knowledge-achievements-validation.json').write_text(json.dumps(result, indent=2) + '\n', 'utf-8')
print(json.dumps(result, indent=2))
