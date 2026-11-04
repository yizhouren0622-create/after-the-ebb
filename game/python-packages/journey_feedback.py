"""Authored first-person responses and actual before/after action receipts."""

RESPONSES = {}  # Filled by storybook.install.

CRAFT_TEXT = {
    'shelter': '岑苇喊我松手，我才发现篷布已经拉紧了。进去试了试，风总算不往脸上灌了。',
    'shelter2': '我用膝盖顶住最后一块板，岑苇把接缝扣紧。她从里面推了两下，这回没晃。',
    'stove': '我把锅放上去试了试。岑苇掰正短的那只脚，说下回煮东西总不用拿手扶着了。',
    'cook': '锅盖刚一掀开，岑苇就伸勺子过来。我让她先别动，等我把热食分成四份。',
    'coats': '岑苇把袖口往里折了一圈，我照着她的样子也折了一下。手伸出来的时候，风没跟进来。',
    'trap': '我把笼口撑开，岑苇用手试了试，卡得住。住港口或街区时再把它放下去。',
    'knife': '我拿旧绳试刀，一下就割断了。岑苇找块厚布裹住刀口，叫我别再往裤兜里塞。',
    'receiver': '我转了一下旋钮，耳机里有了沙沙声。岑苇说先别拆，回中继站再试。',
    'sled': '我把两个包都堆上去，拖过一段烂泥。这回鞋陷进去了，包倒都还在原位。',
    'horn': '岑苇碰了一下电池接头，振膜抖了抖。我把接头用布隔开，等到了灯塔再接。',
    'bandage': '我把消过毒的布条晾凉，折好包起来。岑苇拿笔在外面写了个“药”。',
    'fuel': '我把干木劈开，挑里面没受潮的部分装成两包，顺手塞了一包到背包外袋。',
}

FLAG_NAMES = {'archive': '寂潮工程记录', 'counterphase': '双节律修正公式',
              'clinic_record': '灯塔避难室开门码', 'warning': '不要独自回应的警告',
              'tower_seen': '灯塔最终抉择已开放', 'live_signal': '实时校准频率',
              'helped': '为门后的幸存者留下口粮'}

FLAG_NAMES.update({'door_return': '门后幸存者的回赠', 'queue_names': '候诊名单', 'queue_stopped': '停止循环的取号机', 'red_terminal': '标出的异常端子', 'archive_box': '整理过的档案储物盒', 'terminal_fixed': '断开的异常端子', 'safe_crossing': '布条标记的海床捷径'})


def number(value):
    return str(int(value)) if value == int(value) else '%g' % value


def snapshot(s):
    return {'day': s['day'], 'ap': s['ap'], 'loc': s['loc'],
            'inv': dict(s['inv']), 'crew': [dict(p) for p in s['crew']],
            'bond': s['bond'], 'knowledge': s['knowledge'],
            'gear': list(s['gear']), 'flags': list(s['flags']),
            'unlocked': list(s['unlocked']), 'log_index': len(s['log'])}


