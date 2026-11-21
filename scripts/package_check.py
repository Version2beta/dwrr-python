#!/usr/bin/env python3
"""Complete; do not change. No publication. Build in temp, install outside checkout.

Defaults to local offline build tools; CI supplies explicit public tool paths.
Build dependencies are dev-only. Judge performs no network access.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BUILD = Path(os.environ.get('DWRR_BUILD_PYTHON', ROOT / '.venv/bin/python')).absolute()
WHEELS = Path(os.environ.get('DWRR_BUILD_WHEELS', ROOT / '.loop/build-wheels')).resolve()


def command(args, cwd):
    env = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH', 'PYTHONHOME')}
    env.update(PIP_NO_INDEX='1', PIP_DISABLE_PIP_VERSION_CHECK='1', PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run([str(a) for a in args], cwd=cwd, env=env, capture_output=True, text=True, timeout=90)
    if result.returncode:
        raise AssertionError(f'command failed: {args}\n{result.stdout}\n{result.stderr}')
    return result.stdout


def main():
    readme = (ROOT / 'README.md').read_text()
    examples = re.findall(r'```python\n(.*?)```.*?```text\n(.*?)```', readme, re.S)
    assert len(examples) == 2, 'README must retain both executable histories'
    assert list(WHEELS.glob('setuptools-*.whl')), 'prepare offline build wheels first'
    with tempfile.TemporaryDirectory(prefix='dwrr-package-') as tmp:
        tmp = Path(tmp)
        source = tmp / 'source'
        source.mkdir()
        for name in ('pyproject.toml', 'MANIFEST.in', 'LICENSE', 'README.md', 'SPEC.md'):
            shutil.copy2(ROOT / name, source / name)
        shutil.copytree(ROOT / 'dwrr', source / 'dwrr', ignore=shutil.ignore_patterns('__pycache__'))
        command([BUILD, '-m', 'build', '--no-isolation', '--outdir', tmp / 'artifacts', source], tmp)
        wheel, = (tmp / 'artifacts').glob('*.whl')
        sdist, = (tmp / 'artifacts').glob('*.tar.gz')
        with zipfile.ZipFile(wheel) as archive:
            names = archive.namelist()
            assert all(n.startswith(('dwrr/', 'dwrr_python-0.1.0.dist-info/')) for n in names), names
            metadata = archive.read('dwrr_python-0.1.0.dist-info/METADATA').decode()
            assert 'Requires-Python: >=3.11' in metadata and 'Requires-Dist:' not in metadata
            assert 'License-Expression: MIT' in metadata
        with tarfile.open(sdist) as archive:
            names = archive.getnames()
            assert not any(any(part in n for part in ('private-reference', '/vendor/', '/tests/', '/scripts/', '/.loop/', '/.git/')) for n in names), names
            assert any(n.endswith('/LICENSE') for n in names)
            assert any(n.endswith('/dwrr/_engine.py') for n in names)
        print('PASS archives: pure Python wheel and sdist, MIT, no runtime dependencies')
        for origin, artifact in [('wheel', wheel), ('sdist', sdist), ('checkout', source)]:
            venv = tmp / ('env-' + origin)
            command([sys.executable, '-m', 'venv', venv], tmp)
            python = venv / 'bin/python'
            if origin != 'wheel':
                command([python, '-m', 'pip', 'install', '--no-index', '--find-links', WHEELS, 'setuptools>=77', 'wheel'], tmp)
            command([python, '-m', 'pip', 'install', '--no-deps', '--no-build-isolation', artifact], tmp)
            for code, expected in examples:
                actual = command([python, '-I', '-c', code], tmp)
                assert actual == expected, (origin, actual, expected)
            location = command([python, '-I', '-c', 'import dwrr; print(dwrr.__file__)'], tmp).strip()
            assert str(venv) in location and str(ROOT) not in location, location
            print('PASS isolated install and README examples: ' + origin)
    print('PASS package checks')


if __name__ == '__main__':
    main()
