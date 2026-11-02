screen title_keepsakes():
    $ souvenirs = keepsakes.unlocked(persistent.achievements)
    if souvenirs:
        # A cloth laid in the foreground; objects accumulate across journeys.
        add Solid('#080b0cba') xpos 690 ypos 595 xysize (880, 270)
        for i, row in enumerate(souvenirs):
            $ slot = next(j for j, item in enumerate(keepsakes.OBJECTS) if item[0] == row[0])
            button:
                id ('keepsake_' + row[0])
                xpos (710 + (slot % 4) * 211) ypos (603 + (slot // 4) * 125)
                xysize (203, 122) padding (2, 1) background None hover_background Solid('#c6d0c018')
                action Show('keepsake_detail', row=row)
                add ('images/keepsakes/' + row[0] + '.svg') xysize (170, 121) xalign .5
        text ('行李旁留下的东西  %d / 8  /  点击查看' % len(souvenirs)) xpos 716 ypos 868 size 17 color INK

screen keepsake_detail(row):
    modal True
    key 'K_ESCAPE' action Hide('keepsake_detail')
    add Solid('#000000dd')
    frame:
        xalign .5 yalign .5 xsize 840 background bordered('#000000') padding (40, 30)
        vbox:
            spacing 20
            add ('images/keepsakes/' + row[0] + '.svg') xysize (330, 255) xalign .5
            text row[1] size 34 xalign .5
            text row[4] xsize 750 size 25 line_spacing 10
            text ('留下它的经历：' + row[3]) size 20 color MUTED xsize 750
            textbutton '放回行李旁' xsize 750 text_xalign .5 action Hide('keepsake_detail')

screen story_archive():
    modal True
    default region = 'shore'
    default selected = None
    key 'K_ESCAPE' action Hide('story_archive')
    add Solid('#000000f5')
    frame:
        xpos 65 ypos 40 xysize (1470, 820) background bordered('#000000') padding (28, 22)
        vbox:
            spacing 14
            text '拾到的片段' size 36
            text ('记录了 %d 个场景、%d 条选项后续。换一段旅途，可以回来寻找另一个经过。' % (len(persistent.story_records), keepsakes.total_choices(persistent.story_records))) size 21 color MUTED
            hbox:
                spacing 6
                for key in sim.ORDER + ['camp']:
                    textbutton ('营火旁' if key == 'camp' else sim.PLACES[key][0]):
                        text_size 18 padding (12, 9)
                        selected region == key
                        action [SetScreenVariable('region', key), SetScreenVariable('selected', None)]
            hbox:
                spacing 24
                viewport:
                    xysize (410, 555) child_size (390, None) mousewheel True draggable True
                    vbox:
                        spacing 10
                        $ entries = keepsakes.region_records(persistent.story_records, region)
                        if not entries:
                            text '这里还没有记录。\n走到那里，调查或交谈后再回来。' size 24 xsize 370 color MUTED
                        for entry in entries:
                            button:
                                xsize 390 padding (16, 12)
                                action SetScreenVariable('selected', entry['title'])
                                vbox:
                                    spacing 6
                                    text entry['title'] size 24
                                    text ('已选 %d / %d 条后续' % (len(entry['results']), len(entry['choices']))) size 18 color RUST
                viewport:
                    xysize (975, 555) child_size (940, None) mousewheel True draggable True
                    vbox:
                        spacing 18
                        if selected and selected in persistent.story_records:
                            $ entry = persistent.story_records[selected]
                            text entry['title'] size 32
                            text entry['text'] size 24 xsize 920 line_spacing 10
                            for index, label in enumerate(entry['choices']):
                                if str(index) in entry['results']:
                                    text ('选择：' + label) size 23 color RUST
                                    text entry['results'][str(index)] size 24 xsize 920
                                else:
                                    text '另一条后续尚未记录' size 21 color MUTED
                        else:
                            text '从左侧选一个片段。\n这里只收录实际经历过的内容。' size 27 color MUTED ypos 70
            textbutton '返回' xsize 1400 text_xalign .5 action Hide('story_archive')
