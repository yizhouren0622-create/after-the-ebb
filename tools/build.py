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
    subprocess.run(base + [str(project), 'lint'], check=True, env=env)
    distribute = base + [str(sdk / 'launcher'), 'distribute', str(project),
                         '--destination', str(destination), '--no-update']
    subprocess.run(distribute + ['--package', 'win', '--package', 'linux'], check=True, env=env)
    subprocess.run(distribute + ['--package', 'mac', '--format', 'app-zip'], check=True, env=env)


if __name__ == '__main__':
    main()
