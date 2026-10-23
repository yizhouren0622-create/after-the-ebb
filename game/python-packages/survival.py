"""After the Ebb — deterministic, serializable survival simulation.

All campaign state lives in a plain dictionary. No network or external services.
"""

ITEMS = {
    'food': '口粮', 'raw': '生食', 'wood': '木料', 'scrap': '废金属',
    'cloth': '布料', 'fuel': '燃料', 'wire': '导线', 'med': '药品',
    'core': '接收核心', 'battery': '蓄电池',
}
PLACES = {
    'shore': ('搁浅港', '01 / THE STRANDED COAST', '滩涂留下了食物，也留下了不该出现的脚印。', 'shore', '生食 / 木料 / 布料'),
    'town': ('盐蚀街区', '02 / SALT QUARTER', '居民把门锁好，好像明天还会回来。', 'town', '口粮 / 金属 / 燃料'),
    'library': ('潮汐档案馆', '03 / TIDAL ARCHIVE', '所有潮汐表，都停在了同一天。', 'town', '知识 / 导线 / 旧记录'),
    'clinic': ('白窗诊所', '04 / THE WHITE WINDOWS', '病床上的耳机，仍朝向空无一人的枕头。', 'town', '药品 / 布料 / 病历'),
    'relay': ('旧中继站', '05 / RELAY NINE', '信号不是来自海上。它从海底传来。', 'tower', '核心 / 电池 / 金属'),
    'flats': ('裸露海床', '06 / THE ABSENT SEA', '那条航线，如今可以步行通过。', 'shore', '木料 / 生食 / 路线'),
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
                'text': '我和岑苇沿着倾斜的舷梯爬下渡轮，脚下的淤泥立刻没过了鞋底。海岸上还留着昨夜的漂流物，远处却连一线水光都看不见。我试着回想船搁浅时的震动，脑子里只有一阵刺耳的杂音。\n'
                        '\n'
                        '岑苇从船边捡起一张旧航道图，摊在膝盖上给我看。图上标出的港口街区离这里不远，那里或许还有吃的，也可能找到愿意告诉我们发生了什么的人。她把图折好，低声催我先离开船底：“这艘船撑不了多久。海会不会回来，等我们有东西吃了再想。”',
                'choices': [{'text': '带走航道图，搜集船边的物资',
                             'effect': {'items': {'raw': 3, 'wood': 2, 'cloth': 1}, 'unlock': ['town']},
                             'cost': {},
                             'need': {},
                             'result': '发现盐蚀街区。获得生食 3、木料 2、布料 1。'}],
                'tag': '探索事件'},
 ('shore', 2): {'title': '给明天留一半',
                'text': '救生箱被压在断裂的船腹下面，我和岑苇轮流搬开碎木，才把箱盖露出来。上面用蜡笔写着“给下一个人”，字迹被海水泡得发散，依旧看得出写字的人很用力。\n'
                        '\n'
                        '箱里既有密封罐头，也有卷好的帆布和几根木撑。我们没有力气把整箱东西带走，只能取走一部分。我摸了摸空下来的胃，又看了一眼渐渐阴下来的天色，一时拿不定主意。眼前这顿饭和今晚挡风的地方，我们都缺。',
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
               'text': '杂货铺的卷帘门已经锈死，我和岑苇从后窗钻进去，在货架底层找到几包没拆封的食品。柜台边散着一摞就诊通知，其中一张背面还夹着档案馆的借阅凭条。两个地址都在步行能到的范围内。\n'
                       '\n'
                       '岑苇看着诊所的名字，告诉我她以前常去那里替母亲取助听器。她说这话时一直攥着那张通知，过了好一会儿才把它递给我。我没有追问她母亲在哪里，只把两个地址都标在地图上，再陪她清点能带走的东西。',
               'choices': [{'text': '记录两个地址，清点物资',
                            'effect': {'unlock': ['library', 'clinic'],
                                       'items': {'food': 3, 'scrap': 2, 'fuel': 2}},
                            'cost': {},
                            'need': {},
                            'result': '发现潮汐档案馆、白窗诊所。获得口粮 3、废金属 2、燃料 2。'}],
               'tag': '探索事件'},
 ('library', 1): {'title': '不是退潮',
                  'text': '档案馆地下室积着一层发白的泥，我蹲在倾倒的柜子旁，把黏在一起的工程资料慢慢揭开。同一天的潮汐表竟然有十七个版本：最早还在计算海面高度，最后几份记录的却是声音和热量的变化。\n'
                          '\n'
                          '岑苇替我扶着手电，我在一页被反复修改的报告上读到“振动回收”四个字。有人用红笔写下警告：海水并没有流向别处，系统正在消除让它运动的条件。如果记录是真的，接下来消失的就不会只有海浪。我抄下能看懂的部分，决定继续找那份报告的后页。',
                  'choices': [{'text': '整理工程资料',
                               'effect': {'knowledge': 3,
                                          'items': {'wire': 2, 'cloth': 1},
                                          'flags': ['archive']},
                               'cost': {},
                               'need': {},
                               'result': '知识 +3。得到导线 2、布料 1。再调查一次，可找到中继站路线。'}],
                  'tag': '探索事件'},
 ('library', 2): {'title': '静默协议 / 第九页',
                  'text': '我在一本装订错页的维护手册里找到了报告的后半部分。工程原本想把海浪的能量储存起来，可设备失控后，开始把声音、热量，甚至活人的心跳都当作能够回收的东西。记录里把这场不断扩大的灾难叫作“寂潮”。\n'
                          '\n'
                          '一名工程师在图纸背面留下了停止设备的方法：让两个互不相同、又始终保持稳定的节律进入控制系统，打破它的同步过程。只有一个人操作，会被系统留下，成为新的信号源。我看完后把纸递给岑苇，等她读完，才翻开标着中继站位置的维护图。',
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
                 'text': '诊所的药柜几乎空了，我在最下面的抽屉里找到几卷纱布，还有一份没签名的病历。病人声称自己听见了第二天的广播，诊疗记录却把这当成了集体幻听。我越往下读，越觉得那些记录是在掩盖什么。\n'
                         '\n'
                         '岑苇突然叫我过去。她在值班室找到母亲留下的磁带，里面夹着灯塔机械避难室的开门码。她把磁带翻来覆去看了很久，才小心地放进内袋。我问要不要想办法听一听，她摇摇头：“先找台能用的机器吧。到时候你陪我听。”',
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
                'text': '中继站比地图上画的破败得多，整面外墙都被盐霜覆盖，里面却还有设备通着电。我推门进去时，扩音器正好响起那句已经听熟的天气预报，和渡轮上的语气、停顿完全一样。\n'
                        '\n'
                        '岑苇检查了配电柜，拆下能用的接收模块和备用电池。我在值班桌上找到通往海床的标桩图，以及一张维护通知：灯塔闸门会在第十四天、盐暴结束后自动开启。我们还得在外面熬过几天。离开前，岑苇指了指断掉的调频旋钮，建议先修好便携接收机，再回来试着接收别的频率。',
                'choices': [{'text': '拆取模块，记下标桩',
                             'effect': {'items': {'core': 1, 'battery': 1, 'scrap': 3, 'wire': 2},
                                        'unlock': ['flats']},
                             'cost': {},
                             'need': {},
                             'result': '获得接收核心 1、蓄电池 1、废金属 3、导线 2。发现裸露海床。'}],
                'tag': '探索事件'},
 ('flats', 1): {'title': '两行脚印',
                'text': '我沿着标桩走到海床深处，终于看见一条半埋在盐里的维护道。旧轨道虽然断了几处，仍能通向灯塔所在的高地，只要做出一架拖橇，我们就能把补给一起运过去。\n'
                        '\n'
                        '路旁有一张被盐壳封住的照片，拍的是两名值守员。背面有人写着：设备会模仿你最想念的人，不要一个人回答它。我刚读完，风里就传来了一个女人叫岑苇的声音。她的脸一下子白了，却抓住我的手腕，直到那声音远去才松开。我没有问她听见了谁，只把照片和路线一并收好。',
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
                'text': '我和岑苇爬上最后一段铁梯，终于走进了灯塔控制室。这里没有播音员，井口上方悬着一层巨大的金属振膜。那些失踪者的声音从里面不断传出来，时而重叠，时而只剩一句天气预报。\n'
                        '\n'
                        '控制台上有两个触点，屏幕随着我们的靠近，显示出一快一慢的两条心跳曲线。我想起档案馆那份修正公式，手心开始出汗。岑苇把围巾缠在冰冷的扶手上，问我准备好了没有。我告诉她先别急，我们还有时间把设备和补给检查一遍；一旦作出选择，恐怕就没有退回来的机会了。',
                'choices': [{'text': '先离开控制台，做好最后准备',
                             'effect': {'flags': ['tower_seen']},
                             'cost': {},
                             'need': {},
                             'result': '营地的“最终抉择”已开放。请先查看条件与物资。'}],
                'tag': '探索事件'}}


