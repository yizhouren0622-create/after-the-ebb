"""After the Ebb — deterministic, serializable survival simulation.

All campaign state lives in a plain dictionary. No network or external services.
"""

import journey_feedback as feedback
import knowledge_aid as aid
import achievements
import storybook

ITEMS = {
    'food': '口粮', 'raw': '生食', 'wood': '木料', 'scrap': '废金属',
    'cloth': '布料', 'fuel': '燃料', 'wire': '导线', 'med': '药品',
    'core': '接收核心', 'battery': '蓄电池',
}
PLACES = {
    'shore': ('搁浅港', '01 / THE STRANDED COAST', '滩涂留下了食物，也留下了不该出现的脚印。', 'shore', '生食 / 木料 / 布料'),
    'town': ('盐蚀街区', '02 / SALT QUARTER', '居民把门锁好，好像明天还会回来。', 'town', '口粮 / 金属 / 燃料'),
    'library': ('潮汐档案馆', '03 / TIDAL ARCHIVE', '潮位仪纹丝不动，桌上的铅笔却在滚。', 'archive', '知识 / 导线 / 旧记录'),
    'clinic': ('白窗诊所', '04 / THE WHITE WINDOWS', '取号机停在二十七号。第三把椅子上搭着蓝开衫。', 'clinic', '药品 / 布料 / 病历'),
    'relay': ('旧中继站', '05 / RELAY NINE', '话筒已经拔掉，电平表还在跳。', 'relay', '核心 / 电池 / 金属'),
    'flats': ('裸露海床', '06 / THE ABSENT SEA', '标桩歪进裂缝，两条铁轨通向远处的灯。', 'flats', '木料 / 生食 / 路线'),
    'tower': ('守潮灯塔', '07 / THE LAST FREQUENCY', '气象播报声在这里，比心跳还要清楚。', 'tower', '终点 / 潮汐装置'),
}
ORDER = list(PLACES)
RECIPES = {
    'shelter': ('搭起防风营地', {'wood': 3, 'cloth': 1}, '便携篷布随行。每夜额外恢复体力 8，抵挡部分寒冷。', 0),
    'shelter2': ('加固营地', {'wood': 3, 'scrap': 2, 'cloth': 2}, '每夜再恢复体力 6；配合寒衣可安稳度过风暴。需知识 4。', 4),
    'stove': ('制作折叠炉', {'scrap': 2, 'fuel': 1}, '解锁烹饪。2 生食 + 1 燃料 → 4 口粮。', 0),
    'cook': ('烹饪一锅热食', {'raw': 2, 'fuel': 1}, '得到 4 口粮，两人精神 +3。需要折叠炉。', 0),
    'coats': ('缝制两件寒衣', {'cloth': 3}, '永久减少探索与过夜的寒冷伤害。', 0),
    'trap': ('编制潮沟捕笼', {'wood': 2, 'wire': 1}, '在港口或街区过夜，每天稳定得到 2 生食。', 0),
    'knife': ('磨制工具刀', {'scrap': 2, 'wood': 1}, '打开密封货箱；降低部分探索事件的伤害。', 0),
    'receiver': ('修好便携接收机', {'core': 1, 'wire': 1, 'scrap': 2}, '解锁中继站的调频调查；每夜精神 +3。', 4),
    'sled': ('组装海床拖橇', {'wood': 3, 'scrap': 2, 'cloth': 1}, '进入灯塔的必要工具；移动体力消耗减半。', 0),
    'horn': ('组装逆相发声器', {'scrap': 3, 'wire': 2, 'battery': 1}, '在灯塔尝试中断寂潮。需要知识 8。', 8),
    'bandage': ('制作药品', {'cloth': 2, 'fuel': 1}, '消毒布条，得到 1 药品；治疗一人生命 +28、解除受伤。', 0),
    'fuel': ('拆解干木成燃料', {'wood': 2}, '得到 2 燃料。阴雨天也能点燃的细木屑。', 0),
}
EQUIPMENT = ['shelter', 'shelter2', 'stove', 'coats', 'trap', 'knife', 'receiver', 'sled', 'horn']
WEATHER = {
    1: ('薄雾', '能见度尚可。趁天气平稳，搜集并搭营。', 0),
    2: ('薄雾', '远处的灯塔每隔十秒闪烁一次。', 0),
    3: ('海风', '空气带盐。体力消耗略增。', 1),
    4: ('阴天', '旧广播预报：第 6、7 日有寒流。准备寒衣。', 0),
    5: ('寒流前夜', '明日起降温；布料能缝制寒衣。', 0),
    6: ('寒流', '无寒衣的户外行动会损失生命。', 2),
    7: ('寒流', '入夜更冷。寒衣、营地和生火都能保暖。', 2),
    8: ('晴隙', '难得的光线。适合远行。', 0),
    9: ('低云', '金属偶尔发出像牙齿打战的声音。', 0),
    10: ('低云', '预警：第 12、13 日盐暴，无法探索和移动。', 0),
    11: ('盐暴前夜', '明日起封路两日。储备口粮与燃料。', 1),
    12: ('盐暴', '禁止探索和移动；可留营制作、交谈、休息。', 3),
    13: ('盐暴', '风暴仍在继续。加固营地能大幅减少失温。', 3),
    14: ('风止', '风声消失了。不是风停了，是风没有了声音。', 1),
    15: ('白昼', '脚步声只剩下一半。灯塔依然在播报。', 1),
    16: ('失声', '鸟在张嘴。你听不见它。', 2),
    17: ('寂潮前夜', '最后两天。第 18 日入夜后，世界将彻底静止。', 2),
    18: ('最后的白昼', '日落之前，作出你们的决定。', 2),
}


