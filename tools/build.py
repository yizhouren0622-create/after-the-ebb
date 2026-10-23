"""Build native Ren'Py desktop archives without unpacking or repacking them."""
import argparse
import os
from pathlib import Path
import platform
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sdk', required=True, type=Path)
    parser.add_argument('--out', default='dist', type=Path)
    args = parser.parse_args()
    sdk = args.sdk.expanduser().resolve()
    project = Path(__file__).resolve().parents[1]
    destination = args.out.expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    system = platform.system()
    if system == 'Windows':
        runtime = sdk / 'lib' / 'py3-windows-x86_64' / 'python.exe'
    elif system == 'Darwin':
        runtime = sdk / 'lib' / 'py3-mac-universal' / 'python'
    else:
        candidates = sorted((sdk / 'lib').glob('py3-linux-*/python'))
        machine = platform.machine().lower()
        preferred = 'aarch64' if machine in ('arm64', 'aarch64') else 'x86_64'
        runtime = next((p for p in candidates if preferred in str(p)), sdk / 'lib' / 'py3-linux-x86_64' / 'python')
    if not runtime.is_file():
        raise SystemExit('SDK runtime not found: ' + str(runtime))
    base = [str(runtime), str(sdk / 'renpy.py')]
    env = dict(os.environ, RENPY_LANGUAGE='english')
    distribute = base + [str(sdk / 'launcher'), 'distribute', str(project),
                         '--destination', str(destination), '--no-update']
    log = project / 'tests' / 'build.log'
    with log.open('w', encoding='utf-8') as output:
        for label, command in [
            ('Checking RenPy scripts...', base + [str(project), 'lint']),
            ('Building Windows and Linux archives...', distribute + ['--package', 'win', '--package', 'linux']),
            ('Building universal macOS archive...', distribute + ['--package', 'mac', '--format', 'app-zip']),
        ]:
            print(label, flush=True)
            subprocess.run(command, check=True, env=env, stdout=output, stderr=subprocess.STDOUT)
    print('Desktop packages built in ' + str(destination), flush=True)


if __name__ == '__main__':
    main()
