init -20 python:
    config.name = "海退之后"
    config.version = "1.1.0"
    config.save_directory = "AfterTheEbb-1.0-release"
    config.screen_width = 1600
    config.screen_height = 900
    config.window_title = "海退之后 / After the Ebb"
    config.window_icon = "images/icon.png"
    config.has_sound = True
    config.has_music = True
    config.has_voice = False
    config.rollback_enabled = False
    config.allow_skipping = False
    config.autosave_on_choice = False
    config.autosave_on_quit = False
    config.autosave_on_input = False
    config.default_music_volume = .45
    config.default_sfx_volume = .5
    config.default_fullscreen = False
    config.default_text_cps = 0
    config.game_menu_action = ShowMenu("pause_menu")
    config.developer = False
    config.check_conflicting_properties = True
    config.main_menu_music = "audio/ebb.wav"
    config.main_menu_music_fadein = 2.0
    build.name = "AfterTheEbb"
    build.directory_name = "AfterTheEbb-1.1"
    build.executable_name = "AfterTheEbb"
    build.mac_info_plist = {
        "CFBundleIdentifier": "io.github.yizhouren0622-create.aftertheebb",
        "CFBundleDisplayName": "海退之后",
    }
    build.include_update = False
    build.classify("**.pyc", None)
    build.classify("**.bak", None)
    build.classify("**~", None)
    build.classify("game/cache/**", None)
    build.classify("game/saves/**", None)
    build.classify("**/__pycache__/**", None)
    build.classify("tests/**", None)
    build.classify("**.log", None)
    build.classify("log.txt", None)
    build.classify("traceback.txt", None)
    build.classify("errors.txt", None)
    build.classify("game/**", "all")
    build.classify("*.txt", "all")
    build.classify("*.md", "all")

default persistent.endings = []
default s = None

init python:
    import survival as sim
    import opening
    import time
    PAPER = "#080b0c"
    INK = "#e4e7e2"
    DEEP = "#080b0c"
    MUTED = "#b1bbb6"
    RUST = "#df9b8b"
    LINE = "#8d9a93"

    def bordered(fill):
        return Frame(Composite((8, 8), (0, 0), Solid("#d9e0da", xysize=(8, 8)), (1, 1), Solid(fill, xysize=(6, 6))), 2, 2)

    def fmt(n):
        return str(int(n)) if n == int(n) else str(n)

    def saved_time(slot):
        stamp = renpy.slot_mtime('manual-' + slot)
        return time.strftime('%Y/%m/%d  %H:%M', time.gmtime(stamp + 8 * 3600)) if stamp else '尚未留下记录'

    def sound_click():
        renpy.sound.play("audio/click.wav")

    def select_tab(tab):
        s['tab'] = tab
        if s.get('tutorial', 7) == 1 and tab == 'bag':
            s['tutorial'] = 3 if sim.gear(s, 'shelter') else 2
        renpy.restart_interaction()

    def mark_ending(key):
        if key not in persistent.endings:
            persistent.endings.append(key)
            renpy.save_persistent()

style default:
    font "fonts/SourceHanSansLite.ttf"
    size 23
    color INK
    language "unicode"

style text:
    line_spacing 6

style button:
    background bordered("#080b0c")
    hover_background bordered("#334344")
    insensitive_background bordered("#111718")
    padding (18, 12)
    hover_sound "audio/click.wav"

style button_text:
    size 23
    color INK
    hover_color RUST
    insensitive_color "#65706d"
    selected_color RUST

style textbutton is button
style textbutton_text is button_text

style panel:
    background bordered("#101617")
    padding (24, 20)

style small:
    size 19
    color MUTED

style label_text:
    size 22
    color RUST

style bar:
    ysize 6
    left_bar Solid(RUST)
    right_bar Solid("#364345")
    thumb None
    thumb_shadow None

style vbar:
    xsize 6
    base_bar Solid(LINE)
    thumb Solid(MUTED)
    thumb_shadow None

style slider:
    ysize 20
    left_bar Solid(RUST)
    right_bar Solid(LINE)
    thumb Solid(INK, xsize=12, ysize=20)
    thumb_shadow None

transform rise_in:
    alpha 0.0 yoffset 12
    ease .24 alpha 1.0 yoffset 0

