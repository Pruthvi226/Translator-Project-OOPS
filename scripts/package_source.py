"""Create a source-only handoff, excluding credentials, runtimes and user data."""
from pathlib import Path
import os
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = {'backend', 'frontend', 'evaluation', 'tests', 'deployment', 'docs',
               'scripts', 'templates', 'static', '.github', 'AI-Translator-Pro'}
FILES = {'app.py', 'README.md', 'Dockerfile', 'docker-compose.yml', 'pyproject.toml',
         '.gitignore', '.dockerignore', '.env.example'}
SKIP = {'node_modules', 'dist', '__pycache__', '.pytest_cache', '.ruff_cache',
        'test-results', 'playwright-report', 'results'}


def main():
    output = ROOT / 'artifacts' / 'fluentflow-ai-source.zip'
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        paths = [ROOT / name for name in FILES]
        paths.extend(ROOT.glob('requirements*.txt'))
        paths.extend(ROOT.glob('requirements*.lock'))
        for name in sorted(DIRECTORIES):
            for parent, folders, files in os.walk(ROOT / name):
                folders[:] = [folder for folder in folders if folder not in SKIP
                              and not (Path(parent) / folder).is_symlink()]
                paths.extend(Path(parent) / filename for filename in files)
        for path in sorted(set(paths)):
            relative = path.relative_to(ROOT)
            if path.is_symlink() or not path.is_file() or any(p in SKIP for p in relative.parts):
                continue
            if not (relative.parts[0] in DIRECTORIES or str(relative) in FILES
                    or (len(relative.parts) == 1 and path.name.startswith('requirements')
                        and path.suffix in {'.txt', '.lock'})):
                continue
            if path.name.startswith('.env') and path.name != '.env.example':
                continue
            if path.suffix.lower() in {'.db', '.mp3', '.wav', '.jsonl', '.log', '.pyc'}:
                continue
            archive.write(path, relative.as_posix())
    print(f'Created {output.name} ({output.stat().st_size:,} bytes), with no environment secrets or runtime data.')


if __name__ == '__main__':
    main()