def choice(text, effect=None, cost=None, need=None, result=''):
    return {'text': text, 'effect': effect or {}, 'cost': cost or {}, 'need': need or {}, 'result': result}

def event(title, text, choices, tag='探索事件'):
    return {'title': title, 'text': text, 'choices': choices, 'tag': tag}


DISCOVERIES = {('shore', 1): {'title': '海还在昨天',
                'text': '',
                'choices': [{'text': '带走航道图，搜集船边的物资',
                             'effect': {'items': {'raw': 3, 'wood': 2, 'cloth': 1}, 'unlock': ['town']},
                             'cost': {},
                             'need': {},
                             'result': '发现盐蚀街区。获得生食 3、木料 2、布料 1。'}],
                'tag': '探索事件'},
 ('shore', 2): {'title': '给明天留一半',
                'text': '',
                'choices': [{'text': '带走帆布和木撑',
                             'effect': {'items': {'cloth': 2, 'wood': 3}},
                             'cost': {},
                             'need': {},
                             'result': '寒衣与营地需要这些材料。'},
                            {'text': '带走罐头和固体燃料',
                             'effect': {'items': {'food': 3, 'fuel': 2}},
                             'cost': {},
                             'need': {},
                             'result': '今晚的饭，有着落了。'}],
                'tag': '探索事件'},
 ('town', 1): {'title': '锁门的人',
               'text': '',
               'choices': [{'text': '记录两个地址，清点物资',
                            'effect': {'unlock': ['library', 'clinic'],
                                       'items': {'food': 3, 'scrap': 2, 'fuel': 2}},
                            'cost': {},
                            'need': {},
                            'result': '发现潮汐档案馆、白窗诊所。获得口粮 3、废金属 2、燃料 2。'}],
               'tag': '探索事件'},
 ('library', 1): {'title': '不是退潮',
                  'text': '',
                  'choices': [{'text': '整理工程资料',
                               'effect': {'knowledge': 3, 'items': {'wire': 2, 'cloth': 1}, 'flags': ['archive']},
                               'cost': {},
                               'need': {},
                               'result': '知识 +3。得到导线 2、布料 1。再调查一次，可找到中继站路线。'}],
                  'tag': '探索事件'},
 ('library', 2): {'title': '静默协议 / 第九页',
                  'text': '',
                  'choices': [{'text': '带走修正公式与维护图',
                               'effect': {'knowledge': 3,
                                          'items': {'scrap': 2, 'wire': 1},
                                          'flags': ['counterphase'],
                                          'unlock': ['relay']},
                               'cost': {},
                               'need': {},
                               'result': '知识 +3。发现旧中继站。修正公式已记入手记。'}],
                  'tag': '探索事件'},
 ('clinic', 1): {'title': '一张没有签名的病历',
                 'text': '',
                 'choices': [{'text': '带走磁带、解锁码与医药',
                              'effect': {'items': {'med': 2, 'cloth': 2},
                                         'flags': ['clinic_record'],
                                         'bond': 6,
                                         'knowledge': 2},
                              'cost': {},
                              'need': {},
                              'result': '获得药品 2、布料 2。知识 +2，羁绊 +6。灯塔避难室的线索已记录。'}],
                 'tag': '探索事件'},
 ('relay', 1): {'title': '仍在工作的接收器',
                'text': '',
                'choices': [{'text': '拆取模块，记下标桩',
                             'effect': {'items': {'core': 1, 'battery': 1, 'scrap': 3, 'wire': 2},
                                        'unlock': ['flats']},
                             'cost': {},
                             'need': {},
                             'result': '获得接收核心 1、蓄电池 1、废金属 3、导线 2。发现裸露海床。'}],
                'tag': '探索事件'},
 ('flats', 1): {'title': '两行脚印',
                'text': '',
                'choices': [{'text': '沿着维护道标出灯塔位置',
                             'effect': {'unlock': ['tower'],
                                        'items': {'wood': 3, 'raw': 3},
                                        'bond': 5,
                                        'flags': ['warning']},
                             'cost': {},
                             'need': {},
                             'result': '发现守潮灯塔。需海床拖橇才能运送物资抵达。'}],
                'tag': '探索事件'},
 ('tower', 1): {'title': '明日天气',
                'text': '',
                'choices': [{'text': '先离开控制台，做好最后准备',
                             'effect': {'flags': ['tower_seen']},
                             'cost': {},
                             'need': {},
                             'result': '营地的“最终抉择”已开放。请先查看条件与物资。'}],
                'tag': '探索事件'}}

