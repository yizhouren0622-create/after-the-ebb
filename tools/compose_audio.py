"""Render the original score and Foley with free offline audio tools.

Install tools/requirements-audio.txt, then run this file. Nothing is downloaded
at render time. No samples, soundfonts, models, API keys or paid services.
"""
from pathlib import Path
import json
import math
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt
from pedalboard import Pedalboard, Reverb, HighpassFilter, LowpassFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'game' / 'audio'
SR = 44100
RNG = np.random.default_rng(20261024)
MANIFEST = {'sample_rate': SR, 'tools': {}, 'files': {}}


def db(value):
    return round(float(20 * np.log10(max(value, 1e-12))), 2)


def stats(x):
    return {'duration_seconds': round(len(x) / SR, 4),
            'peak_dbfs': db(np.max(np.abs(x))),
            'rms_dbfs': db(np.sqrt(np.mean(x ** 2, dtype=np.float64)))}


def filt(x, cutoff, kind='lowpass'):
    return sosfilt(butter(2, cutoff, btype=kind, fs=SR, output='sos'), x, axis=0).astype(np.float32)


def noise(seconds, low=120, high=2200):
    x = RNG.standard_normal(round(seconds * SR)).astype(np.float32)
    x = filt(filt(x, low, 'highpass'), high)
    return x / max(np.sqrt(np.mean(x ** 2)), 1e-6)


def stereo(x, pan=0):
    return np.column_stack((x * math.sqrt((1 - pan) / 2),
                            x * math.sqrt((1 + pan) / 2))).astype(np.float32)


def add(bus, sound, start):
    """Circular addition keeps all note and room tails across the loop seam."""
    pos = round(start * SR) % len(bus)
    first = min(len(sound), len(bus) - pos)
    bus[pos:pos + first] += sound[:first]
    if len(sound) > first:
        bus[:len(sound) - first] += sound[first:]


def key(midi, seconds=9, velocity=1):
    t = np.arange(round(seconds * SR), dtype=np.float32) / SR
    frequency = 440 * 2 ** ((midi - 69) / 12)
    x = np.zeros_like(t)
    # Slightly inharmonic, damped partials and a soft felt attack.
    for partial, gain in [(1, 1), (2, .28), (3, .11), (4, .035), (5, .012)]:
        f = frequency * partial * math.sqrt(1 + .000035 * partial ** 2)
        x += gain * np.sin(2 * np.pi * f * t) * np.exp(-t / (3.2 / partial ** .62))
    x *= (1 - np.exp(-t / .027)) * np.minimum(1, (seconds - t) / .8)
    return (x * velocity * .16).astype(np.float32)


def bowed(midi, seconds):
    t = np.arange(round(seconds * SR), dtype=np.float32) / SR
    f = 440 * 2 ** ((midi - 69) / 12)
    envelope = np.sin(np.pi * t / seconds) ** 2
    x = (np.sin(2 * np.pi * f * t + .13 * np.sin(2 * np.pi * .23 * t)) +
         .22 * np.sin(2 * np.pi * f * 2.001 * t) +
         .07 * np.sin(2 * np.pi * f * 3.002 * t))
    return (x * envelope * .027).astype(np.float32)


def save(name, x, peak, description, loop=False):
    x = np.asarray(x, dtype=np.float32)
    if x.ndim == 1:
        x = stereo(x)
    x *= 10 ** (peak / 20) / max(np.max(np.abs(x)), 1e-9)
    path = OUT / name
    options = {'format': 'OGG', 'subtype': 'VORBIS'} if path.suffix == '.ogg' else {'format': 'WAV', 'subtype': 'PCM_16'}
    # Block IO also avoids oversized native stack allocations in libvorbis.
    with sf.SoundFile(path, 'w', samplerate=SR, channels=2, **options) as stream:
        for start in range(0, len(x), 16384):
            stream.write(x[start:start + 16384])
    peak_read, energy, frames, first, last = 0., 0., 0, None, None
    with sf.SoundFile(path) as stream:
        for block in stream.blocks(blocksize=16384, dtype='float32', always_2d=True):
            peak_read = max(peak_read, float(np.max(np.abs(block))))
            energy += float(np.sum(block ** 2, dtype=np.float64))
            frames += len(block)
            if first is None: first = block[0].copy()
            last = block[-1].copy()
    entry = {'duration_seconds': round(frames / SR, 4), 'peak_dbfs': db(peak_read),
             'rms_dbfs': db(np.sqrt(energy / (frames * 2))),
             'description': description, 'channels': 2}
    if loop:
        seam = np.abs(last - first)
        entry['seam_step_dbfs'] = db(np.max(seam))
        assert entry['seam_step_dbfs'] < -52, entry
    assert peak_read < .95, 'Clipping: ' + name
    MANIFEST['files'][name] = entry
    print(name, json.dumps(entry, ensure_ascii=False), flush=True)


