"""Optional, unlimited knowledge aid; only fills missing basic supplies.

The question deck has its own saved RNG, separate from exploration. Stable IDs
and saved answer order keep a question unchanged across save/load.
"""

# One emergency bundle, not an endless inventory increase. Story components
# (receiver core and battery), knowledge, clues and equipment are never granted.
LIMITS = {'food': 2, 'raw': 2, 'wood': 3, 'scrap': 3,
          'cloth': 3, 'fuel': 2, 'wire': 2, 'med': 1}


def mc(key, category, prompt, answers, correct, explanation):
    return {'id': key, 'category': category, 'type': '选择题', 'prompt': prompt,
            'answers': list(answers), 'correct': correct, 'explanation': explanation}


def tf(key, category, prompt, correct, explanation):
    return mc(key, category, prompt, ['正确', '错误'], 0 if correct else 1, explanation) | {'type': '判断题'}


QUESTIONS = [
    mc('km', '单位换算', '一段路长 1.5 千米，换算成米是多少？', ['150 米', '1500 米', '15000 米'], 1,
       '1 千米等于 1000 米，所以 1.5 千米是 1500 米。'),
    mc('area', '单位换算', '1 平方米等于多少平方厘米？', ['100', '1000', '10000'], 2,
       '1 米等于 100 厘米。换算面积时两条边都要换算，因此是 100 × 100 = 10000 平方厘米。'),
    mc('litre', '单位换算', '750 毫升加上 0.5 升，一共是多少升？', ['0.8 升', '1.25 升', '1.75 升'], 1,
       '1000 毫升等于 1 升。750 毫升是 0.75 升，加上 0.5 升就是 1.25 升。'),
    mc('speed', '单位换算', '匀速行驶的车每小时走 36 千米，相当于每秒多少米？', ['10 米', '36 米', '100 米'], 0,
       '36 千米是 36000 米，1 小时是 3600 秒。36000 ÷ 3600 = 10，所以速度是每秒 10 米。'),
    mc('fraction', '数学', '一箱物资拿走了四分之三，拿走的部分占原来多少？', ['25%', '50%', '75%'], 2,
       '四分之三等于 0.75，换算成百分数就是 75%。剩下的部分才是 25%。'),
    mc('average', '数学', '三次测得的长度分别是 4、6、8 米，平均值是多少？', ['5 米', '6 米', '7 米'], 1,
       '先把三个数相加，再除以测量次数：(4 + 6 + 8) ÷ 3 = 6 米。'),
    mc('triangle', '数学', '一个直角三角形的两条直角边分别长 3 米和 4 米，斜边长多少？', ['5 米', '6 米', '7 米'], 0,
       '根据勾股定理，斜边的平方是 3 × 3 + 4 × 4 = 25，所以斜边长 5 米。'),
    mc('negative', '数学', '计算（-3）×（-4），结果是多少？', ['-12', '-7', '12'], 2,
       '两个负数相乘得到正数，3 × 4 = 12，所以结果是 12。'),
    mc('gcd', '数学', '把 12 根木条和 18 根铁丝平均分成若干份，每份两种材料的数量都一样且没有剩余，最多能分几份？', ['3 份', '6 份', '12 份'], 1,
       '份数必须同时整除 12 和 18。它们的最大公因数是 6，因此最多分成 6 份，每份有 2 根木条和 3 根铁丝。'),
    mc('coin', '概率', '连续抛两次公平硬币，两次都正面朝上的概率是多少？', ['1/4', '1/2', '3/4'], 0,
       '两次抛掷相互独立，各自出现正面的概率都是 1/2。两次都是正面的概率是 1/2 × 1/2 = 1/4。'),
    mc('series', '电学', '在稳定的简单串联电路中，流过两个串联电阻的电流有什么关系？', ['靠近电源的更大', '两个相同', '电阻较大的那段更小'], 1,
       '串联电路只有一条电流通路。在稳定状态下，流过串联各元件的电流相同，电压则可以不同。'),
    mc('energy', '物理', '下面哪个是能量的国际单位？', ['瓦特', '牛顿', '焦耳'], 2,
       '焦耳是能量和功的单位；瓦特表示功率，牛顿表示力。'),
    mc('weight', '物理', '用国际单位表示质量，通常应该使用哪个单位？', ['千克', '牛顿', '帕斯卡'], 0,
       '千克是质量单位。牛顿表示力，帕斯卡表示压强，三者不能直接当成同一种量。'),
    mc('equator', '地理', '纬度为 0° 的那条纬线叫什么？', ['北回归线', '赤道', '本初子午线'], 1,
       '赤道是 0° 纬线，划分南北半球。本初子午线是 0° 经线，不是纬线。'),
    mc('seasons', '天文', '地球四季变化的主要原因是什么？', ['地球在一年中离太阳忽远忽近', '地轴倾斜，且地球绕太阳公转', '月球改变了太阳的温度'], 1,
       '地轴相对公转轨道倾斜，使不同季节各半球获得阳光的角度和白昼长度不同。地日距离变化不是四季的主要原因。'),
    mc('lunar_eclipse', '天文', '月食发生时，哪一个天体位于太阳和月球之间？', ['地球', '金星', '水星'], 0,
       '月食发生时，地球位于太阳与月球之间，月球进入地球的影子。日食时则是月球挡在太阳和地球之间。'),
    tf('discount', '数学', '一件物品先降价 20%，再按降价后的价格涨价 20%，就会恢复原价。', False,
       '两次百分比的基数不同。假设原价为 100，降价后是 80，再涨 20% 得到 96，仍低于原价。'),
    tf('prime', '数学', '1 是质数。', False,
       '质数必须是大于 1、且只有 1 和它本身两个不同正因数的整数。1 不满足这个定义。'),
    tf('angles', '数学', '在通常的平面欧几里得几何中，三角形的内角和是 180°。', True,
       '平面欧几里得几何中的三角形内角和为 180°。题目限定了平面，避免与球面三角形混淆。'),
    tf('rectangle', '数学', '长方形的长和宽都扩大为原来的 2 倍，面积会扩大为原来的 4 倍。', True,
       '长方形面积等于长乘宽。两条边各乘以 2，面积就乘以 2 × 2 = 4。'),
    tf('necessary', '逻辑', '已知所有合格的箱子都有封条，因此只要箱子有封条，就一定合格。', False,
       '“合格就有封条”不能反过来推出“有封条就合格”。不合格的箱子也可能贴着封条，还需要其他条件才能判断。'),
    tf('negation', '逻辑', '对于两盏只有亮、灭两种状态的灯，“至少有一盏亮着”的否定是“两盏都没有亮”。', True,
       '要否定“至少一盏亮”，就必须让亮灯的数量为零，也就是两盏都不亮。'),
    tf('density', '物理', '两个物体体积相同，质量较大的物体平均密度更大。', True,
       '平均密度等于质量除以体积。体积相同而质量更大时，平均密度也更大。'),
    tf('vacuum', '物理', '普通声波可以像光一样，在没有任何物质的真空中传播。', False,
       '普通声波需要物质作为传播介质，例如空气、水或固体。真空里没有这样的介质，而光可以在真空中传播。'),
    tf('ohm', '电学', '对遵守欧姆定律的电阻而言，保持两端电压不变，电阻越大，电流就越大。', False,
       '欧姆定律是 I = U / R。电压不变时，电阻增大，电流反而减小。'),
    tf('power', '物理', '功率越大，表示单位时间内转移或消耗的能量越多。', True,
       '功率表示能量转移或做功的快慢。它等于能量除以所用时间，因此单位时间内的能量越多，功率越大。'),
    tf('moonlight', '天文', '我们通常看见的明亮月面，主要是因为月球反射了太阳光。', True,
       '月球本身不是像太阳那样发光的恒星。我们看见的月面亮光主要来自它反射的太阳光。'),
    tf('rotation', '天文', '地球上的昼夜交替，主要是地球绕太阳公转造成的。', False,
       '昼夜交替主要由地球自转造成。同一地点随地球转动，轮流面向太阳和背向太阳。'),
    tf('gregorian1900', '历法', '按照公历的闰年规则，1900 年是闰年。', False,
       '公历中，能被 100 整除的年份还必须能被 400 整除，才是闰年。1900 不能被 400 整除，所以是平年。'),
    tf('gregorian2000', '历法', '按照公历的闰年规则，2000 年是闰年。', True,
       '2000 能被 400 整除，因此即使它也是整百年，仍然是闰年。'),
    tf('hours', '单位换算', '1.5 小时等于 1 小时 50 分钟。', False,
       '0.5 小时是半小时，也就是 30 分钟。因此 1.5 小时等于 1 小时 30 分钟。'),
    tf('square_zero', '数学', '一个实数的平方不可能小于零。', True,
       '正数和负数的平方都为正，零的平方为零。因此对实数而言，平方总是不小于零。'),
]
BY_ID = {q['id']: q for q in QUESTIONS}