POOLS = {'shore': [{'title': '泥里的银光',
            'text': '',
            'choices': [{'text': '用衣角捞取',
                         'effect': {'items': {'raw': 4}, 'energy': -3},
                         'cost': {},
                         'need': {},
                         'result': '得到生食 4。'},
                        {'text': '安静地看一会儿',
                         'effect': {'sanity': 9, 'bond': 2, 'items': {'raw': 1}},
                         'cost': {},
                         'need': {},
                         'result': '两人精神 +9，羁绊 +2；带回生食 1。'}],
            'tag': '探索事件'},
           {'title': '帆布下的箱子',
            'text': '',
            'choices': [{'text': '用工具刀打开',
                         'effect': {'items': {'food': 3, 'fuel': 2}},
                         'cost': {},
                         'need': {'gear': 'knife'},
                         'result': '完好取出补给。'},
                        {'text': '垫布撬开',
                         'effect': {'items': {'food': 2, 'cloth': 1}, 'hp0': -7},
                         'cost': {},
                         'need': {},
                         'result': '我的手掌被划伤，生命 -7；得到补给。'},
                        {'text': '拆下外面的木板',
                         'effect': {'items': {'wood': 3, 'wire': 1}},
                         'cost': {},
                         'need': {},
                         'result': '收获制作材料。'}],
            'tag': '探索事件'},
           {'title': '尚有余温',
            'text': '',
            'choices': [{'text': '收集余下的燃料',
                         'effect': {'items': {'fuel': 3, 'wood': 1}},
                         'cost': {},
                         'need': {},
                         'result': '燃料 3、木料 1。'},
                        {'text': '把椅子留在原处，只拿毯子',
                         'effect': {'items': {'cloth': 3}, 'sanity': 3},
                         'cost': {},
                         'need': {},
                         'result': '布料 3，两人精神 +3。'}],
            'tag': '探索事件'}],
 'town': [{'title': '门后的咳嗽',
           'text': '',
           'choices': [{'text': '留下两份口粮',
                        'effect': {'items': {'scrap': 3, 'wire': 1}, 'bond': 7, 'flags': ['helped']},
                        'cost': {'food': 2},
                        'need': {},
                        'result': '门没有打开。我们离开时，咳嗽声轻了些。'},
                       {'text': '交换一卷布料',
                        'effect': {'items': {'food': 2, 'fuel': 1}},
                        'cost': {'cloth': 1},
                        'need': {},
                        'result': '公平的交换。'},
                       {'text': '轻轻把门带上',
                        'effect': {'items': {'wood': 2, 'fuel': 1}, 'sanity': -2},
                        'cost': {},
                        'need': {},
                        'result': '在隔壁找到材料。'}],
           'tag': '探索事件'},
          {'title': '停电的冷柜',
           'text': '',
           'choices': [{'text': '收集食品',
                        'effect': {'items': {'food': 3, 'raw': 2}},
                        'cost': {},
                        'need': {},
                        'result': '口粮 3、生食 2。'},
                       {'text': '拆解热水器',
                        'effect': {'items': {'scrap': 3, 'wire': 2, 'fuel': 1}},
                        'cost': {},
                        'need': {},
                        'result': '废金属 3、导线 2、燃料 1。'}],
           'tag': '探索事件'},
          {'title': '屋顶的晾衣绳',
           'text': '',
           'choices': [{'text': '取两件大衣，留住小的',
                        'effect': {'items': {'cloth': 3, 'wood': 1}, 'bond': 2},
                        'cost': {},
                        'need': {},
                        'result': '布料 3、木料 1。'},
                       {'text': '检查楼梯间的应急柜',
                        'effect': {'items': {'food': 2, 'med': 1}, 'energy': -4},
                        'cost': {},
                        'need': {},
                        'result': '口粮 2、药品 1；额外消耗体力 4。'}],
           'tag': '探索事件'}],
 'library': [{'title': '写给未出生的人',
              'text': '',
              'choices': [{'text': '抄下旁边的工程批注',
                           'effect': {'knowledge': 2, 'items': {'wire': 1, 'fuel': 1}, 'sanity': -2},
                           'cost': {},
                           'need': {},
                           'result': '知识 +2，导线 1、燃料 1。'},
                          {'text': '读完信的最后一页',
                           'effect': {'sanity': 10, 'bond': 3, 'items': {'food': 1}},
                           'cost': {},
                           'need': {},
                           'result': '书页里还夹着一块没拆封的饼干。'}],
              'tag': '探索事件'},
             {'title': '闭馆广播',
              'text': '',
              'choices': [{'text': '拔下扬声器，拆出线材',
                           'effect': {'items': {'wire': 3, 'scrap': 2}, 'sanity': -6},
                           'cost': {},
                           'need': {},
                           'result': '导线 3、废金属 2；两人精神 -6。'},
                          {'text': '在门外互相确认名字',
                           'effect': {'sanity': 7, 'bond': 3, 'knowledge': 1},
                           'cost': {},
                           'need': {},
                           'result': '我们还记得彼此的声音。'}],
              'tag': '探索事件'}],
 'clinic': [{'title': '储药柜',
             'text': '',
             'choices': [{'text': '带走药品和纱布',
                          'effect': {'items': {'med': 2, 'cloth': 2}},
                          'cost': {},
                          'need': {},
                          'result': '药品 2、布料 2。'},
                         {'text': '只拿糖和应急干粮',
                          'effect': {'items': {'food': 3}, 'sanity': 5},
                          'cost': {},
                          'need': {},
                          'result': '口粮 3，两人精神 +5。'}],
             'tag': '探索事件'},
            {'title': '诊室的镜子',
             'text': '',
             'choices': [{'text': '互相检查伤口',
                          'effect': {'hp': 12, 'sanity': -3, 'items': {'med': 1}},
                          'cost': {},
                          'need': {},
                          'result': '两人生命 +12，精神 -3，得到药品 1。'},
                         {'text': '拆下保温帘',
                          'effect': {'items': {'cloth': 3, 'scrap': 1}},
                          'cost': {},
                          'need': {},
                          'result': '布料 3、废金属 1。'}],
             'tag': '探索事件'}],
 'relay': [{'title': '备用机房',
            'text': '',
            'choices': [{'text': '拆走维护备件',
                         'effect': {'items': {'scrap': 4, 'wire': 2, 'fuel': 1}},
                         'cost': {},
                         'need': {},
                         'result': '废金属 4、导线 2、燃料 1。'},
                        {'text': '打开值守员的背包',
                         'effect': {'items': {'food': 3, 'battery': 1}, 'sanity': -3},
                         'cost': {},
                         'need': {},
                         'result': '口粮 3、蓄电池 1；两人精神 -3。'}],
            'tag': '探索事件'},
           {'title': '另一端的敲击',
            'text': '',
            'choices': [{'text': '不回应，整理绝缘材料',
                         'effect': {'items': {'cloth': 2, 'wire': 2, 'scrap': 2}},
                         'cost': {},
                         'need': {},
                         'result': '布料 2、导线 2、废金属 2。'},
                        {'text': '敲出不同的节拍',
                         'effect': {'knowledge': 2, 'sanity': -5, 'items': {'fuel': 2}},
                         'cost': {},
                         'need': {},
                         'result': '管道安静下来。知识 +2，精神 -5；找到燃料 2。'}],
            'tag': '探索事件'}],
 'flats': [{'title': '船骸里的花',
            'text': '',
            'choices': [{'text': '留下花，收集背风处的物资',
                         'effect': {'items': {'raw': 3, 'wood': 3}, 'sanity': 6},
                         'cost': {},
                         'need': {},
                         'result': '生食 3、木料 3；两人精神 +6。'},
                        {'text': '画下它的样子',
                         'effect': {'sanity': 13, 'bond': 4, 'items': {'raw': 1}},
                         'cost': {},
                         'need': {},
                         'result': '两人精神 +13，羁绊 +4；得到生食 1。'}],
            'tag': '探索事件'},
           {'title': '旧航线',
            'text': '',
            'choices': [{'text': '拆取边缘的木料',
                         'effect': {'items': {'wood': 4, 'fuel': 2}},
                         'cost': {},
                         'need': {},
                         'result': '木料 4、燃料 2。'},
                        {'text': '搜查搁浅的补给艇',
                         'effect': {'items': {'food': 3, 'scrap': 2}, 'energy': -4},
                         'cost': {},
                         'need': {},
                         'result': '口粮 3、废金属 2；额外消耗体力 4。'}],
            'tag': '探索事件'}],
 'tower': [{'title': '值守员的厨房',
            'text': '',
            'choices': [{'text': '清点最后的补给',
                         'effect': {'items': {'food': 4, 'fuel': 3}},
                         'cost': {},
                         'need': {},
                         'result': '口粮 4、燃料 3。'},
                        {'text': '检查仪表与备用线材',
                         'effect': {'items': {'wire': 3, 'scrap': 3}, 'knowledge': 1},
                         'cost': {},
                         'need': {},
                         'result': '导线 3、废金属 3，知识 +1。'}],
            'tag': '探索事件'},
           {'title': '塔顶的风',
            'text': '',
            'choices': [{'text': '并肩坐一会儿',
                         'effect': {'sanity': 12, 'bond': 5},
                         'cost': {},
                         'need': {},
                         'result': '两人精神 +12，羁绊 +5。'},
                        {'text': '继续校验设备',
                         'effect': {'knowledge': 2, 'items': {'scrap': 2, 'fuel': 1}},
                         'cost': {},
                         'need': {},
                         'result': '知识 +2，废金属 2、燃料 1。'}],
            'tag': '探索事件'}]}

