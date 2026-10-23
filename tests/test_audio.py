"""Decode final assets and check level matching, tails and the loop seam.

Uses the optional offline audio requirements, never imported by the game.
"""
import json
from pathlib import Path
import sys
import wave
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'tests' / 'audio-manifest.json').read_text('utf-8'))
measured = {}
checks = 0


def check(ok, message):
    global checks
    checks += 1
    assert ok, message


for name, expected in manifest['files'].items():
    path = ROOT / 'game' / 'audio' / name
    peak, total, energy, first, last = 0., 0, 0., None, None
    with sf.SoundFile(path) as stream:
        check(stream.samplerate == 44100 and stream.channels == 2, 'Bad audio format')
        for block in stream.blocks(blocksize=16384, dtype='float32', always_2d=True):
            check(np.all(np.isfinite(block)), 'Invalid audio samples')
            peak = max(peak, float(np.max(np.abs(block))))
            energy += float(np.sum(block ** 2, dtype=np.float64))
            total += len(block)
            if first is None: first = block[0].copy()
            last = block[-1].copy()
    peak_db = float(20 * np.log10(max(peak, 1e-12)))
    check(peak < .9, 'Clipped audio: ' + name)
    check(abs(peak_db - expected['peak_dbfs']) < .02, 'Changed audio levels')
    check(abs(total / 44100 - expected['duration_seconds']) < .001, 'Wrong duration')
    check(energy > 0, 'Silent audio')
    measured[name] = {'peak_dbfs': round(peak_db, 2), 'seconds': round(total / 44100, 4)}
    if name.endswith('.ogg'):
        seam_db = float(20 * np.log10(max(np.max(np.abs(last - first)), 1e-12)))
        check(120 < total / 44100 < 180, 'Score is not the intended full piece')
        check(seam_db < -52, 'Audible loop edge')
        measured[name]['seam_dbfs'] = round(seam_db, 2)
    else:
        with wave.open(str(path)) as wav:
            check(wav.getsampwidth() == 2, 'RenPy requires signed 16-bit PCM WAV')
        check(np.max(np.abs(first)) < .001 and np.max(np.abs(last)) < .001, 'Hard sound edge')

music_peak = measured['where_the_sea_was.ogg']['peak_dbfs']
for name, values in measured.items():
    if name.endswith('.wav'):
        check(values['peak_dbfs'] < music_peak - 10, 'Foley too loud relative to music')
peak_sum = sum(10 ** (measured[name]['peak_dbfs'] / 20)
               for name in ['where_the_sea_was.ogg', 'search.wav', 'ui_confirm.wav'])
check(peak_sum < .9, 'Full-volume music/Foley/UI mix could clip')
script = (ROOT / 'game' / 'options.rpy').read_text('utf-8')
check('hover_sound' not in script and 'activate_sound' in script, 'Hover noise regression')
check("register_channel('foley', mixer='sfx'" in script, 'Foley shares UI interruptions')
check('if_changed=True' in script, 'Same music restarts after actions')
result = {'checks': checks, 'files': measured, 'full_volume_peak_bound': round(peak_sum, 4),
          'seam_checked_after_ogg_decode': True}
(ROOT / 'tests' / 'audio-validation.json').write_text(json.dumps(result, indent=2) + '\n', 'utf-8')
print(json.dumps(result, indent=2))