def shortfalls(s):
    """Read-only, ranked list; each reward equals only the missing quantity."""
    entries = []
    for key, limit in LIMITS.items():
        owned = s['inv'].get(key, 0)
        if owned >= limit: continue
        priority = 10
        reason = '未达到一份应急储备。'
        if key == 'food':
            priority, reason = 100, '两人今晚吃饱需要 2 份口粮。'
        elif key == 'med' and any(p['hurt'] or p['hp'] < 40 for p in s['crew']):
            priority, reason = 110, '有人受伤或生命偏低，先备一份药品。'
        elif key == 'fuel':
            priority = 80 if s['day'] in [5, 6, 7, 11, 12, 13] else 40
            reason = '燃料可用于生火保暖或烹饪。'
        elif key in ['wood', 'cloth'] and 'shelter' not in s['gear']:
            priority, reason = 70, '还没有搭好防风营地。'
        elif key == 'cloth' and 'coats' not in s['gear']:
            priority, reason = 60, '备齐 3 份布料就能缝制寒衣。'
        entries.append({'item': key, 'owned': owned, 'limit': limit,
                        'amount': limit - owned, 'reason': reason, 'priority': priority})
    return sorted(entries, key=lambda x: -x['priority'])


def available(s):
    return s['difficulty'] == 'standard' and not s['ending'] and not s.get('pending')