TALKS = []
ENDINGS = {'tomorrow': ('01', '没有天气预报的明天', ''),
 'shelter': ('02', '把灯留着', ''),
 'voice': ('03', '替世界守夜的人', ''),
 'silent': ('04', '无人应答', ''),
 'lost': ('05', '走不到的海岸', ''),
 'drift': ('06', '忘记名字之前', '')}


storybook.install(__import__(__name__))


def new_game(loadout='tools', difficulty='standard', seed=27419):
    inv = dict.fromkeys(ITEMS, 0)
    inv.update(food=6, wood=1, cloth=1, fuel=2)
    if loadout == 'tools': inv.update(scrap=3, wire=1, wood=3)
    if loadout == 'rations': inv.update(food=11, med=1, raw=2)
    if loadout == 'keepsake': inv.update(food=7, cloth=3, wire=2)
    if difficulty == 'gentle': inv['food'] += 4
    s = {'day': 1, 'ap': 3, 'loc': 'shore', 'inv': inv, 'gear': [],
         'crew': [{'name': '梁弦', 'role': '录音师 / 27', 'hp': 90, 'energy': 85, 'sanity': 78, 'hurt': False},
                  {'name': '岑苇', 'role': '轮机工 / 26', 'hp': 88, 'energy': 83, 'sanity': 80, 'hurt': False}],
         'knowledge': 0, 'bond': 48 if loadout != 'keepsake' else 60,
         'unlocked': ['shore'], 'visits': {}, 'pool': {}, 'flags': [], 'log': [],
         'memories': [], 'ending': None, 'difficulty': difficulty, 'seed': seed,
         'pending': None, 'talk_day': 0, 'talks': 0, 'scan': False,
         'last_result': '第 6、7 日寒流；第 12、13 日盐暴。第 18 日日落前抵达灯塔。',
         'tab': 'explore', 'night_count': 0, 'tutorial': 0,
         'feedback': None, 'last_feedback': None, 'action_origin': None,
         'quiz': None, 'quiz_seen': [], 'quiz_seq': 0, 'quiz_last_result': None,
         'quiz_seed': seed ^ 0xA17D53, 'story_seen': [], 'loadout': loadout}
    log(s, '出发', '海退去了。你们决定一起找到那座仍在报时的灯塔。')
    achievements.update(s)
    return s

