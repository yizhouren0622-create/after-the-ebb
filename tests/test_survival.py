import sys, copy, pickle, random, json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'game'/'python-packages'))
import survival as g

checks=0
def check(x, msg):
    global checks
    checks+=1
    assert x,msg

def action(s,*cmd):
    check(g.dispatch(s, cmd), 'Action failed: '+str(cmd)+' / '+str((s['day'],s['ap'],s['loc'])))
    while s['pending']:
        opts=[i for i,c in enumerate(s['pending']['choices']) if g.can_choice(s,c)]
        if s['pending'] in g.DISCOVERIES.values() or s['pending']['tag'] != '探索事件': index=opts[0]
        else:
            def score(i):
                c=s['pending']['choices'][i]
                values={'food':5,'raw':3,'fuel':3,'wood':2,'scrap':1,'cloth':1}
                return sum(values.get(k,0)*v for k,v in c['effect'].get('items',{}).items())-sum(values.get(k,0)*v for k,v in c['cost'].items())
            index=max(opts,key=score)
        check(g.choose(s,index), 'Could not resolve authored event')
    check(not s['ending'], 'Premature ending: '+str(s['ending']))

def end_day(s):
    while s['ap']>0:
        if s['talk_day']!=s['day']: action(s,'talk')
        else: action(s,'rest')
    check(g.night(s,1,1), 'Could not feed campaign')
    check(not s['ending'], 'Campaign did not survive night')

def prepare():
    s=g.new_game('tools','standard',916)
    action(s,'craft','shelter'); action(s,'explore'); action(s,'explore'); end_day(s)
    action(s,'travel','town'); action(s,'explore'); action(s,'travel','library'); end_day(s)
    action(s,'explore'); action(s,'explore'); action(s,'travel','clinic'); end_day(s)
    action(s,'explore'); action(s,'craft','coats'); action(s,'travel','relay'); end_day(s)
    # At this point all food came from fixed discoveries and initial pack.
    action(s,'explore'); action(s,'craft','receiver'); action(s,'scan')
    # Cook before ending day 5, with no AP remaining: use next day's action.
    check(g.night(s,.5,.5), 'Day 5 ration'); check(not s['ending'],'Day 5 died')
    action(s,'craft','stove'); action(s,'craft','cook'); action(s,'travel','flats'); end_day(s)
    action(s,'explore'); action(s,'craft','sled'); action(s,'craft','cook'); end_day(s)
    # The maintenance gate opens after the storm. Stockpile at the town camp.
    check(bool(g.travel_reason(s,'tower')), 'Tower opened before day 14')
    action(s,'travel','town'); action(s,'craft','trap'); action(s,'craft','horn'); end_day(s)
    while s['day'] < 14:
        while s['ap']:
            if g.amt(s,'food')<5 and g.amt(s,'raw')>=2 and g.amt(s,'fuel')>=1:
                action(s,'craft','cook')
            elif g.amt(s,'fuel')<2 and g.amt(s,'wood')>=2:
                action(s,'craft','fuel')
            elif s['day'] not in [12,13] and (g.amt(s,'food')<6 or g.amt(s,'wood')<2):
                action(s,'explore')
            elif s['talk_day']!=s['day']:action(s,'talk')
            else:action(s,'rest')
        check(g.night(s,1,1,fire=s['day'] in [12,13] and g.amt(s,'fuel')>=1),'Storm supplies exhausted')
        check(not s['ending'],'Could not survive the storm')
    action(s,'travel','tower'); action(s,'explore')
    return s

s=prepare()
check(all(ok for _,ok in g.true_requirements(s)), 'True ending not reachable: '+str(g.true_requirements(s)))
for key in ['tomorrow','shelter','voice']:
    ss=copy.deepcopy(s)
    if key=='shelter':
        # Collect the guaranteed tower kitchen event, choosing supplies.
        action(ss,'explore')
        if ss['inv']['food']<4 or ss['inv']['fuel']<2:
            ss['ap']=3; action(ss,'explore')
    check(g.finish(ss,key),'Ending unreachable '+key)
    check(ss['ending']==key, 'Incorrect ending '+key)

# Explicit terminal hazards and final deadline.
for field,key in [('hp','lost'),('sanity','drift')]:
    q=g.new_game(); q['crew'][0][field]=0; g.resolve_health(q)
    check(q['ending']==key,'Terminal condition '+field)
q=g.new_game(); q['day']=18; check(g.night(q,1,1),'Deadline night'); check(q['ending']=='silent','Deadline missing')

# Save/restore preserves random sequence and campaign data.
q=g.new_game(seed=123); g.explore(q); g.choose(q,0)
r=pickle.loads(pickle.dumps(q)); check(q==r,'Save round-trip')
g.explore(q);g.explore(r);check(q==r,'RNG diverges after load')

# Weather, invalid input and gating must be enforced by the model too.
q=g.new_game(); before=copy.deepcopy(q)
check(not g.craft(q,'horn') and q==before,'Craft exploited')
check(not g.travel(q,'tower') and q==before,'Map gate bypassed')
check(not g.night(q,99,0) and q==before,'Invalid ration accepted')
q['day']=12; check(not g.explore(q),'Storm exploration allowed')
check(not g.travel(q,'town'),'Storm travel allowed')
q['day']=1;g.explore(q);before=copy.deepcopy(q)
check(not g.choose(q,99) and q==before,'Bad event choice accepted')

# 250 random campaigns stress state boundaries, supplies and pending-event locks.
u=g.new_game()
def guided(*command):
    check(g.dispatch(u,command),'Tutorial action failed '+str(command))
    g.tutorial_progress(u,command)
guided('explore');guided('choose',0);check(u['tutorial']==1,'Tutorial explore not advanced')
u['tab']='bag';u['tutorial']=2
guided('craft','shelter');check(u['tutorial']==3,'Tutorial camp not advanced')
guided('use','food',0);check(u['tutorial']==4,'Tutorial food not advanced')
guided('talk');guided('choose',0);check(u['tutorial']==5,'Tutorial talk not advanced')
guided('night',1,1,False);check(u['tutorial']==6,'Tutorial night not advanced')
guided('travel','town');check(u['tutorial']==7,'Tutorial map not completed')

rr=random.Random(9)
for seed in range(250):
    q=g.new_game(['tools','rations','keepsake'][seed%3],['standard','gentle'][seed%2],seed)
    for _ in range(200):
        if q['ending']:break
        if q['pending']:
            opts=[i for i,c in enumerate(q['pending']['choices']) if g.can_choice(q,c)]
            check(bool(opts),'Softlock: no event choices');g.choose(q,rr.choice(opts))
        else:
            commands=[('rest',),('talk',),('explore',),('scan',),('night',0,0,False)]
            commands += [('craft',k) for k in g.RECIPES]
            commands += [('travel',k) for k in q['unlocked']]
            commands += [('use',item,target) for item in ['food','med'] for target in [0,1]]
            if q['inv']['food']>=2:commands.append(('night',1,1,False))
            g.dispatch(q,rr.choice(commands))
        check(0<=q['ap']<=3,'AP out of bounds')
        check(all(x>=0 for x in q['inv'].values()),'Negative resource')
        check(all(0<=p[f]<=100 for p in q['crew'] for f in ['hp','energy','sanity']),'Crew out of bounds')
result={'checks':checks,'random_campaigns':250,'guaranteed_route_day':s['day'], 'ending_conditions':g.true_requirements(s), 'route_inventory':s['inv'], 'crew':s['crew']}
(root/'tests'/'simulation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