def compose():
    print('Composing the 32-bar score...', flush=True)
    beat = 60 / 54
    bar = 4 * beat
    frames = round(32 * bar * SR)
    duration = frames / SR
    keys = np.zeros((frames, 2), dtype=np.float32)
    strings = np.zeros_like(keys)
    # D minor, suspended colours and one unresolved ninth; no triumphant cadence.
    chords = [(38, 45, 53, 64), (34, 41, 53, 57),
              (31, 38, 53, 57), (33, 40, 50, 55),
              (29, 41, 52, 57), (36, 43, 50, 55),
              (34, 41, 53, 60), (33, 40, 55, 58)]
    motifs = [[(0, 62, .9), (1.75, 69, .62), (3, 65, .68)],
              [(.5, 64, .64), (2.5, 62, .7)],
              [(0, 57, .68), (2.25, 62, .65), (3.25, 60, .48)],
              [(1, 57, .55)],
              [(.25, 65, .74), (2, 64, .55), (3.25, 62, .64)],
              [(.5, 60, .58), (2.75, 55, .55)],
              [(0, 57, .66), (2, 62, .59), (3, 64, .46)],
              [(1, 61, .40), (2.75, 57, .50)]]
    for b in range(32):
        if b % 8 == 0: print('Score bar', b + 1, flush=True)
        chord = chords[(b // 2) % 8]
        # Alternating spaces give the melody room; the second half varies it.
        for offset, midi, vel in motifs[b % 8]:
            if b >= 16 and b % 4 == 3:
                midi -= 12
            start = b * bar + offset * beat + float(RNG.uniform(-.025, .025))
            add(keys, stereo(key(midi, velocity=vel), -.16 if b % 2 == 0 else .12), start)
        if b % 2 == 0:
            for j, note in enumerate(chord):
                add(keys, stereo(key(note, 11, .38 if j else .46), (j - 1.5) * .13),
                    b * bar + j * .11)
            for j, note in enumerate(chord[:3]):
                add(strings, stereo(bowed(note, 2.5 * bar), (j - 1) * .34), b * bar - .6)
    # A very quiet, periodic band-limited air layer avoids a dead silent seam.
    air_n = 32768
    air = np.fft.rfft(RNG.standard_normal(air_n))
    f = np.fft.rfftfreq(air_n, 1 / SR)
    air *= np.exp(-(f / 1050) ** 2) * (1 - np.exp(-(f / 160) ** 2))
    air = np.fft.irfft(air).astype(np.float32)
    air /= max(np.std(air), 1e-6)
    room = Pedalboard([HighpassFilter(45), LowpassFilter(5200),
                      Reverb(room_size=.88, damping=.76, wet_level=.34,
                             dry_level=.72, width=.84)])
    # Warm the reverb for a whole cycle, then retain the second complete cycle.
    def process_loop(board, bus):
        chunk = SR
        for start in range(0, len(bus), chunk):
            board(bus[start:start + chunk].T, SR, reset=start == 0)
        for start in range(0, len(bus), chunk):
            bus[start:start + chunk] = board(bus[start:start + chunk].T, SR, reset=False).T
    print('Rendering felt-key room...', flush=True)
    process_loop(room, keys)
    pad_room = Pedalboard([LowpassFilter(1550), Reverb(room_size=.94, damping=.85,
                         wet_level=.6, dry_level=.45, width=.95)])
    print('Rendering bowed room...', flush=True)
    process_loop(pad_room, strings)
    keys += strings
    del strings
    wet = keys
    for start in range(0, frames, SR):
        pos = np.arange(start, min(start + SR, frames), dtype=np.float64)
        air_long = np.interp(pos * air_n * 193 / frames % air_n,
                             np.arange(air_n + 1), np.r_[air, air[0]]).astype(np.float32)
        breath = (.65 + .35 * np.sin(2 * np.pi * pos / frames * 8)).astype(np.float32)
        wet[start:start + len(pos)] += stereo(air_long * breath * .0018)
    # The 8 ms seam correction is below audibility and does not fade the song.
    count = round(.008 * SR)
    delta = wet[0] - wet[-1]
    wet[-count:] += np.linspace(0, 1, count, dtype=np.float32)[:, None] * delta
    print('Encoding music...', flush=True)
    save('where_the_sea_was.ogg', wet, -9,
         'Original 32-bar 54 BPM score: felt keys, bowed low chords and air; D minor. ' +
         'A complete %.3f second seamless loop, without drums or scene changes.' % duration, True)


def burst(seconds, centre, width=.12, amplitude=1):
    t = np.arange(round(seconds * SR)) / SR
    return (np.exp(-((t - centre) / width) ** 2) * amplitude).astype(np.float32)


def foley():
    # Foley is filtered and quieter than the score peaks. No hover beep.
    t = np.arange(round(.22 * SR)) / SR
    click = (np.sin(2 * np.pi * 370 * t) + .15 * np.sin(2 * np.pi * 740 * t))
    click *= (1 - np.exp(-t / .004)) * np.exp(-t / .035)
    click *= np.minimum(1, (.22 - t) / .03)
    save('ui_confirm.wav', click, -26, 'Soft felt/wood confirmation, activation only.')

    x = noise(1.6, 170, 2100)
    x *= burst(1.6, .35, .20) + burst(1.6, .91, .26, .72) + burst(1.6, 1.32, .11, .4)
    save('search.wav', x, -20, 'Gloved hands moving cloth and sorting supplies.')

    t = np.arange(round(1.8 * SR)) / SR
    x = noise(1.8, 95, 1400) * (burst(1.8, .3, .10) + burst(1.8, .87, .11, .9) + burst(1.8, 1.43, .11, .72))
    x += np.sin(2 * np.pi * 105 * t) * (burst(1.8, .29, .035) + burst(1.8, .86, .035, .7)) * .23
    save('footsteps.wav', x, -21, 'Three muffled steps over salt and gravel.')

    t = np.arange(round(1.5 * SR)) / SR
    x = noise(1.5, 230, 1800) * (burst(1.5, .24, .13) + burst(1.5, .82, .20, .7)) * .22
    for start in [.20, .58, 1.05]:
        tt = np.maximum(t - start, 0)
        x += ((t >= start) * np.exp(-tt * 24) * (1 - np.exp(-tt * 320)) *
              (np.sin(2 * np.pi * 435 * tt) + .27 * np.sin(2 * np.pi * 913 * tt))) * .28
    save('craft.wav', x, -23, 'Damped wood and metal assembly; no sharp hammer hits.')

    x = noise(1.4, 100, 1500) * (burst(1.4, .35, .23) + burst(1.4, .92, .22, .7))
    save('cloth.wav', x, -24, 'Soft cloth tension for sewing, camp and bandages.')
    x = noise(1.7, 150, 1900) * (burst(1.7, .4, .26) + burst(1.7, 1.09, .24, .8))
    save('eat.wav', x, -24, 'Unwrapping a ration and handling a cup, without eating closeups.')

    seconds = 2.6
    t = np.arange(round(seconds * SR)) / SR
    env = np.sin(np.pi * t / seconds) ** 1.5
    x = noise(seconds, 130, 1700) * env * .32
    for centre in [.32, .67, 1.02, 1.6, 2.02]:
        x += noise(seconds, 400, 2600) * burst(seconds, centre, .018, .13) * env
    save('fire.wav', x, -23, 'A restrained stove flame and soft embers.')

    t = np.arange(round(1.9 * SR)) / SR
    x = noise(1.9, 180, 1400) * np.sin(np.pi * t / 1.9) ** 2
    x *= .25 + .13 * np.sin(2 * np.pi * 5.3 * t)
    x += .12 * np.sin(2 * np.pi * (290 * t + 32 * t ** 2)) * burst(1.9, .9, .35)
    save('radio.wav', x, -25, 'Band-limited receiver tuning, with no piercing static.')

    x = noise(1.0, 300, 2300) * (burst(1., .25, .11) + burst(1., .62, .16, .5))
    save('page.wav', x, -25, 'Turning and smoothing a notebook page.')
    x = noise(2.2, 100, 1000) * burst(2.2, .8, .48)
    save('rest.wav', x, -26, 'A blanket settling while the pair take shelter.')


def main():
    import pedalboard, scipy
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST['tools'] = {'numpy': np.__version__, 'scipy': scipy.__version__,
                         'soundfile': sf.__version__, 'pedalboard': pedalboard.__version__}
    compose()
    foley()
    (ROOT / 'tests' / 'audio-manifest.json').write_text(
        json.dumps(MANIFEST, ensure_ascii=False, indent=2) + '\n', 'utf-8')


if __name__ == '__main__':
    main()
