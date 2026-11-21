"""Exercise the post-kit guard in disposable tracked copies, never this tree."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    names = subprocess.check_output(
        ['git', 'ls-files', '-co', '--exclude-standard', '--deduplicate'],
        cwd=ROOT, text=True).splitlines()
    with tempfile.TemporaryDirectory(prefix='dwrr-integrity-') as tmp:
        root = Path(tmp)
        for name in names:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        subprocess.run(['git', 'init', '-q', str(root)], check=True)

        def check(ok):
            result = subprocess.run([sys.executable, '-B', 'scripts/kit_check.py'],
                                    cwd=root, capture_output=True, text=True)
            assert (result.returncode == 0) == ok, result.stdout + result.stderr

        check(True)
        # Cover frozen behavior, evolved docs, workflow, baseline and extra paths.
        for name in ('tests/test_state.py', 'README.md', '.github/workflows/ci.yml',
                     'kit-manifest.json', 'ci/post-kit.json'):
            path = root / name
            saved = path.read_bytes()
            path.write_bytes(saved + b'\n# unauthorized drift\n')
            check(False)
            path.write_bytes(saved)
        extra = root / 'unexpected.txt'
        extra.write_text('not inventoried\n')
        check(False)
        extra.unlink()
        check(True)
    print('PASS post-kit guard: clean copy and six unauthorized mutations')


if __name__ == '__main__':
    main()