POOLS = {'shore': [{'title': '泥里的银光',
            'text': '我绕过船尾时，发现一处还没干透的水洼。几条小鱼挤在浅水里，尾巴拍起的泥点落在我的鞋面上。我蹲下来试了试水温，冷得手指发疼，但这些鱼至少还能吃。\n'
                    '\n'
                    '岑苇站在旁边替我挡风。她看了一会儿水面，忽然说以前总嫌码头的鱼腥味太重。我知道她其实想说什么，却没有接话。我们可以趁现在多捞一点，也可以在这里坐一会儿，等那阵一直催着人赶路的心慌稍微缓下来。',
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
            'text': '一块烂帆布下面盖着几只没有开封的货箱。我用力扳了扳卡扣，金属边缘立刻在指腹划出一道白痕。里面应该有补给，可我不想为几包罐头弄出一道止不住血的伤口。\n'
                    '\n'
                    '岑苇替我按住箱盖，说有工具刀就能沿缝挑开；没有的话，也可以垫着布慢慢撬，只是难免会划伤。我们还可以放弃箱里的东西，把外面的木板拆走。眼下每样东西都有用，得先想清楚自己更缺哪一种。',
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
            'text': '我在一堵残墙后发现一堆刚熄灭不久的灰烬，旁边摆着两只杯子，杯底的水还没有结冰。这里的人大概才离开不久，也许只是去附近找吃的，可我们等了很长时间，始终没有人回来。\n'
                    '\n'
                    '岑苇在地上找到一条还算干燥的毯子，墙根则堆着几块没烧完的燃料。我们带不走所有东西。我把杯子重新摆好，尽量没有碰乱他们留下的行李，再和她商量应该取走什么。',
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
           'text': '我正准备离开药店，后门忽然传来一阵压得很低的咳嗽。我问里面有没有人，对方没有开门，只从门缝塞出一张纸，上面写着还有孩子，需要食物。紧接着，一只装着螺丝和导线的碗被推了出来。\n'
                   '\n'
                   '岑苇看了看我们的背包，没有催我作决定。我不清楚门后的人是否可信，也知道两份口粮足够让我们多撑一晚。门里又咳了起来，我只好先蹲下，隔着门问他们还有什么可以交换。',
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
           'text': '冷柜里的冰早就化成了浑水，我和岑苇戴着捡来的手套，把还能用的密封食品从上层取出来。气味很难闻，好在包装没有破，擦干净就能带走。\n'
                   '\n'
                   '柜台后面还立着一台坏热水器，外壳已经松开，里面的导线和金属件保存得不错。岑苇说再花些工夫就能拆下来，只是我们今天没办法两头都顾上。我清了清背包里的位置，开始考虑是先带吃的回去，还是把这个机会留给修理设备。',
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
           'text': '楼顶的晾衣绳上还挂着几件冬衣，风一吹，衣袖就在墙上来回扫动。我伸手摸了摸，外层已经干了，拆开以后应该足够缝制保暖的衣服。绳子最里面还有一件小外套，袖口补过两回，针脚密密地挤在一起。\n'
                   '\n'
                   '我把小外套推回背风处，没有摘下来。岑苇指着楼梯间说那里可能还有应急柜，如果我们不想动这些衣服，可以再下去找找，只是要多费一些力气。',
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
              'text': '我翻开气象年鉴时，一封没有寄出的信从书页里掉下来。写信的人在给尚未出生的孩子解释，为什么今年的海一直不平静。他写到最后已经没了把握，只说如果有一天海底发亮，不要急着把那当作太阳。\n'
                      '\n'
                      '年鉴的边缘记着许多工程参数，或许能帮助我们弄懂设备。岑苇却让我先别翻页，她想听完这封信。我看着那几行越来越潦草的字，忽然很难再把它们只当成待整理的资料。',
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
              'text': '我正在翻找线材，走廊里的广播突然响了。它用平板的语调念着逾期借阅者的名字，念到最后，竟然叫出了我和岑苇。我们谁也没来过这里，更不可能办过借阅证。\n'
                      '\n'
                      '岑苇伸手拉住我的衣角，我才发现自己已经走到了扬声器下面。那里面还在重复我们的名字。我可以把它拆掉，取出能用的零件，也可以先陪她退到门外，确定自己没有听错，再决定要不要回去。',
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
             'text': '药柜的玻璃碎了一半，下面贴着“请按需取用”的纸条。我清开碎玻璃，找到几瓶没过期的药和一些纱布。最里层还放着应急干粮，旁边有一颗没拆糖纸的水果糖。\n'
                     '\n'
                     '岑苇认出了那种糖，说以前护士会拿它哄不愿吃药的孩子。她说完自己也觉得有些奇怪，毕竟我们现在早就没有挑拣食物的余地。我把能带走的东西摆在台面上，和她一起重新数了一遍。',
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
             'text': '我在洗手池旁清洗伤口时，余光看见镜子里的自己慢了一拍。我的手已经放下，镜中的手却还停在水龙头边。那一瞬间，我几乎以为自己太累，终于开始看见不存在的东西。\n'
                     '\n'
                     '岑苇没有让我继续看下去，她把镜子翻向墙壁，又让我坐到门边。我们可以在这里互相检查一下伤口，也可以赶紧拆下保温帘，离开这间让我越来越不舒服的诊室。',
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
            'text': '备用机房里堆着拆到一半的设备，墙上用铅笔画了很多短线，似乎是值守员用来计日子的。最后一组只画到第六道，旁边的铅笔却还削得很尖。我没有告诉岑苇自己在想什么，只把手电照向了工具架。\n'
                    '\n'
                    '这里的备件够我们做不少东西，桌下的背包里也可能有吃的。岑苇检查了一遍门锁，提醒我别在这个没有窗户的地方待太久。我们得选一处先找。',
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
            'text': '管道深处响起三下敲击，我停下手里的动作，等了一会儿，同样的声音又响了一遍。我喊了几声，没有人回答；无论我们说什么，那声音总是隔着相同的时间重复。\n'
                    '\n'
                    '岑苇用扳手轻轻碰了碰管壁，想确认声音是从哪边来的。我想起照片背面的警告，心里有些发紧。如果那真是设备在模仿求救，继续回答也许不是好主意。可我也想知道，当我们换一种节奏，它会不会跟着改变。',
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
            'text': '锚链中间竟然长着一株白花，我蹲下去仔细看，才发现它的根扎在碎木和薄薄的淤泥里。周围的盐结得很厚，那一点白色仍然没有枯。我不知道它还能撑多久，只觉得自己不应该碰坏它。\n'
                    '\n'
                    '岑苇在旁边看了很久，问我有没有带纸。我翻出手记，空白页已经不多，但留一页画下它似乎也没有什么不好。背风的船壳下面还有些能用的东西，等我们离开前可以再收拾。',
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
            'text': '盐层下面露出一排铺路木，沿着它向前看，我终于辨认出旧维护线的轮辙。拖橇从这里走，会比直接穿过泥地省力得多。我在地图上补好记号，免得回来时找不到路。\n'
                    '\n'
                    '维护线一侧散着还能燃烧的干木，另一侧停着一艘补给艇。舱门半开着，里面应该还有东西，只是得绕过一大片裂开的淤泥。我问岑苇还撑不撑得住，再和她商量这一趟要走多远。',
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
            'text': '我推开厨房门，发现炉台已经被打扫干净，两只碗倒扣在架子上。米和应急食品都装在密封桶里，桶盖上留了张便条，请接班的人节省一点，不要指望下一班补给船准时到。\n'
                    '\n'
                    '我看完便条，又看了一眼窗外干涸的海床，没有把它念给岑苇听。她在隔壁找到备用仪表和线材，问我要不要一起搬过来。我们终于到了灯塔，可现在还不能急着坐下。',
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
            'text': '我扶着栏杆站到塔顶，来时的几个营地都能从这里看见，距离比走路时感觉的近得多。那些让我以为再也走不出的废墟，现在只剩下雾里几块深色的轮廓。我的腿还在发抖，一时说不清是累，还是终于后怕起来。\n'
                    '\n'
                    '岑苇坐在避风的一侧，拍了拍身边的位置。我可以陪她歇一会儿，也可以趁还有光，继续检查准备好的设备。无论选哪一种，我都不想再把她一个人留在这里。',
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


TALKS = [('第一件想做的事',
  '我问岑苇，如果我们真的能离开这里，她最想做什么。她想了半天，说想去一家普通面馆，最好窗外连一点海都看不见。我以为她饿了，她却摇头，说她只是很想再听一次老板问要不要加葱。\n'
  '\n'
  '我告诉她自己不吃葱，到时候可以全夹给她。她嫌弃地看了我一眼，又笑了。我没有再往下追问，只默默记住了那家还不知道在哪里的面馆。'),
 ('录音师',
  '岑苇一直以为我是记者，直到今晚看见我整理录音笔里的素材，才知道我平时给电影补录声音。我告诉她，有时候一个人走过碎石的几秒钟，要反复录上几十遍，导演才觉得像是真的。\n'
  '\n'
  '她听完笑了，说现在遍地都是碎石，倒是方便我工作。我也跟着笑了一会儿，随后才意识到，自己已经很久没有因为这种无关紧要的事笑过。'),
 ('没说完的话',
  '岑苇把母亲最后发来的那条消息播放给我听，只有七秒，前面两秒全是水声。她说自己这几天总是不敢听完，怕里面留着一句还没来得及回答的嘱托。\n'
  '\n'
  '我们把音量开到最大，反复听了好几遍，终于听清她母亲问的是冰箱里的鱼还要不要留。我不知道该怎么安慰她，只好认真地说，等回去以后，先买一条新的。岑苇低下头，过了很久才应了一声。'),
 ('各自的节拍',
  '我走路时习惯数步子，四步吸气，四步呼气，累的时候这样会舒服一点。岑苇今天听见了，问我为什么总走到第四步就慢下来。我说可能是担心她没有跟上，她却说她也一直在等我。\n'
  '\n'
  '我们对着彼此看了一会儿，才发现这几天谁都不愿意催另一个人。后来她让我照原来的节奏走，说自己会跟在旁边，不必非得把脚步踩在同一个地方。'),
 ('如果没有明天',
  '火快灭的时候，我终于问出了那句一直不敢说的话：如果我们忙了这么多天，最后还是没能活下来呢？岑苇没有立刻回答，只把剩下的木条又折成两截，往火里添了一截。\n'
  '\n'
  '她说她也怕，怕得有时连眼睛都不敢闭，可只要明早还能醒，就还是想吃点东西，想再往灯塔走一段。我望着她留在手边的那半截木头，觉得自己暂时也能这么做。'),
 ('记住名字',
  '我越来越少听见风声，夜里有时会惊醒，怀疑是自己的耳朵先出了问题。岑苇发现以后，没有让我一遍遍检查录音笔，而是叫我说一件今天发生过的事，她再补上一件。\n'
  '\n'
  '我们就这样慢慢聊着，从谁先发现那扇没锁的门，说到我煮糊了一点的晚饭。等我不再紧盯着黑暗，她才把毯子拉过来。我听见她说自己的名字，还听见我答应她，明天早上也会记得。')]


ENDINGS = {'tomorrow': ('01',
              '没有天气预报的明天',
              '我把手放上触点时，脑子里还在回想那些校准步骤。岑苇没有跟着我的呼吸调整自己，而是照我们练过的那样，在第四拍稍作停顿。两条心跳曲线在屏幕上靠近，又始终没有重合。\n'
              '\n'
              '装置响起的那一瞬间，我以为自己的耳膜会被撕裂。随后，广播突然中断，整座塔都安静下来。我死死抓住扶手，直到岑苇拉我的袖子，才发现窗外有水落在铁皮上。\n'
              '\n'
              '我没敢立刻把那当成海回来的征兆，只陪她下楼，一点点走到维护道边。冰冷的水正从石缝里渗出来，漫过我们留下的脚印。\n'
              '\n'
              '我们还不知道城里有没有别人活着，也不知道这台机器是不是真的停住了。但岑苇问我明天会不会下雨时，我终于可以告诉她，我不知道。'),
 'shelter': ('02',
             '把灯留着',
             '我按病历里的号码打开机械门，把最后的粮食和燃料搬进避难室。岑苇坚持让我把塔顶的灯留着，说如果还有人往这里走，至少得让他们知道这不是一座空塔。\n'
             '\n'
             '地面上的声音在那天夜里消失了。门后的机械钟还在走，我贴近表壳，听见极轻的振动，才敢相信我们没有跟着外面的世界一起停下来。\n'
             '\n'
             '后来，我们开始用纸笔交谈，每天轮流摇动发电机。食物比预想的消耗得更快，我不敢在手记里写还能坚持多少天。\n'
             '\n'
             '有一天下午，门板传来三下敲击。我和岑苇谁都没有马上去开门。我先贴着门，慢慢敲出了另一个节奏，等着外面的人回答。'),
 'voice': ('03',
           '替世界守夜的人',
           '我看着控制台上的单人接管说明，终于明白了那名值守员为什么会留下照片。我知道把手放上去以后会发生什么，可当屏幕再次显示岑苇的心跳时，还是没有把手收回来。\n'
           '\n'
           '她发现得太晚，只来得及叫我的名字。隔离门落下前，我看见她扑到玻璃上，用力敲了两下。我想告诉她先走，扩音器里传出的却是那句天气预报。\n'
           '\n'
           '从那以后，我仍然能感觉到灯塔的振动，也能透过它听见海水慢慢回到岸边。有时候，我甚至分不清自己究竟是在等她，还是只在等下一轮播报。\n'
           '\n'
           '直到有一天，一个熟悉的声音从塔外传来，告诉我今天下雨了。我试了很久，想回答她一句不在程序里的话，最后仍然只说出了“明日，沿岸晴”。'),
 'silent': ('04',
            '无人应答',
            '我把最后一块燃料放进火里，和岑苇靠在一起，等着第十八天的太阳落下。我们已经来不及再去灯塔，可我还是时不时抬头，看它的灯光有没有什么变化。\n'
            '\n'
            '先是木头不再发出噼啪声，随后连岑苇的呼吸也听不见了。她的胸口还在起伏，手心仍然温热，我便一次次握紧她，确认她没有离开。\n'
            '\n'
            '等远处的灯终于停止闪烁，我发现自己的手指也开始变得僵硬。我翻开手记，想把我们这几天经历的事写下来，笔尖却越来越难以移动。\n'
            '\n'
            '最后一页只写下了两个名字。我希望下一次有人经过这里时，至少能知道我们曾经一起走到过这个地方。'),
 'lost': ('05',
          '走不到的海岸',
          '我已经很难把背包重新抬到肩上。地图上的路并没有变长，可每次站起来，眼前都会黑上一阵。岑苇把东西一件件拿出来，想替我减轻些重量，我却连告诉她不必再忙都要停下来喘气。\n'
          '\n'
          '我们在背风的地方坐下。她把红围巾系到路旁的标桩上，回来时仍然说再歇一会儿就走。我看见她把药盒翻了个遍，没有找到能用的东西。\n'
          '\n'
          '远处的灯塔比昨晚更清楚了。我望着那一点光，第一次觉得准备得够不够、走得对不对，已经不是能够重新商量的事。手记还压在我膝上，我却没有力气再翻过这一页。'),
 'drift': ('06',
           '忘记名字之前',
           '起初我只是听不清岑苇在说什么，以为她离得太远。可她蹲到我面前，握住我的手，一字一字地重复时，那些我明明熟悉的声音仍然像别人的语言。\n'
           '\n'
           '我开始害怕，急着在手记上找能说明这一切的记录，却连自己的字迹也认得越来越慢。她拿走我的笔，把两个名字写在掌心，又把我的手放到旁边，像是在教我记住一件非常简单的事。\n'
           '\n'
           '我知道自己不能忘，可每当抬头去看她，那一点刚抓住的念头就会散开。最后，我只好一直低头看着我们的手，不再去想灯塔和海在哪里。至少现在，我还愿意相信这两个名字很重要。')}

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
         'tab': 'explore', 'night_count': 0, 'tutorial': 0}
    log(s, '出发', '海退去了。你们决定一起找到那座仍在报时的灯塔。')
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
    spend(s, 4 if gear(s, 'sled') else 8, True)
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
    s['pending'] = event('不是回声', '我慢慢转动调频旋钮，直到刻度停在九十一点六。杂音里突然传出一个女人的问话，她问我们能不能听见。我报出自己的名字，对方竟然准确地重复了一遍。另一端真的有人活着。\n\n她告诉我，曾有人试着独自接替灯塔的信号源，救回了一片海域，却再也没能离开设备。要真正停止寂潮，必须让两个人保持不同的节律，同时完成校准。我一边追问，一边把她报出的参数写下来。岑苇握着接收机，手指一直在发抖。', [choice('抄下双人校准频率', {'flags': ['live_signal'], 'knowledge': 2, 'bond': 5, 'sanity': 6}, result='记录实时频率。知识 +2，羁绊 +5，两人精神 +6。')], '主线 / 实时信号')
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

def dispatch(s, command):
    if s['ending']: return False
    kind = command[0]
    if kind == 'choose': return choose(s, command[1])
    if s['pending']: return False
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