def make_report(s, before, command, rules, source=None):
    kind = command[0]
    title, selected, cue = '', '', 'page'
    figures = False
    notes = []
    if kind == 'choose':
        title = source['title']
        selected = source['choices'][command[1]]['text']
        texts = RESPONSES.get(title)
        description = source['choices'][command[1]].get('narrative') or (texts[command[1]] if texts else '我拉好背包，岑苇已经在外面等我了。')
        figures = source['tag'] == '营火旁'
        cue = 'page' if figures or title == '海消失的早晨' else 'search'
        if title == '不是回声': cue = 'radio'
        if title == '帆布下的箱子': cue = 'craft'
        if title == '诊室的镜子' and command[1] == 0: cue = 'cloth'
        if title == '不是退潮': notes.append('档案馆还留有未读的资料，继续探索可找到中继站的路线。')
        if title == '仍在工作的接收器': notes.append('灯塔闸门在第 14 日开启；修好接收机后，可回中继站调频。')
        if title == '两行脚印': notes.append('前往灯塔需要海床拖橇，且须等到第 14 日闸门开启。')
    elif kind == 'quiz_answer':
        result = s['quiz_last_result']
        title = '知识补给 / 回答正确' if result['correct'] else '知识补给 / 再想一想'
        selected = result['selected']
        name = rules.ITEMS[result['item']]
        cue = 'search' if result['correct'] else 'page'
        if result['correct']:
            description = '这回答对了。我把领到的%s塞进背包，顺手在本子上把数量改了。' % name
        else:
            description = '我把答案又读了一遍，才看出自己漏了哪儿。这回没领到东西，还能换道题。'
        notes.extend(['题目：' + result['prompt'], '正确答案：' + result['answer'],
                      '解析：' + result['explanation'],
                      '答题不消耗行动或时间，也不改变剧情知识与羁绊；答错没有惩罚。'])
    elif kind == 'craft':
        title, selected = '制作完成', rules.RECIPES[command[1]][0]
        description = CRAFT_TEXT[command[1]]
        cue = 'fire' if command[1] == 'cook' else 'cloth' if command[1] in ['shelter', 'shelter2', 'coats', 'bandage'] else 'craft'
        notes.append(rules.RECIPES[command[1]][2])
    elif kind == 'travel':
        title, selected, cue = '转移营地', '前往' + rules.PLACES[s['loc']][0], 'footsteps'
        description = '到了%s，岑苇先把包放下，让我等等。她蹲下来，把鞋里的砂倒了个干净。' % rules.PLACES[s['loc']][0]
        if rules.has(s, 'safe_crossing') and (s['loc'] in ['flats', 'tower'] or before['loc'] in ['flats', 'tower']):
            notes.append('沿布条标记的路穿行：这次移动的基础体力消耗减少 2。')
    elif kind == 'use':
        name = s['crew'][command[2]]['name']
        title = '处理伤口' if command[1] == 'med' else '补充食物'
        selected = ('为%s使用一份药品' if command[1] == 'med' else '给%s一份口粮') % name
        figures = command[1] == 'med'
        cue = 'cloth' if figures else 'eat'
        if command[1] == 'med':
            if before['crew'][command[2]]['hurt']:
                description = ('我伸手让岑苇帮忙。纱布绕到第二圈时，她问是不是太紧。我摇头，让她再打一遍结。' if command[2] == 0 else '我让岑苇坐下，把伤口清理干净。她一直低头看我包，最后才说：“行了，衣服别压上去。”')
            else:
                description = ('我用完药，在原地坐了一会儿。岑苇把药盒拿过去，扣了两下才扣好。' if command[2] == 0 else '我把药递给岑苇，等她用完，再把空包装收进袋子。')
        else:
            description = ('我坐在包旁边吃完这份口粮。起身前把包装倒过来，拍掉粘在底上的碎渣。' if command[2] == 0 else '我把口粮递给岑苇。她说先放着，过一会儿又问我要了回去，坐下来吃完了。')
        notes.append('这次补给不消耗行动；状态最多恢复到 100，下方显示本次实际变化。')
    elif kind == 'rest':
        title, selected, cue = '稍作休息', '轮流守望，留在营地休息', 'rest'
        description = '我枕着背包躺了一会儿。换我守的时候，岑苇才脱下靴子，把湿袜子搭在膝上。'
    elif kind == 'night':
        title, selected, figures = '过夜', '分配晚餐并过夜', True
        cue = 'fire' if command[3] else 'rest'
        portions = {1: '吃了一份', .5: '吃了半份', 0: '没吃'}
        description = '晚饭我%s，岑苇%s。' % (portions[command[1]], portions[command[2]])
        description += ('我在背风处点了火，岑苇把湿袖口伸过去烤。' if command[3] else '今晚没点火，我俩把背包拉近了些，挡住脚边的风。')
        import storybook
        if not s['ending']:
            description += '\n\n' + storybook.night_text(s, before['day'])
        else:
            description += '后来谁也没说话，外面只剩下风声。'
        notes.append('当天剩余的 %s 行动在入夜后作废。' % before['ap'])
        if s['day'] != before['day']: notes.append('现在是第 %d 日：%s。%s' % (s['day'], rules.weather(s)[0], rules.weather(s)[1]))
        protection = sum(int(rules.gear(s, k)) for k in ['shelter', 'shelter2', 'coats']) + int(command[3])
        damage = max(0, rules.WEATHER[min(18, before['day'])][2] - protection) * (4 if s['difficulty'] == 'gentle' else 7)
        if damage: notes.append('保暖不足：两人各承受 %d 点失温伤害，已计入生命净变化。' % damage)
        if rules.gear(s, 'trap') and s['loc'] in ['shore', 'town']: notes.append('捕笼收获了 2 份生食，已收入行李。')
        if before['inv']['food'] - command[1] - command[2] > 16 and not rules.gear(s, 'shelter2'): notes.append('储藏不当损坏了 2 份口粮，已计入口粮消耗；加固营地可避免。')
        if any(p['hurt'] for p in before['crew']): notes.append('尚未处理的伤口在夜间使相应人物再失去 3 点生命。')
    elif kind == 'finish':
        title, selected, cue = '最后的选择', rules.ENDINGS[s['ending']][1], 'radio'
        description = '我拿手压住图纸，免得它从台子上滑下去。岑苇把围巾往上拉了拉，往旁边让出半步。'
    else:
        title, selected, cue = '没能继续走下去', '调查周围', 'footsteps'
        description = '我伸手去够地上的包，试了两次也没提起来。'

    groups = []
    def group(label, rows):
        if rows: groups.append({'title': label, 'rows': rows})
    def change(label, old, new):
        delta = new - old
        return '%s  %s → %s（%s%s）' % (label, number(old), number(new), '+' if delta > 0 else '', number(delta))

    group('物资变化', [change(name, before['inv'].get(k, 0), s['inv'].get(k, 0))
                         for k, name in rules.ITEMS.items() if before['inv'].get(k, 0) != s['inv'].get(k, 0)])
    if not groups: group('物资变化', ['本次没有获得或消耗物资。'])
    for i, p in enumerate(s['crew']):
        old = before['crew'][i]
        rows = [change(label, old[k], p[k]) for k, label in [('hp', '生命'), ('energy', '体力'), ('sanity', '精神')] if old[k] != p[k]]
        if old['hurt'] != p['hurt']: rows.append('受伤状态已解除。' if not p['hurt'] else '新增受伤状态。')
        group(p['name'], rows or ['生命、体力、精神均未改变。'])
    common = [change(label, before[k], s[k]) for k, label in [('bond', '羁绊'), ('knowledge', '知识')] if before[k] != s[k]]
    if kind == 'night':
        common.append('行动  %s → %s%s' % (before['ap'], s['ap'], '（新一天恢复）' if s['day'] != before['day'] else ''))
    elif before['ap'] != s['ap']: common.append(change('行动', before['ap'], s['ap']))
    group('旅途进展', common)
    group('新增装备', [rules.RECIPES[k][0] for k in s['gear'] if k not in before['gear']])
    group('新路线', [rules.PLACES[k][0] for k in s['unlocked'] if k not in before['unlocked']])
    group('记住的线索', [FLAG_NAMES.get(k, k) for k in s['flags'] if k not in before['flags']])
    report = {'title': title, 'selected': selected, 'description': description,
            'groups': groups, 'notes': notes, 'cue': cue, 'figures': figures,
            'day': before['day'], 'kind': kind}
    if kind == 'choose' and source:
        report['scene'] = {'title': source['title'], 'text': source['text'],
                           'tag': source['tag'], 'loc': before['loc'],
                           'choices': [c['text'] for c in source['choices']],
                           'index': command[1], 'result': description}
    if kind == 'quiz_answer':
        report['quiz_target'] = s['quiz_last_result']['item']
        report['quiz_correct'] = s['quiz_last_result']['correct']
    return report


def plain_text(report):
    lines = [report['selected'], report['description']]
    for section in report['groups']:
        lines.append(section['title'] + '：' + '；'.join(section['rows']))
    lines.extend(report['notes'])
    return '\n'.join(lines)