screen main_menu():
    tag menu
    add "images/shore-final.png" xysize (1600, 900)
    add Solid("#080b0ce8") xsize 640
    add Solid(RUST) xpos 82 ypos 110 xysize (45, 4)
    vbox:
        xpos 80 ypos 152 spacing 12
        text "AFTER THE EBB" size 20 color RUST kerning 5
        text "海退之后" size 82 color INK
        text "海消失的第十八天，\n连告别也将不再有声音。" size 24 color MUTED line_spacing 10
    vbox:
        xpos 68 ypos 430 spacing 4
        textbutton "开始一段旅途  →" action ShowMenu("expedition_setup") text_size 29
        if renpy.can_load("journey"):
            textbutton "继续 / 自动存档" action FileLoad("journey", confirm=False, slot=True)
        elif renpy.can_load("camp"):
            textbutton "继续 / 清晨备份" action FileLoad("camp", confirm=False, slot=True)
        if renpy.can_load("quick-1"):
            textbutton "读取快速存档" action QuickLoad(confirm=False)
        textbutton "旅途手册" action Show("handbook")
        textbutton "留下的回声  /  [len(persistent.endings)] / 6" action ShowMenu("ending_archive")
        textbutton "声音与画面" action ShowMenu("preferences_menu")
        textbutton "离开" action Quit(confirm=False)
    text "一部关于准备、取舍，与两个人如何活下去的生存冒险。" xpos 82 ypos 817 size 18 color MUTED
    text "原创独立短篇  /  v1.1" xpos 82 ypos 852 size 17 color MUTED

screen expedition_setup():
    tag menu
    default mode = "standard"
    default bag = "tools"
    add Solid(PAPER)
    text "出发之前" xpos 110 ypos 75 size 50
    text "你带不走全部的昨天。选一件行李，再决定如何走过这段路。" xpos 112 ypos 145 size 24 color MUTED
    hbox:
        xpos 110 ypos 235 spacing 24
        for key, num, name, desc in [("tools", "01", "修理工的工具袋", "口粮 6 / 木料 3 / 金属 3\n导线 1 / 布料 1 / 燃料 2\n\n适合尽快搭营与制作工具。"), ("rations", "02", "渡轮的应急箱", "口粮 11 / 药品 1 / 生食 2\n木料 1 / 布料 1 / 燃料 2\n\n多一些余地，慢慢摸清路线。"), ("keepsake", "03", "没寄出的旅行包", "口粮 7 / 布料 3 / 导线 2\n木料 1 / 燃料 2 / 初始羁绊 60\n\n里面装着旧信和珍藏的录音。")]:
            button:
                xysize (444, 340)
                background bordered("#202b2b" if bag == key else "#101617")
                action SetScreenVariable("bag", key)
                padding (30, 25)
                vbox:
                    spacing 14
                    text num size 22 color RUST
                    text name size 30
                    text desc size 20 color MUTED line_spacing 6
    hbox:
        xpos 110 ypos 587 spacing 24
        textbutton "求生 / 标准规则" action SetScreenVariable("mode", "standard") selected mode == "standard"
        textbutton "余温 / 补给更充裕，环境伤害较低" action SetScreenVariable("mode", "gentle") selected mode == "gentle"
    text "每局最多 18 天，每天 3 行动。随机事件不重复抽取直至事件池轮完。\n关键线索固定获得；没有战斗操作。每次行动后自动保存，新游戏自带教学。" xpos 128 ypos 660 size 21 color MUTED line_spacing 9
    textbutton "← 返回" xpos 110 ypos 790 action ShowMenu("main_menu")
    textbutton "带上行李，出发  →" xpos 1115 ypos 785 background bordered(DEEP) text_color INK text_hover_color "#e9b5a8" action Start("begin_" + bag + "_" + mode)

screen crew_card(p, index):
    fixed:
        xysize (258, 270)
        add bordered("#101617")
        text p['name'] xpos 20 ypos 10 size 28
        text p['role'] xpos 20 ypos 51 size 16 color MUTED
        if p['hurt']:
            text "受伤" xpos 187 ypos 19 size 17 color RUST
        for i, field in enumerate([('hp', '生命'), ('energy', '体力'), ('sanity', '精神')]):
            $ key, title = field
            text title xpos 20 ypos (83 + i * 43) size 17 color MUTED
            text str(p[key]) xpos 193 ypos (83 + i * 43) size 18 color (RUST if p[key] < 30 else INK)
            bar value StaticValue(p[key], 100) xpos 20 ypos (115 + i * 43) xysize (218, 5) left_bar Solid(RUST if p[key] < 30 else "#c0cbc3")
        textbutton "进食" xpos 20 ypos 224 text_size 17 padding (13, 3) background bordered("#1b2929") sensitive sim.amt(s, 'food') >= 1 action Return(('use', 'food', index))
        textbutton "治疗" xpos 104 ypos 224 text_size 17 padding (13, 3) background bordered("#1b2929") sensitive sim.amt(s, 'med') >= 1 action Return(('care_menu', index))