def _rand(s, size):
    s['quiz_seed'] = (1664525 * s.get('quiz_seed', s['seed'] ^ 0xA17D53) + 1013904223) % 2**32
    return s['quiz_seed'] % size


def start(s, item):
    if not available(s) or s.get('quiz') or s.get('feedback'): return False
    reward = next((r for r in shortfalls(s) if r['item'] == item), None)
    if not reward: return False
    seen = s.get('quiz_seen', [])
    pool = [q for q in QUESTIONS if q['id'] not in seen]
    if not pool:
        last = seen[-1] if seen else None
        seen = []
        pool = [q for q in QUESTIONS if q['id'] != last]
    q = pool[_rand(s, len(pool))]
    order = list(range(len(q['answers'])))
    # Keep true/false in familiar order; shuffle only multiple-choice answers.
    if len(order) > 2:
        for i in range(len(order) - 1, 0, -1):
            j = _rand(s, i + 1)
            order[i], order[j] = order[j], order[i]
    sequence = s.get('quiz_seq', 0) + 1
    s['quiz_seq'] = sequence
    s['quiz_seen'] = seen + [q['id']]
    s['quiz'] = {'id': q['id'], 'item': item, 'amount': reward['amount'],
                 'order': order, 'token': '%d-%d' % (sequence, s['quiz_seed'])}
    return True


def answer(s, token, index):
    active = s.get('quiz')
    if not available(s) or not active or token != active['token']: return False
    if type(index) is not int or not 0 <= index < len(active['order']): return False
    q = BY_ID[active['id']]
    selected = active['order'][index]
    correct = selected == q['correct']
    missing = max(0, LIMITS[active['item']] - s['inv'].get(active['item'], 0))
    reward = min(active['amount'], missing) if correct else 0
    if reward: s['inv'][active['item']] = s['inv'].get(active['item'], 0) + reward
    s['quiz_last_result'] = {'id': q['id'], 'prompt': q['prompt'],
                             'selected': q['answers'][selected], 'correct': correct,
                             'answer': q['answers'][q['correct']], 'explanation': q['explanation'],
                             'item': active['item'], 'amount': reward}
    s['quiz'] = None
    return True


def cancel(s):
    if not s.get('quiz') or not available(s): return False
    s['quiz'] = None
    return True
