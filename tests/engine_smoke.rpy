# Copied into game/ temporarily by tools/test_engine.py; excluded from builds.
init 100 python:
    from renpy.test.testsettings import _test
    _test.timeout = 50.0
    _test.focus_trials = 5
    _test.screenshot_directory = 'tests/screenshots-1.3'

screen _qa_command(command):
    timer .02 action [Hide('_qa_command'), Return(command)]

testcase feedback_release:
    run Start('begin_tools_standard')
    pause until screen 'story_event'
    run Show('_qa_command', command=('choose', 0))
    pause until screen 'action_result'
    pause .4
    screenshot '01-intro-result.png'
    assert eval (s['inv']['food'] == 6 and s['ap'] == 3)
    assert eval (renpy.music.get_playing() == 'audio/where_the_sea_was.ogg')
    run Show('_qa_command', command=True)
    pause until screen 'hub'
    pause .3
    screenshot '00-hub-before-exploration.png'
    run Show('_qa_command', command=('explore',))
    pause until screen 'story_event'
    run Show('_qa_command', command=('choose', 0))
    pause until screen 'action_result'
    pause .4
    screenshot '02-explore-result.png'
    assert eval (s['inv']['raw'] == 3 and s['ap'] == 2)
    assert eval (s['crew'][0]['energy'] == 75)
    run FileLoad('journey', confirm=False, slot=True)
    pause until screen 'action_result'
    assert eval (s['inv']['raw'] == 3 and s['ap'] == 2)
    run Show('_qa_command', command=True)
    pause until screen 'hub'
    run Show('action_result', report=s['last_feedback'], reviewing=True)
    pause until screen 'action_result'
    pause .4
    screenshot '03-review-result.png'
    run Hide('action_result')
    pause until screen 'hub'
    run Show('_qa_command', command=('craft', 'shelter'))
    pause until screen 'action_result'
    pause .4
    screenshot '04-camp-result.png'
    assert eval ('shelter' in s['gear'] and s['ap'] == 1)
    assert eval (s['inv']['wood'] == 2 and s['inv']['cloth'] == 1)
    run Show('_qa_command', command=True)
    pause until screen 'hub'
    run Show('_qa_command', command=('use', 'food', 0))
    pause until screen 'action_result'
    assert eval (s['inv']['food'] == 5 and s['ap'] == 1)
    run Show('_qa_command', command=True)
    pause until screen 'hub'
    run Show('_qa_command', command=('talk',))
    pause until screen 'story_event'
    run Show('_qa_command', command=('choose', 0))
    pause until screen 'action_result'
    pause .4
    screenshot '05-conversation-result.png'
    assert eval (s['feedback']['figures'] is True and s['ap'] == 0)
    run Show('_qa_command', command=True)
    pause until screen 'hub'
    run Show('_qa_command', command=('night_menu',))
    pause until screen 'night_menu'
    run Show('_qa_command', command=('night', .5, 1, True))
    pause until screen 'action_result'
    pause .4
    screenshot '06-night-result.png'
    assert eval (s['day'] == 2 and s['ap'] == 3 and s['inv']['food'] == 3.5)
    assert eval (s['inv']['fuel'] == 1)
    run FileLoad('journey', confirm=False, slot=True)
    pause until screen 'action_result'
    assert eval (s['day'] == 2 and s['inv']['food'] == 3.5)
    run Show('_qa_command', command=True)
    pause until screen 'hub'
    assert eval (s['day'] == 2 and s['inv']['food'] == 3.5)
    assert eval (renpy.music.get_playing() == 'audio/where_the_sea_was.ogg')
    $ s['inv']['med'] = 1
    $ s['crew'][0]['hp'] = 98
    $ s['crew'][0]['hurt'] = True
    run Show('_qa_command', command=('care_menu', 0))
    pause until screen 'care_menu'
    run Show('_qa_command', command=('use', 'med', 0))
    pause until screen 'action_result'
    pause .4
    screenshot '07-treatment-result.png'
    assert eval (s['crew'][0]['hp'] == 100 and not s['crew'][0]['hurt'])
    assert eval (s['inv']['med'] == 0)