def rng(s, n):
    s['seed'] = (1664525 * s['seed'] + 1013904223) % (2**32)
    return s['seed'] % n

def log(s, title, text):
    s['log'].append({'day': s['day'], 'title': title, 'text': text})

def weather(s): return WEATHER[min(18, s['day'])]
def amt(s, k): return s['inv'].get(k, 0)
def gear(s, k): return k in s['gear']
def has(s, k): return k in s['flags']
def clamp(n): return max(0, min(100, n))

def adjust(s, field, value, target=None):
    for i, p in enumerate(s['crew']):
        if target is None or i == target:
            p[field] = clamp(p[field] + value)

def resolve_health(s):
    if any(p['hp'] <= 0 for p in s['crew']): s['ending'] = 'lost'
    elif any(p['sanity'] <= 0 for p in s['crew']): s['ending'] = 'drift'

def apply(s, fx):
    for k, v in fx.get('items', {}).items(): s['inv'][k] = max(0, amt(s, k) + v)
    for field in ['hp', 'energy', 'sanity']:
        if field in fx: adjust(s, field, fx[field])
        for i in range(2):
            if field + str(i) in fx: adjust(s, field, fx[field + str(i)], i)
    s['knowledge'] += fx.get('knowledge', 0)
    s['bond'] = clamp(s['bond'] + fx.get('bond', 0))
    for key in fx.get('flags', []):
        if key not in s['flags']: s['flags'].append(key)
    for key in fx.get('unlock', []):
        if key not in s['unlocked']: s['unlocked'].append(key)
    resolve_health(s)

def costs_text(cost):
    return '  '.join(ITEMS[k] + ' ' + str(v) for k, v in cost.items())


def night_preview(s, ration0=1, ration1=1, fire=False):
    """Use the real night rules on a copy, including injuries and weather."""
    import copy
    q = copy.deepcopy(s)
    if not night(q, ration0, ration1, fire): return None
    return {'crew': q['crew'], 'ending': q['ending'], 'day': q['day']}


def region_progress(s):
    loc = s['loc']
    main = sum(1 for key in DISCOVERIES if key[0] == loc)
    done = min(main, s['visits'].get(loc, 0))
    return '关键调查 %d / %d' % (done, main)


def recommendation(s):
    if s['inv']['food'] < 2: return '今晚口粮不足 2 份。先找食物，或用折叠炉烹饪。'
    if any(p['hp'] < 30 for p in s['crew']): return '有人生命偏低。人物卡下的治疗不消耗行动。'
    if any(p['energy'] < 15 for p in s['crew']): return '体力接近耗尽。先去营地休息，或进食再出发。'
    if s['ap'] == 0: return '今天的行动已用完。点右上角过夜，预览分餐后的状态。'
    return objective(s)

def can_choice(s, c):
    for k, v in c['cost'].items():
        if amt(s, k) < v: return False
    if c['need'].get('gear') and not gear(s, c['need']['gear']): return False
    return True

def choice_hint(c):
    t = costs_text(c['cost'])
    if c['need'].get('gear'): t += '  需' + RECIPES[c['need']['gear']][0].replace('制作', '').replace('磨制', '')
    return t

def choose(s, index):
    e = s.get('pending')
    if not e or not 0 <= index < len(e['choices']): return False
    c = e['choices'][index]
    if not can_choice(s, c): return False
    apply(s, {'items': {k: -v for k, v in c['cost'].items()}})
    apply(s, c['effect'])
    s['last_result'] = c['result']
    log(s, e['title'], c['text'] + '。' + c['result'])
    s['memories'].append({'title': e['title'], 'text': e['text']})
    s['pending'] = None
    return True