screen hub():
    tag game
    key "K_ESCAPE" action ShowMenu('pause_menu')
    key "K_f" action ToggleField(_preferences, 'fullscreen')
    key "K_F5" action QuickSave()
    key "K_F9" action QuickLoad(confirm=True)
    add Solid(PAPER)
    add Solid(DEEP) ysize 83
    text "海退之后" xpos 32 ypos 23 size 30 color INK
    text "AFTER THE EBB" xpos 195 ypos 34 size 14 kerning 2 color "#bbc7c6"
    text "第 [s['day']] 日" xpos 460 ypos 22 size 30 color INK
    $ days_left = 19 - s['day']
    text "距寂潮 [days_left] 天" xpos 608 ypos 33 size 19 color "#bbc7c6"
    $ ap_display = '● ' * s['ap'] + '○ ' * (3 - s['ap'])
    text "行动  [ap_display]" xpos 865 ypos 26 size 25 color "#e9b5a8"
    textbutton "手册" xpos 1184 ypos 19 text_color INK text_size 19 action Show("handbook")
    textbutton "存档 / 设置" xpos 1290 ypos 19 text_color INK text_size 19 action ShowMenu("pause_menu")
    textbutton "过夜 →" xpos 1455 ypos 18 text_color "#e9b5a8" text_size 21 action Return(('night_menu',))

    vbox:
        xpos 24 ypos 104 spacing 15
        use crew_card(s['crew'][0], 0)
        use crew_card(s['crew'][1], 1)
        fixed:
            xysize (258, 116)
            add bordered("#202b2b")
            text "羁绊" xpos 20 ypos 10 size 19
            text str(s['bond']) xpos 190 ypos 10 size 22 color RUST
            bar value StaticValue(s['bond'], 100) xpos 20 ypos 46 xsize 218
            text "知识" xpos 20 ypos 63 size 19
            text str(s['knowledge']) xpos 190 ypos 63 size 22
    text "不消耗行动：进食 / 治疗\n口粮 1 → 体力 +18、生命 +8\n药品 1 → 生命 +28" xpos 36 ypos 803 size 16 color MUTED line_spacing 7

    $ loc = sim.PLACES[s['loc']]
    $ camp_view = s['tab'] in ['camp', 'craft', 'bag']
    $ camp_stage = 2 if sim.gear(s, 'shelter2') else 1 if sim.gear(s, 'shelter') else 0
    $ camp_names = ['露天落脚点', '防风营地', '加固营地']
    fixed:
        xpos 306 ypos 104 xysize (1268, 280)
        if camp_view:
            add Solid('#000000')
            add Transform('images/camp-' + str(camp_stage) + '.png', xysize=(1268, 280), fit='contain') xalign .5
        else:
            add Transform(Crop((0, 300, 1672, 500), "images/" + ("shore-final" if loc[3] == "shore" else loc[3]) + ".png"), xysize=(1268, 280)) matrixcolor (TintMatrix("#b6c8d4") if loc[3] != 'shore' else IdentityMatrix())
        add Solid("#080b0cbf") ypos 180 ysize 100
        text ('CAMP / LEVEL ' + str(camp_stage) if camp_view else loc[1]) xpos 26 ypos 192 size 16 color "#dde5df" kerning 2
        text (camp_names[camp_stage] if camp_view else loc[0]) xpos 24 ypos 220 size 37 color INK
        $ w = sim.weather(s)
        text w[0] xpos 1022 ypos 202 size 26 color INK
        text "风暴：12–13 日" xpos 1022 ypos 242 size 16 color "#dde5df"
    text w[1] xpos 327 ypos 399 size 20 color RUST

    hbox:
        xpos 306 ypos 439 spacing 5
        for tab, label in [('explore', '探索'), ('camp', '营地'), ('craft', '制作'), ('map', '路线'), ('bag', '背包'), ('journal', '手记')]:
            textbutton label:
                xsize 153 ysize 49
                background bordered(DEEP if s['tab'] == tab else "#141e1f")
                text_color INK
                text_xalign .5
                action Function(select_tab, tab)
        textbutton "F5 快存 / F9 快读" text_size 16 xsize 300 action QuickSave()

    frame:
        xpos 306 ypos 503 xysize (806, 331)
        background bordered("#101617") padding (24, 20)
        if s['tab'] == 'explore':
            vbox:
                spacing 14
                text loc[2] size 23
                text "主要发现：" + loc[4] size 18 color MUTED
                text "已探索 [s['visits'].get(s['loc'], 0)] 次 / 每次消耗 1 行动与两人体力约 10" size 18 color MUTED
                textbutton "调查周围  →" background bordered(DEEP) text_color INK xsize 710 text_xalign .5 sensitive not sim.outdoor_reason(s) action Return(('explore',))
                if s['loc'] == 'relay':
                    textbutton "调频调查 / 1 行动" sensitive not sim.scan_reason(s) action Return(('scan',))
                if sim.outdoor_reason(s):
                    text sim.outdoor_reason(s) size 18 color RUST
                else:
                    text "低体力时继续行动会失去生命。需要时先休息或进食。" size 18 color MUTED
        elif s['tab'] == 'camp':
            vbox:
                spacing 10
                text "火还亮着的时候" size 27
                hbox:
                    spacing 16
                    textbutton "轮流休息 / 1 行动" background bordered("#1a2828") sensitive s['ap'] > 0 action Return(('rest',))
                    textbutton "说会儿话 / 1 行动" background bordered("#1a2828") sensitive s['ap'] > 0 and s['talk_day'] != s['day'] action Return(('talk',))
                text "休息：体力 +20，精神 +4。营地可进一步增加恢复。\n交谈：精神 +12，羁绊 +7，每天一次。" size 18 color MUTED
                textbutton "分配晚餐，结束今天  →" action Return(('night_menu',))
                if s['loc'] == 'tower' and sim.has(s, 'tower_seen'):
                    textbutton "走向控制台 / 最终抉择  →" text_color RUST action Return(('final_menu',))
                else:
                    text "营地为可携带篷布，移动时自动随行。" size 18 color MUTED
        elif s['tab'] == 'craft':
            viewport:
                xysize (754, 291) child_size (730, None) mousewheel True draggable True
                vbox:
                    spacing 13
                    for key, recipe in sim.RECIPES.items():
                        $ reason = sim.recipe_reason(s, key)
                        hbox:
                            spacing 15
                            vbox:
                                xsize 490 spacing 3
                                text recipe[0] size 23
                                text sim.costs_text(recipe[1]) size 17 color RUST
                                text recipe[2] size 17 color MUTED
                            textbutton ("已完成" if sim.gear(s, key) else "制作 / 1 行动"):
                                xsize 210 text_size 20
                                background bordered("#1a2828")
                                sensitive not reason
                                action Return(('craft', key))
                        if reason and reason != '已完成':
                            text reason size 16 color RUST
                        add Solid(LINE) xysize (710, 1)
        elif s['tab'] == 'map':
            viewport:
                xysize (754, 291) child_size (730, None) mousewheel True draggable True
                vbox:
                    spacing 8
                    for key in sim.ORDER:
                        $ found = key in s['unlocked']
                        $ reason = sim.travel_reason(s, key)
                        button:
                            xsize 722 padding (14, 10)
                            background bordered("#182223" if s['loc'] == key else "#101819")
                            sensitive found and not reason
                            action Return(('travel', key))
                            hbox:
                                vbox:
                                    xsize 515 spacing 2
                                    text (sim.PLACES[key][0] if found else '未发现区域') size 24
                                    text (reason if reason else sim.PLACES[key][4]) size 17 color MUTED
                                text ('所在营地' if key == s['loc'] else '前往 / 1 行动') size 18 color RUST yalign .5
        elif s['tab'] == 'bag':
            viewport:
                xysize (754, 291) child_size (730, None) mousewheel True draggable True
                vbox:
                    spacing 12
                    text "共同的行李" size 27
                    for key, name in sim.ITEMS.items():
                        text (name + '    ' + fmt(sim.amt(s, key))) size 22
                    text "已经制作的装备" size 24
                    text (' / '.join(sim.RECIPES[k][0] for k in s['gear']) or '还没有装备。先用木料与布料搭营。') size 20 color MUTED
        elif s['tab'] == 'journal':
            viewport:
                xysize (754, 291) child_size (730, None) mousewheel True draggable True
                vbox:
                    spacing 12
                    text "这一路发生的事" size 27
                    for entry in reversed(s['log']):
                        text ('第 %d 日  /  %s' % (entry['day'], entry['title'])) size 19 color RUST
                        text entry['text'] size 19
                    text "记录下来的片段" size 27
                    for memory in reversed(s['memories']):
                        text memory['title'] size 22 color RUST
                        text memory['text'] size 19

    frame:
        xpos 1130 ypos 503 xysize (444, 331)
        background bordered("#182223") padding (23, 20)
        vbox:
            spacing 14
            text "接下来" size 18 color RUST
            text sim.objective(s) size 23
            add Solid("#87928b") xysize (395, 1)
            fixed:
                xysize (395, 42)
                text "口粮" size 19 ypos 4
                text fmt(sim.amt(s, 'food')) size 24 xpos 88
                text "药品" size 19 xpos 215 ypos 4
                text fmt(sim.amt(s, 'med')) size 24 xpos 310
            fixed:
                xysize (395, 42)
                text "燃料" size 19 ypos 4
                text fmt(sim.amt(s, 'fuel')) size 24 xpos 88
                text "生食" size 19 xpos 215 ypos 4
                text fmt(sim.amt(s, 'raw')) size 24 xpos 310
            text "两人一晚吃饱需 2 口粮；半份可节粮，恢复较少。" size 18 color MUTED
    text s['last_result'] xpos 315 ypos 851 xsize 1050 size 18 color RUST
    text '进度已自动保存' xpos 1410 ypos 855 size 16 color MUTED

    if s.get('tutorial', 7) < 7:
        $ guide = [
            ('先找一点物资', '点击下方“调查周围”。每次探索消耗 1 行动，并带回物资或线索。'),
            ('看看刚找到的东西', '点击“背包”。两人共用食物和材料，先认清手里有什么。'),
            ('给今晚找个住处', '点击“制作”，再制作“防风营地”。它能帮两人每晚恢复更多体力。'),
            ('体力不是生命', '点击任一人物下方的“进食”。吃 1 口粮可以恢复体力，不消耗行动。'),
            ('别让精神一直往下掉', '点击“营地”，选择“说会儿话”。交谈恢复精神，也会增加羁绊。'),
            ('把今天的饭分好', '点击右上角“过夜”。先按默认每人一份分餐，再确认过夜。'),
            ('去新的地方看看', '点击“路线”，前往“盐蚀街区”。到达后探索，能发现更多区域。')][s.get('tutorial', 7)]
        frame:
            xpos 328 ypos 117 xysize (910, 157) background bordered('#000000') padding (20, 12)
            vbox:
                spacing 7
                text ('上手教学 %d / 7：%s' % (s['tutorial'] + 1, guide[0])) size 24 color INK
                text guide[1] size 21 xsize 860 color MUTED
            textbutton '跳过教学' xpos 735 ypos 106 text_size 17 padding (8, 2) action SetDict(s, 'tutorial', 7)