testcase knowledge_achievements_release:
    run Start('begin_tools_standard')
    pause until screen 'story_event'
    run Show('_qa_command', command=('choose', 0))
    pause until screen 'action_result'
    run Show('_qa_command', command=True)
    pause until screen 'hub'
    assert eval (renpy.get_widget('hub', 'knowledge_aid') is not None)
    $ renpy.session['qa_story_seed'] = s['seed']
    run Show('_qa_command', command=('aid_menu',))
    pause until screen 'knowledge_supply'
    pause .3
    screenshot '10-aid-supplies.png'
    run Show('_qa_command', command=('quiz_start', 'med'))
    pause until screen 'knowledge_question'
    $ renpy.session['qa_original_quiz'] = dict(s['quiz'])
    pause .3
    screenshot '11-question.png'
    run FileLoad('journey', confirm=False, slot=True)
    pause until screen 'knowledge_question'
    assert eval (s['quiz'] == renpy.session['qa_original_quiz'])
    $ wrong_index = next(i for i, index in enumerate(s['quiz']['order']) if index != aid.BY_ID[s['quiz']['id']]['correct'])
    run Show('_qa_command', command=('quiz_answer', s['quiz']['token'], wrong_index))
    pause until screen 'action_result'
    assert eval (s['inv']['med'] == 0 and s['day'] == 1 and s['ap'] == 3)
    assert eval (s['seed'] == renpy.session['qa_story_seed'] and s['knowledge'] == 0 and s['bond'] == 48)
    assert eval (not s['quiz_last_result']['correct'])
    pause .3
    screenshot '12-wrong-no-penalty.png'
    run Show('_qa_command', command=('quiz_retry', 'med'))
    pause until screen 'knowledge_question'
    assert eval (s['quiz']['id'] != renpy.session['qa_original_quiz']['id'])
    $ right_index = s['quiz']['order'].index(aid.BY_ID[s['quiz']['id']]['correct'])
    run Show('_qa_command', command=('quiz_answer', s['quiz']['token'], right_index))
    pause until screen 'action_result'
    assert eval (s['inv']['med'] == 1 and s['quiz_last_result']['correct'])
    assert eval (s['day'] == 1 and s['ap'] == 3 and s['seed'] == renpy.session['qa_story_seed'])
    pause .3
    screenshot '13-correct-reward.png'
    run FileLoad('journey', confirm=False, slot=True)
    pause until screen 'action_result'
    assert eval (s['inv']['med'] == 1 and s['quiz'] is None)
    run Show('_qa_command', command=True)
    pause until screen 'hub'
    $ s['inv'].update(aid.LIMITS)
    run Show('_qa_command', command=('aid_menu',))
    pause until screen 'knowledge_supply'
    pause .3
    screenshot '14-full-bundles.png'
    assert eval (not aid.shortfalls(s))
    run Show('_qa_command', command=('cancel',))
    pause until screen 'hub'
    $ s['crew'][0]['hp'] = 4
    run Show('_qa_command', command=('use', 'food', 1))
    pause until screen 'action_result'
    assert eval ('edge' in persistent.achievements)
    run Show('_qa_command', command=True)
    pause until screen 'hub'
    run Hide('achievement_toast')
    run Show('achievement_archive')
    pause until screen 'achievement_archive'
    pause .3
    screenshot '15-achievements-top.png'
    run Function(renpy.get_widget('achievement_archive', 'achievement_list').yadjustment.change, 700)
    pause .3
    screenshot '16-achievements-progress.png'
    assert eval (persistent.achievement_best['edge'] == 1)
    run Hide('achievement_archive')
    run Jump('begin_tools_gentle')
    pause until screen 'story_event'
    assert eval ('edge' in persistent.achievements)
    run Show('_qa_command', command=('choose', 0))
    pause until screen 'action_result'
    run Show('_qa_command', command=True)
    pause until screen 'hub'
    assert eval (renpy.get_widget('hub', 'knowledge_aid') is None)
    assert eval (renpy.music.get_playing() == 'audio/where_the_sea_was.ogg')
