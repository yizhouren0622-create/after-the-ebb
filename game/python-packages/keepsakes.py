"""Persistent reading records and title-screen objects, independent of Ren'Py."""

OBJECTS = [
    ('mugs', '两只搪瓷杯', ['first_night', 'daily_talk'], '熬过第一夜，或连续谈心五天。', '杯沿各缺了一小块。放在一起时，缺口朝着不同的方向。'),
    ('crate', '装满罐头的木箱', ['hoarder', 'warehouse', 'full_meals'], '达成囤粮、材料储备或连续饱餐成就。', '最下面那排罐头垫着旧报纸，箱外用粉笔画了两只碗。'),
    ('bandage', '缠过绷带的手套', ['edge', 'comeback'], '达成命悬一线或力挽狂澜。', '绷带拆下以后，手套上还留着斜斜的压痕。'),
    ('roll', '补好的工具卷', ['home', 'maker'], '加固营地，或制作六种永久装备。', '针别在布卷内侧，扳手与螺丝刀之间塞着一块折过的布。'),
    ('lantern', '挡风的提灯', ['cold', 'storm', 'warmth'], '度过寒流、盐暴，或连续三晚生火。', '灯罩底边糊着盐。提起时，里面的灯芯轻轻晃了一下。'),
    ('chart', '折旧的航道图', ['explorer', 'tower'], '完成十二次探索，或并肩抵达灯塔。', '折痕处补着纸，红线沿着旧航道一直画到灯塔。'),
    ('plant', '裂盆里的幼苗', ['tomorrow'], '达成「没有天气预报的明天」。', '花盆的裂缝拿铁丝捆住。底下垫着接水的小碟子。'),
    ('book', '写满的练习本', ['quiz'], '答对五道知识补给题。', '答错的地方划着一道线，铅笔用细绳系在封底。'),
]


def unlocked(earned):
    return [row for row in OBJECTS if any(k in earned for k in row[2])]


def merge_records(records, report):
    import copy
    scene = report.get('scene') if report else None
    if not scene: return records
    title = scene['title']
    old = records.get(title, {})
    if old.get('results', {}).get(str(scene['index'])) == scene['result']:
        return records
    records = copy.deepcopy(records)
    entry = {k: scene[k] for k in ['title', 'text', 'tag', 'loc', 'choices']}
    entry['results'] = dict(old.get('results', {}))
    entry['results'][str(scene['index'])] = scene['result']
    records[title] = entry
    return records


def seen(records, title, index=None):
    entry = records.get(title)
    if not entry: return False
    return bool(entry['results']) if index is None else str(index) in entry['results']


def region_records(records, region):
    return [v for v in records.values()
            if ('camp' if v['tag'] == '营火旁' else v['loc']) == region]


def total_choices(records):
    return sum(len(row['results']) for row in records.values())
