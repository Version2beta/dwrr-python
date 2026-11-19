#!/usr/bin/env python3
"""Complete; do not change. Non-writing incremental-safe kit integrity/effects guard.

Not a sandbox or proof of correctness. Protected tests and mandatory source review
supply behavioral assurance. This guard must not require unfinished later tasks.
"""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
EDITABLE = {'dwrr/_engine.py', 'scripts/_adapter.py', 'PROGRESS.md'}
ALLOWED = {'typing', 'collections', 'dataclasses', '_contracts', '_state', 'dwrr', 'scripts.wire'}
FORBIDDEN = {'open', 'print', 'input', 'eval', 'exec', 'compile', '__import__', 'exit', 'quit',
             'set_int_max_str_digits', 'getenv', 'system', 'popen', 'read_text', 'read_bytes'}


def main():
    manifest = json.loads((ROOT / 'kit-manifest.json').read_text())
    files = subprocess.check_output(['git', 'ls-files', '-co', '--exclude-standard', '--deduplicate'], cwd=ROOT, text=True).splitlines()
    allowed_paths = set(manifest['sha256']) | EDITABLE | {'kit-manifest.json'}
    assert set(files) <= allowed_paths, 'unapproved kit paths: ' + repr(sorted(set(files) - allowed_paths))
    for name, digest in manifest['sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, 'protected file changed: ' + name
    for folder in ('dwrr', 'scripts', 'tests'):
        for path in (ROOT / folder).glob('*.py'):
            text = path.read_text()
            assert text.endswith('\n') and all(line == line.rstrip() for line in text.splitlines()), 'format: ' + str(path)
            tree = ast.parse(text, str(path))
            if path.relative_to(ROOT).as_posix() not in EDITABLE:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    assert all(alias.name in ALLOWED for alias in node.names), 'unsupported core/adapter import'
                if isinstance(node, ast.ImportFrom):
                    assert node.module in ALLOWED, 'unsupported core/adapter import: ' + str(node.module)
                if isinstance(node, ast.Name):
                    assert node.id not in FORBIDDEN, 'forbidden external effect: ' + node.id
                if isinstance(node, ast.Attribute):
                    assert node.attr not in FORBIDDEN, 'forbidden external effect: ' + node.attr
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    assert not any(marker in node.value for marker in ('vendor/', 'tests/', 'private-reference', 'spec_model')), 'fixture/fallback dependency'
    print('PASS kit integrity, syntax, format and external-effect guard')


if __name__ == '__main__':
    main()
