# Copied into game/ temporarily by tools/test_engine.py; excluded from builds.
init 100 python:
    from renpy.test.testsettings import _test
    _test.timeout = 50.0
    _test.focus_trials = 5
    _test.screenshot_directory = 'tests/screenshots-1.2'

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
