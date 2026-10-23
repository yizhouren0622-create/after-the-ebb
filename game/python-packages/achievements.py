"""Campaign milestones. The UI separately persists unlocked IDs and best runs."""

DEFINITIONS = [
    ('first_night', '熬过第一夜', '两个人一起活过第一晚。', 'nights', 1),
    ('daily_talk', '每天都想听你说', '连续 5 天完成营火谈心。', 'talk_streak', 5),
    ('hoarder', '囤囤鼠', '共同口粮储备达到 16 份。', 'food_peak', 16),
    ('warehouse', '废墟里的仓库', '木料、废金属、布料、燃料和导线合计达到 24 份。', 'materials_peak', 24),
    ('edge', '命悬一线', '有人生命只剩 1–5 点时，两个人仍然活着。', 'edge', 1),
    ('comeback', '力挽狂澜', '曾有人生命或精神不高于 15，再让两人的生命恢复到 60、精神恢复到 50。', 'comeback', 1),
    ('home', '风吹不散的家', '完成营地加固。', 'reinforced', 1),
    ('maker', '修修补补也能活', '在同一段旅途中制作 6 种永久装备。', 'equipment', 6),
    ('explorer', '废墟丈量者', '在同一段旅途中完成 12 次探索。', 'explorations', 12),
    ('full_meals', '没让你挨饿', '连续 7 晚都给两人分配完整口粮。', 'meal_streak', 7),
    ('warmth', '三夜微光', '连续 3 晚生火过夜。', 'fire_streak', 3),
    ('cold', '寒夜尽头', '两人一起度过第 7 日的寒流之夜。', 'cold', 1),
    ('storm', '盐暴之后', '两人一起度过第 13 日的盐暴之夜。', 'storm', 1),
    ('quiz', '知识就是补给', '在同一段旅途中答对 5 道知识补给题。', 'quiz_correct', 5),
    ('tower', '并肩走到这里', '两人生命均不低于 25 时，抵达守潮灯塔。', 'tower', 1),
    ('tomorrow', '把明天还给世界', '达成结局「没有天气预报的明天」。', 'tomorrow', 1),
]
BY_ID = {entry[0]: entry for entry in DEFINITIONS}
TALK_TITLES = {'第一件想做的事', '录音师', '没说完的话', '各自的节拍', '如果没有明天', '记住名字'}


def upgrade(s):
    if 'milestones' not in s:
        # Old journals retain talk dates, so a known streak can be reconstructed.
        days = sorted({e['day'] for e in s.get('log', []) if e['title'] in TALK_TITLES})
        streak = best = 0
        previous = -2
        for day in days:
            streak = streak + 1 if day == previous + 1 else 1
            best = max(best, streak)
            previous = day
        s['milestones'] = {'talk_streak': best, 'talk_current': streak,
                           'talk_last_day': previous, 'meal_current': 0,
                           'fire_current': 0, 'ever_critical': False}
    s.setdefault('earned_achievements', [])


def update(s, command=(), before=None, source=None):
    upgrade(s)
    m = s['milestones']
    kind = command[0] if command else ''
    alive = not s['ending'] or s['ending'] in ['tomorrow', 'shelter', 'voice']
    if alive:
        if any(0 < p['hp'] <= 5 for p in s['crew']): m['edge'] = 1
        if any(p['hp'] <= 15 or p['sanity'] <= 15 for p in s['crew']): m['ever_critical'] = True
        if m['ever_critical'] and all(p['hp'] >= 60 and p['sanity'] >= 50 for p in s['crew']):
            m['comeback'] = 1
    if kind == 'choose' and source and source.get('tag') == '营火旁':
        last = m.get('talk_last_day', -2)
        if last != s['day']:
            m['talk_current'] = m.get('talk_current', 0) + 1 if last == s['day'] - 1 else 1
            m['talk_last_day'] = s['day']
            m['talk_streak'] = max(m.get('talk_streak', 0), m['talk_current'])
    if kind == 'night' and alive:
        m['meal_current'] = m.get('meal_current', 0) + 1 if command[1] == command[2] == 1 else 0
        m['fire_current'] = m.get('fire_current', 0) + 1 if command[3] else 0
        m['meal_streak'] = max(m.get('meal_streak', 0), m['meal_current'])
        m['fire_streak'] = max(m.get('fire_streak', 0), m['fire_current'])
    if kind == 'quiz_answer' and s.get('quiz_last_result', {}).get('correct'):
        m['quiz_correct'] = m.get('quiz_correct', 0) + 1
    m['nights'] = s['night_count'] if alive else max(0, s['night_count'] - 1)
    m['food_peak'] = max(m.get('food_peak', 0), s['inv'].get('food', 0))
    materials = sum(s['inv'].get(k, 0) for k in ['wood', 'scrap', 'cloth', 'fuel', 'wire'])
    m['materials_peak'] = max(m.get('materials_peak', 0), materials)
    m['reinforced'] = int('shelter2' in s['gear'])
    m['equipment'] = len(s['gear'])
    m['explorations'] = sum(s['visits'].values())
    if alive and s['day'] > 7: m['cold'] = 1
    if alive and s['day'] > 13: m['storm'] = 1
    if alive and s['loc'] == 'tower' and all(p['hp'] >= 25 for p in s['crew']): m['tower'] = 1
    if s['ending'] == 'tomorrow': m['tomorrow'] = 1
    newly = []
    for key, _, _, field, target in DEFINITIONS:
        if m.get(field, 0) >= target and key not in s['earned_achievements']:
            s['earned_achievements'].append(key)
            newly.append(key)
    return newly


def progress(s):
    m = s.get('milestones', {}) if s else {}
    return {key: min(target, m.get(field, 0)) for key, _, _, field, target in DEFINITIONS}


def merge(earned, best, s):
    """Pure merge, usable by both persistent UI data and regression tests."""
    earned = list(earned)
    best = dict(best)
    newly = [key for key in s.get('earned_achievements', []) if key in BY_ID and key not in earned]
    earned.extend(newly)
    for key, value in progress(s).items(): best[key] = max(best.get(key, 0), value)
    return earned, best, newly