screen story_event(e):
    modal True
    $ conversation = e['tag'] == '营火旁'
    if conversation:
        add Solid('#000000')
        add "images/travelers.png" xpos 1130 ypos 285 xysize (450, 365)
    else:
        $ event_bg = sim.PLACES[s['loc']][3]
        add ('images/' + ('shore-final' if event_bg == 'shore' else event_bg) + '.png') xysize (1600, 900)
        add Solid("#080b0cbb")
    frame at rise_in:
        xpos (45 if conversation else 260) yalign .5 xysize (1080, 808)
        padding (38, 28) background bordered('#000000')
        vbox:
            spacing 13
            text e['tag'] size 18 color RUST kerning 2
            text e['title'] size 34
            add Solid(LINE) xysize (1000, 1)
            viewport:
                xysize (1000, 370) mousewheel True draggable True
                child_size (965, None)
                text e['text'] size 24 line_spacing 10 xsize 965 color INK
            for index, c in enumerate(e['choices']):
                button:
                    xsize 1000 background bordered("#111a1b") padding (20, 10)
                    sensitive sim.can_choice(s, c)
                    action Return(('choose', index))
                    vbox:
                        spacing 1
                        text c['text'] size 22
                        if sim.choice_hint(c):
                            text sim.choice_hint(c) size 16 color RUST
            text "可用滚轮阅读正文" size 16 color MUTED