def outdoor_reason(s):
    if s['ap'] < 1: return '今天的行动已用尽，请安排晚餐与过夜。'
    if s['day'] in [12, 13]: return '盐暴封路。今天请留营制作、交谈或休息。'
    return ''

def spend(s, cost=10, outside=False):
    s['ap'] -= 1
    for p in s['crew']:
        drain = cost + (2 if p['hurt'] else 0)
        if p['energy'] < drain: p['hp'] = clamp(p['hp'] - 7)
        p['energy'] = clamp(p['energy'] - drain)
    if outside:
        w = weather(s)[2]
        if w >= 2 and not gear(s, 'coats'): adjust(s, 'hp', -5 if s['difficulty'] == 'gentle' else -8)
        adjust(s, 'sanity', -1 if s['difficulty'] == 'gentle' else -2)
    resolve_health(s)

def explore(s):
    if outdoor_reason(s): return False
    spend(s, 10 + weather(s)[2], True)
    if s['ending']: return True
    loc = s['loc']; n = s['visits'].get(loc, 0) + 1
    s['visits'][loc] = n
    if (loc, n) in DISCOVERIES: s['pending'] = DISCOVERIES[(loc, n)]
    elif (thread := storybook.next_thread(s, __import__(__name__))):
        s['pending'] = thread
    else:
        pool = POOLS[loc]
        used = s['pool'].get(loc, [])
        if len(used) >= len(pool): used = []
        options = [i for i in range(len(pool)) if i not in used]
        idx = options[rng(s, len(options))]
        s['pool'][loc] = used + [idx]
        s['pending'] = pool[idx]
    return True

def travel_reason(s, loc):
    if loc not in s['unlocked']: return '尚未发现。继续探索已知区域。'
    if loc == s['loc']: return '目前就在这里。'
    if outdoor_reason(s): return outdoor_reason(s)
    if loc == 'tower' and not gear(s, 'sled'): return '需要组装海床拖橇，以运送补给穿过裂隙。'
    if loc == 'tower' and s['day'] < 14: return '维护闸门于第 14 日开启。先准备补给，度过盐暴。'
    return ''

def travel(s, loc):
    if travel_reason(s, loc): return False
    cost = 4 if gear(s, 'sled') else 8
    if has(s, 'safe_crossing') and (loc in ['flats', 'tower'] or s['loc'] in ['flats', 'tower']):
        cost = max(2, cost - 2)
    spend(s, cost, True)
    s['loc'] = loc
    s['tab'] = 'explore'
    s['last_result'] = '抵达' + PLACES[loc][0] + '。便携营地已经安置。'
    log(s, '转移营地', s['last_result'])
    return True

def recipe_reason(s, key):
    name, cost, desc, knowledge = RECIPES[key]
    if key in EQUIPMENT and gear(s, key): return '已完成'
    if s['ap'] < 1: return '今日行动已用尽'
    if s['knowledge'] < knowledge: return '需要知识 ' + str(knowledge)
    if key == 'shelter2' and not gear(s, 'shelter'): return '先搭起防风营地'
    if key == 'cook' and not gear(s, 'stove'): return '需要折叠炉'
    missing = [ITEMS[k] + '缺' + str(v - amt(s, k)) for k, v in cost.items() if amt(s, k) < v]
    return ' / '.join(missing)

def craft(s, key):
    if key not in RECIPES or recipe_reason(s, key): return False
    name, cost, _, _ = RECIPES[key]
    spend(s, 3)
    apply(s, {'items': {k: -v for k, v in cost.items()}})
    if key in EQUIPMENT: s['gear'].append(key)
    if key == 'cook': apply(s, {'items': {'food': 4}, 'sanity': 3})
    if key == 'bandage': apply(s, {'items': {'med': 1}})
    if key == 'fuel': apply(s, {'items': {'fuel': 2}})
    s['last_result'] = name + '完成。消耗 1 行动。'
    log(s, '制作', name + '。使用：' + costs_text(cost))
    return True

def use_item(s, item, target):
    if item not in ['food', 'med'] or amt(s, item) < 1 or target not in [0, 1]: return False
    p = s['crew'][target]
    s['inv'][item] -= 1
    if item == 'food':
        p['energy'] = clamp(p['energy'] + 18); p['hp'] = clamp(p['hp'] + 8)
        p['sanity'] = clamp(p['sanity'] + 3)
        result = '体力 +18，生命 +8，精神 +3。'
    else:
        p['hp'] = clamp(p['hp'] + 28); p['hurt'] = False
        result = '生命 +28，解除受伤。'
    s['last_result'] = p['name'] + '使用了' + ITEMS[item] + '，' + result
    log(s, '补给', s['last_result'])
    return True

def rest(s):
    if s['ap'] < 1: return False
    s['ap'] -= 1
    adjust(s, 'energy', 20 + (5 if gear(s, 'shelter') else 0)); adjust(s, 'sanity', 4)
    s['last_result'] = '轮流守望，稍作休息。两人体力 +%d，精神 +4。' % (25 if gear(s, 'shelter') else 20)
    log(s, '休息', s['last_result']); return True

