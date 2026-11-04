"""Run Ren'Py's own screen/action tests, using isolated saves and input events."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import queue
import threading
import time
import re


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--case', default='feedback_release',
                        choices=['feedback_release', 'knowledge_achievements_release', 'storybook_release'])
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sdk = args.sdk.resolve()
    version = re.search(r'config.version = "([^"]+)"', (root / 'game' / 'options.rpy').read_text('utf-8')).group(1)
    candidates = list((sdk / 'lib').glob('py3-*/python.exe'))
    candidates += list((sdk / 'lib').glob('py3-*/python'))
    runtime = next(p for p in candidates if ('windows' in str(p)) == (os.name == 'nt'))
    target = root / 'game' / '_release_test.rpy'
    if target.exists():
        raise SystemExit('Refusing to overwrite ' + str(target))
    target.write_text((root / 'tests' / 'engine_smoke.rpy').read_text('utf-8').replace(
        '@VERSION@', version), 'utf-8')
    try:
        process = subprocess.Popen([str(runtime), str(sdk / 'renpy.py'), str(root), 'test',
                        args.case, '--overwrite-screenshots', '--report-detailed',
                        '--savedir', str(root / 'tests' / 'engine-saves')],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env=dict(os.environ, PYTHONIOENCODING='utf-8'))
        lines = queue.Queue()
        def reader():
            for line in iter(process.stdout.readline, b''):
                lines.put(line.decode('utf-8', errors='replace').rstrip('\r\n') + '\n')
        threading.Thread(target=reader, daemon=True).start()
        deadline = time.monotonic() + 120
        passed = False
        transcript = []
        try:
            while time.monotonic() < deadline:
                try:
                    line = lines.get(timeout=.2)
                except queue.Empty:
                    if process.poll() is not None: break
                    continue
                transcript.append(line)
                print(line, end='', flush=True)
                if '[rpytest] Status:' in line:
                    passed = line.strip().endswith('PASSED')
                    break
        finally:
            if process.poll() is None: process.terminate()
            process.wait(timeout=10)
            (root / 'tests' / 'engine-validation.log').write_text(''.join(transcript), 'utf-8')
        if not passed: raise SystemExit('Engine screen test failed; see tests/engine-validation.log')
        knowledge_case = args.case == 'knowledge_achievements_release'
        story_case = args.case == 'storybook_release'
        result_name = 'engine-storybook-validation.json' if story_case else 'engine-knowledge-validation.json' if knowledge_case else 'engine-validation.json'
        scope = (['saved question and answer order', 'wrong answer without penalty',
                  'retry and deficit-only reward', 'full emergency supplies',
                  'achievement archive and cross-campaign persistence', 'gentle mode excludes aid']
                 if knowledge_case else
                 ['actual result screens', 'music channel playing', 'automatic save reload',
                  'no duplicate exploration rewards', 'no duplicate night costs',
                  'inline craft and food results, reload without repeating costs',
                  'review without actions', 'treatment clamped at 100'])
        if story_case:
            scope = ['new region backgrounds in actual engine', 'one-time story branch save reload',
                     'reading archive and seen choices', 'real night preview',
                     'title SVG objects for all achievements', 'keepsake detail', 'simplified craft page',
                     'stocked bag items, storm countdown, inline rest and travel',
                     'opening broadcast and ticket machine cues']
        (root / 'tests' / result_name).write_text(json.dumps({
            'status': 'PASSED', 'version': version, 'test_selection': args.case,
            'assertions': int(re.search(r'Assertions\s*:\s*(\d+)', ''.join(transcript)).group(1)),
            'method': 'RenPy internal timed screen events, isolated save directory',
            'screenshots': sorted(p.name for p in (root / 'tests' / ('screenshots-' + version)).glob('*.png')
                                  if (int(p.name[:2]) // 10) in ({2, 3} if story_case else {1} if knowledge_case else {0})),
            'scope': scope
        }, indent=2) + '\n', 'utf-8')
    finally:
        target.unlink(missing_ok=True)
        target.with_suffix('.rpyc').unlink(missing_ok=True)


if __name__ == '__main__':
    main()