screen night_menu():
    modal True
    key "K_ESCAPE" action Return(('cancel',))
    default r0 = 1 if sim.amt(s, 'food') >= 2 else .5 if sim.amt(s, 'food') >= 1 else 0
    default r1 = 1 if sim.amt(s, 'food') >= 2 else .5 if sim.amt(s, 'food') >= 1 else 0
    default fire = False
    add Solid('#000000')
    add "images/travelers.png" xpos 1130 ypos 285 xysize (450, 365)
    frame at rise_in:
        xpos 45 yalign .5 xsize 1080 padding (45, 35) background bordered('#000000')
        vbox:
            spacing 22
            text "把今天分给两个人" size 38
            text "口粮 [fmt(sim.amt(s, 'food'))] / 燃料 [fmt(sim.amt(s, 'fuel'))] / 剩余行动 [s['ap']]（过夜后不保留）" size 21 color MUTED
            for i, p in enumerate(s['crew']):
                hbox:
                    spacing 16
                    text p['name'] size 26 xsize 145 yalign .5
                    for val, label in [(1, '一份'), (.5, '半份'), (0, '不吃')]:
                        textbutton label:
                            xsize 180 background bordered("#182223")
                            selected (r0 if i == 0 else r1) == val
                            action SetScreenVariable('r0' if i == 0 else 'r1', val)
            text "一份：生命 +5、体力 +26、精神 +4。\n半份：生命 -3、体力 +14。不吃：生命、精神持续下降。" size 20 color MUTED
            textbutton ("+ 生火过夜 / 燃料 1" if fire else "○ 生火过夜 / 燃料 1"):
                action ToggleScreenVariable("fire") sensitive sim.amt(s, 'fuel') >= 1
            $ protection = int(sim.gear(s, 'shelter')) + int(sim.gear(s, 'shelter2')) + int(sim.gear(s, 'coats')) + int(fire)
            $ damage = max(0, sim.weather(s)[2] - protection) * (4 if s['difficulty'] == 'gentle' else 7)
            text ("今晚保暖充足。" if damage == 0 else "预计失温：两人各失去生命 %d。" % damage) size 23 color RUST
            text "营地额外恢复体力；接收机恢复精神。生火：精神 +5、保暖 +1。" size 19 color MUTED
            hbox:
                spacing 20
                textbutton "再想一想" action Return(('cancel',)) xsize 280
                textbutton "收好行李，过夜  →":
                    xsize 620 background bordered(DEEP) text_color INK text_xalign .5
                    sensitive r0 + r1 <= sim.amt(s, 'food') and (not fire or sim.amt(s, 'fuel') >= 1)
                    action Return(('night', r0, r1, fire))