def talk(s):
    if s['ap'] < 1 or s['talk_day'] == s['day']: return False
    s['ap'] -= 1; s['talk_day'] = s['day']
    title, text = TALKS[s['talks'] % len(TALKS)]
    s['talks'] += 1
    s['pending'] = event(title, text, [choice('把这件小事记下来', {'sanity': 12, 'bond': 7}, result='两人精神 +12，羁绊 +7。')], '营火旁')
    return True

def scan_reason(s):
    if s['loc'] != 'relay': return '需要在旧中继站调频'
    if not gear(s, 'receiver'): return '先修好便携接收机'
    if s['scan']: return '已完成调频'
    return outdoor_reason(s)

def scan(s):
    if scan_reason(s): return False
    spend(s, 4); s['scan'] = True
    s['pending'] = event('不是回声', storybook.TEXT['不是回声'][1], [choice('抄下双人校准频率', {'flags': ['live_signal'], 'knowledge': 2, 'bond': 5, 'sanity': 6}, result='记录实时频率。知识 +2，羁绊 +5，两人精神 +6。')], '主线 / 实时信号')
    s['pending']['text'] = storybook.TEXT['不是回声'][1]
    return True

def night(s, ration0=1, ration1=1, fire=False):
    if s['pending'] or s['ending']: return False
    if ration0 not in [0, .5, 1] or ration1 not in [0, .5, 1]: return False
    if amt(s, 'food') < ration0 + ration1: return False
    if fire and amt(s, 'fuel') < 1: return False
    s['inv']['food'] -= ration0 + ration1
    if fire: s['inv']['fuel'] -= 1
    cold = weather(s)[2]
    protection = (1 if gear(s, 'shelter') else 0) + (1 if gear(s, 'shelter2') else 0) + (1 if gear(s, 'coats') else 0) + (1 if fire else 0)
    damage = max(0, cold - protection) * (4 if s['difficulty'] == 'gentle' else 7)
    notes = []
    for i, ration in enumerate([ration0, ration1]):
        p = s['crew'][i]
        if ration == 1:
            p['hp'] = clamp(p['hp'] + 5); p['energy'] = clamp(p['energy'] + 26)
            p['sanity'] = clamp(p['sanity'] + 4)
        elif ration == .5:
            p['energy'] = clamp(p['energy'] + 14); p['hp'] = clamp(p['hp'] - 3)
        else:
            p['hp'] = clamp(p['hp'] - (9 if s['difficulty'] == 'gentle' else 14))
            p['energy'] = clamp(p['energy'] + 3); p['sanity'] = clamp(p['sanity'] - 9)
        p['energy'] = clamp(p['energy'] + (8 if gear(s, 'shelter') else 0) + (6 if gear(s, 'shelter2') else 0))
        p['hp'] = clamp(p['hp'] - damage - (3 if p['hurt'] else 0))
        p['sanity'] = clamp(p['sanity'] + (5 if fire else 0) + (3 if gear(s, 'receiver') else 0) - (2 if s['day'] >= 14 else 0))
    notes.append('梁弦 %.1f / 岑苇 %.1f 口粮。' % (ration0, ration1))
    if damage: notes.append('保暖不足，两人各失去生命 %d。' % damage)
    if fire: notes.append('生火使两人精神 +5。')
    if gear(s, 'trap') and s['loc'] in ['shore', 'town']:
        s['inv']['raw'] += 2; notes.append('捕笼收获生食 2。')
    if amt(s, 'food') > 16 and not gear(s, 'shelter2'):
        s['inv']['food'] -= 2; notes.append('储藏不当，口粮损坏 2。加固营地可避免。')
    if ration0 != ration1: s['bond'] = clamp(s['bond'] - 2)
    else: s['bond'] = clamp(s['bond'] + 1)
    log(s, '夜间结算', ' '.join(notes))
    s['last_result'] = ' '.join(notes)
    s['night_count'] += 1
    resolve_health(s)
    if s['day'] >= 18 and not s['ending']: s['ending'] = 'silent'
    if not s['ending']:
        s['day'] += 1; s['ap'] = 3
        log(s, '清晨 / ' + weather(s)[0], weather(s)[1])
    return True

def true_requirements(s):
    return [('逆相发声器', gear(s, 'horn')),
            ('档案馆修正公式', has(s, 'counterphase')),
            ('中继站实时频率', has(s, 'live_signal')),
            ('羁绊达到 55', s['bond'] >= 55),
            ('两人生命均不低于 25', all(p['hp'] >= 25 for p in s['crew'])),
            ('两人精神均不低于 30', all(p['sanity'] >= 30 for p in s['crew']))]


def ending_text(s, key):
    field = 'hp' if key == 'lost' else 'sanity'
    if key in storybook.PARTNER_ENDINGS and s['crew'][1][field] <= 0 < s['crew'][0][field]:
        return storybook.PARTNER_ENDINGS[key][1]
    return ENDINGS[key][2]