screen care_menu(index):
    modal True
    key "K_ESCAPE" action Return(('cancel',))
    add Solid('#000000')
    add "images/travelers.png" xpos 1130 ypos 285 xysize (450, 365)
    $ person = s['crew'][index]
    frame at rise_in:
        xpos 45 yalign .5 xsize 1080 padding (45, 35) background bordered('#000000')
        vbox:
            spacing 25
            text ('为' + person['name'] + '处理伤口') size 36
            text ('当前生命 %d / 100，现有药品 %s。' % (person['hp'], fmt(sim.amt(s, 'med')))) size 25
            text '使用一份药品可恢复生命 28，并解除受伤。\n治疗不消耗行动；尚未使用的药品可以留到之后。' size 24 color MUTED
            textbutton '使用药品 / 消耗 1 份':
                xsize 970 background bordered('#111a1b')
                sensitive sim.amt(s, 'med') >= 1
                action Return(('use', 'med', index))
            textbutton '暂时不用，返回营地' xsize 970 action Return(('cancel',))

screen final_menu():
    modal True
    add Solid("#1d2525db")
    frame:
        xalign .5 yalign .5 xsize 1100 padding (45, 30) background bordered(PAPER)
        vbox:
            spacing 15
            text "世界不只有一种答案" size 37
            text "最后的选择会结束这段旅途。你们可以先返回准备。" size 20 color MUTED
            for title, ok in sim.true_requirements(s):
                text (('+  ' if ok else '○  ') + title) size 22 color (INK if ok else RUST)
            textbutton "用两种节律，尝试中断寂潮":
                background bordered("#1e2c2c") xsize 1000
                sensitive all(ok for title, ok in sim.true_requirements(s))
                action Return(('finish', 'tomorrow'))
            textbutton "进入机械避难室，让灯继续亮着":
                background bordered("#1e2c2c") xsize 1000
                sensitive sim.has(s, 'clinic_record') and sim.amt(s, 'food') >= 4 and sim.amt(s, 'fuel') >= 2
                action Return(('finish', 'shelter'))
            text "避难条件：诊所解锁码、口粮 4、燃料 2。" size 18 color MUTED
            textbutton "梁弦接替信号源，让岑苇回到海岸":
                background bordered("#1e2c2c") xsize 1000
                sensitive s['bond'] >= 35 action Return(('finish', 'voice'))
            text "接替条件：羁绊不低于 35。你已经知道，这意味着告别。" size 18 color MUTED
            textbutton "还没有准备好，先返回" action Return(('cancel',))

screen handbook():
    modal True
    add Solid('#000000e8')
    frame:
        xalign .5 yalign .5 xsize 1060 padding (40, 30) background bordered('#000000')
        vbox:
            spacing 24
            text '先记住这三件事' size 38
            text '1  白天找物资' size 28 color RUST
            text '探索、移动、制作各用 1 行动，每天一共 3 次。' size 24
            text '2  晚上把饭分好' size 28 color RUST
            text '点右上角“过夜”，通常给每人一份口粮。没饭吃会掉生命和精神。' size 24 xsize 970
            text '3  累了就休息，心情差就交谈' size 28 color RUST
            text '体力低时别硬撑；在营地休息、交谈。进食和治疗不消耗行动。' size 24 xsize 970
            text '每次行动后自动保存，重新打开点“继续”即可。\n新游戏自带逐步教学；长列表用滚轮翻阅。' size 21 color MUTED
            textbutton '明白了，继续' xsize 970 text_xalign .5 action Hide('handbook')

screen pause_menu():
    tag menu
    add Solid(PAPER)
    text "暂停旅途" xpos 100 ypos 65 size 49
    text "每次行动后自动保存；下列手动档位可另外留作备份。" xpos 105 ypos 135 size 22 color MUTED
    hbox:
        xpos 105 ypos 230 spacing 28
        for slot in ['1', '2', '3']:
            frame:
                xysize (440, 430) background bordered("#101617") padding (25, 25)
                vbox:
                    spacing 10
                    text ('行李箱 ' + slot) size 29
                    text saved_time(slot) size 20 color MUTED
                    add FileScreenshot(slot, page="manual") xysize (360, 150)
                    hbox:
                        textbutton "保存" sensitive not main_menu action FileSave(slot, confirm=False, page="manual")
                        textbutton "读取" sensitive renpy.can_load('manual-' + slot) action FileLoad(slot, confirm=False, page="manual")
    hbox:
        xpos 105 ypos 720 spacing 25
        textbutton "继续" action Return()
        textbutton "读取自动档" sensitive renpy.can_load('journey') action FileLoad('journey', confirm=False, slot=True)
        textbutton "清晨备份" sensitive renpy.can_load('camp') action FileLoad('camp', confirm=False, slot=True)
        textbutton "旅途手册" action Show('handbook')
        textbutton "声音与画面" action ShowMenu('preferences_menu')
        textbutton "回到标题" action MainMenu(confirm=False)
    text "F5 快存 / F9 快读 / Esc 返回 / F 全屏" xpos 120 ypos 780 size 20 color MUTED

screen preferences_menu():
    tag menu
    add Solid(PAPER)
    vbox:
        xpos 180 ypos 130 spacing 38
        text "声音与画面" size 48
        text "环境声 / 配乐" size 25
        bar value Preference("music volume") xsize 900
        text "界面音效" size 25
        bar value Preference("sound volume") xsize 900
        hbox:
            spacing 30
            textbutton "窗口" action Preference('display', 'window')
            textbutton "全屏" action Preference('display', 'fullscreen')
        textbutton "返回" action (ShowMenu("main_menu") if main_menu else ShowMenu("pause_menu"))

screen ending_view(key):
    tag game
    add "images/tower.png" xysize (1600, 900)
    add Solid("#080b0cf5") xsize 1000
    vbox at rise_in:
        xpos 110 ypos 75 xsize 810 spacing 20
        text ('END ' + sim.ENDINGS[key][0] + '  /  第 %d 日' % s['day']) size 20 color RUST kerning 2
        text sim.ENDINGS[key][1] size 43
        viewport:
            xysize (810, 565) child_size (780, None) mousewheel True draggable True
            text sim.ENDINGS[key][2] size 23 line_spacing 10 xsize 775
        text "这段旅途已记入「留下的回声」。" size 18 color MUTED
        hbox:
            spacing 18
            textbutton "回到标题 →" action MainMenu(confirm=False)
            textbutton "读取清晨备份" sensitive renpy.can_load('camp') action FileLoad('camp', confirm=False, slot=True)