def finish(s, key):
    if s['loc'] != 'tower' or not has(s, 'tower_seen') or s['ending']: return False
    if key == 'tomorrow' and not all(ok for _, ok in true_requirements(s)): return False
    if key == 'shelter' and (not has(s, 'clinic_record') or amt(s, 'food') < 4 or amt(s, 'fuel') < 2): return False
    if key == 'voice' and s['bond'] < 35: return False
    if key not in ['tomorrow', 'shelter', 'voice']: return False
    s['ending'] = key; log(s, '最后的选择', ENDINGS[key][1]); return True

def objective(s):
    if not s['visits'].get('shore'): return '探索搁浅港，找到通往城镇的路线。'
    if 'town' not in s['visits']: return '在“路线”中前往盐蚀街区，调查废墟。'
    if not has(s, 'counterphase'): return '探索潮汐档案馆两次，找出寂潮的原理与路线。'
    if not has(s, 'clinic_record'): return '白窗诊所藏着磁带与避难室线索。'
    if not s['visits'].get('relay'): return '前往旧中继站，寻找接收模块与海床路线。'
    if not gear(s, 'receiver'): return '制作便携接收机，回中继站进行调频调查。'
    if not has(s, 'live_signal'): return '在旧中继站选择“调频调查”，寻找实时信号。'
    if not s['visits'].get('flats'): return '前往裸露海床，探索通往灯塔的维护道。'
    if not gear(s, 'sled'): return '制作海床拖橇，才能运送物资进入灯塔。'
    if not has(s, 'tower_seen'): return '抵达守潮灯塔，并调查控制室。'
    if not gear(s, 'horn'): return '准备逆相发声器，照顾好彼此，然后作出最终抉择。'
    return '灯塔已就绪。确认条件，在营地作出最终抉择。'

def tutorial_progress(s, command):
    step = s.get('tutorial', 7)
    if step >= 7: return
    if s['day'] >= 2 and step < 6:
        s['tutorial'] = 6
        return
    if step == 0 and s['visits'].get('shore', 0) >= 1 and not s['pending']:
        s['tutorial'] = 1
    elif step == 2 and gear(s, 'shelter'):
        s['tutorial'] = 3
    elif step == 3 and command[:2] == ('use', 'food'):
        s['tutorial'] = 4
    elif step == 4 and command[0] == 'choose' and s['talk_day'] == s['day']:
        s['tutorial'] = 5
    elif step == 6 and command[0] == 'travel' and s['loc'] == 'town':
        s['tutorial'] = 7
        s['last_result'] = '教学完成。每个新区域都值得调查；留够晚餐，留意天气。'

def _dispatch_action(s, command):
    if s['ending']: return False
    kind = command[0]
    if kind == 'quiz_answer': return len(command) == 3 and aid.answer(s, command[1], command[2])
    if kind == 'quiz_cancel': return aid.cancel(s)
    if s.get('quiz'): return False
    if kind == 'choose': return choose(s, command[1])
    if s['pending']: return False
    if kind == 'quiz_start': return len(command) == 2 and aid.start(s, command[1])
    if kind == 'explore': return explore(s)
    if kind == 'travel': return travel(s, command[1])
    if kind == 'craft': return craft(s, command[1])
    if kind == 'rest': return rest(s)
    if kind == 'talk': return talk(s)
    if kind == 'scan': return scan(s)
    if kind == 'use': return use_item(s, command[1], command[2])
    if kind == 'night': return night(s, *command[1:])
    if kind == 'finish': return finish(s, command[1])
    return False


def dispatch(s, command):
    """Apply once, then persist a receipt computed from actual state changes.

    Exploring/starting a conversation defers its receipt until the player picks
    an option. Its original AP/weather/energy costs belong to that same receipt.
    """
    before = feedback.snapshot(s)
    source = s.get('pending') if command[0] == 'choose' else None
    if not _dispatch_action(s, command): return False
    newly = achievements.update(s, command, before, source)
    if command[0] in ['quiz_start', 'quiz_cancel']: return True
    if command[0] in ['explore', 'talk', 'scan'] and s.get('pending'):
        s['action_origin'] = before
        s['feedback'] = None
        return True
    if command[0] == 'choose':
        before = s.get('action_origin') or before
    report = feedback.make_report(s, before, command, __import__(__name__), source)
    if newly:
        report['groups'].append({'title': '本次旅途达成的成就',
                                'rows': [achievements.BY_ID[key][1] for key in newly]})
    s['feedback'] = report
    s['last_feedback'] = report
    s['action_origin'] = None
    s['last_result'] = report['selected'] + '。完整经过与实际变化已记入手记。'
    text = feedback.plain_text(report)
    index = before['log_index']
    if index < len(s['log']):
        s['log'][index]['text'] = text
    else:
        log(s, report['title'], text)
    return True


def acknowledge_feedback(s):
    """UI dismissal changes no supplies, time, or character statistics."""
    s['feedback'] = None


def upgrade_state(s):
    """Keep released journeys usable; initialize only missing fields."""
    for key in ['feedback', 'last_feedback', 'action_origin', 'quiz', 'quiz_last_result']:
        s.setdefault(key, None)
    s.setdefault('quiz_seen', [])
    s.setdefault('quiz_seq', 0)
    s.setdefault('quiz_seed', s['seed'] ^ 0xA17D53)
    s.setdefault('story_seen', [])
    s.setdefault('loadout', 'tools')
    achievements.update(s)