screen ending_archive():
    tag menu
    default selected = None
    add Solid(PAPER)
    text "留下的回声" xpos 110 ypos 75 size 48
    text "每一种抵达，都曾是某个人的全部。" xpos 113 ypos 147 size 23 color MUTED
    vbox:
        xpos 105 ypos 230 spacing 14
        for key, entry in sim.ENDINGS.items():
            textbutton (entry[0] + '  /  ' + (entry[1] if key in persistent.endings else '尚未抵达')):
                xsize 570 background bordered("#182223")
                sensitive key in persistent.endings action SetScreenVariable('selected', key)
        textbutton "← 返回" action ShowMenu('main_menu')
    if selected:
        viewport:
            xpos 750 ypos 230 xysize (720, 590) child_size (690, None) mousewheel True draggable True
            vbox:
                spacing 20
                text sim.ENDINGS[selected][1] size 32 color RUST
                text sim.ENDINGS[selected][2] size 22

screen confirm(message, yes_action, no_action):
    modal True
    add Solid("#1d2525c9")
    frame:
        xalign .5 yalign .5 xsize 780 padding (40, 40) background bordered(PAPER)
        vbox:
            spacing 30
            text message size 25
            hbox:
                spacing 50
                textbutton "确定" action yes_action
                textbutton "返回" action no_action

screen notify(message):
    zorder 100
    frame:
        xalign .5 ypos 95 background bordered(DEEP) padding (25, 15)
        text message size 23 color INK
    timer 2.2 action Hide('notify')

label start:
    jump begin_tools_standard

label main_menu:
    call screen main_menu
    jump main_menu

label begin_tools_standard:
    $ s = sim.new_game('tools', 'standard', int(time.time()) % 4294967296)
    jump introduction
label begin_tools_gentle:
    $ s = sim.new_game('tools', 'gentle', int(time.time()) % 4294967296)
    jump introduction
label begin_rations_standard:
    $ s = sim.new_game('rations', 'standard', int(time.time()) % 4294967296)
    jump introduction
label begin_rations_gentle:
    $ s = sim.new_game('rations', 'gentle', int(time.time()) % 4294967296)
    jump introduction
label begin_keepsake_standard:
    $ s = sim.new_game('keepsake', 'standard', int(time.time()) % 4294967296)
    jump introduction
label begin_keepsake_gentle:
    $ s = sim.new_game('keepsake', 'gentle', int(time.time()) % 4294967296)
    jump introduction

label introduction:
    play music "audio/ebb.wav" fadein 2.0
    $ s['pending'] = sim.event('海消失的早晨', opening.INTRO, [sim.choice('一起走下搁浅的渡轮', result='每日 3 行动。先探索找路线，或用木料 3、布料 1 搭营。')], '序 / 第一天')
    jump survival_loop

label survival_loop:
    $ renpy.save('journey')
    if s['ending']:
        $ mark_ending(s['ending'])
        play music "audio/ebb.wav" fadein 1.0
        call screen ending_view(s['ending'])
        return
    if s['pending']:
        call screen story_event(s['pending'])
        $ sim.dispatch(s, _return)
        $ sim.tutorial_progress(s, _return)
        jump survival_loop
    if s.get('saved_day') != s['day']:
        $ s['saved_day'] = s['day']
        $ renpy.save('camp')
    call screen hub
    $ cmd = _return
    if cmd[0] == 'night_menu':
        call screen night_menu
        $ cmd = _return
    elif cmd[0] == 'final_menu':
        call screen final_menu
        $ cmd = _return
    elif cmd[0] == 'care_menu':
        call screen care_menu(cmd[1])
        $ cmd = _return
    if cmd[0] != 'cancel':
        $ sim.dispatch(s, cmd)
        $ sim.tutorial_progress(s, cmd)
    jump survival_loop

label before_main_menu:
    play music "audio/ebb.wav" fadein 2.0
    return

label after_load:
    play music "audio/ebb.wav" fadein 1.0
    jump survival_loop
