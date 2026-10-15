"""Convert aligned, locally obtained FLORES files without downloading datasets."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('reference', type=Path)
    parser.add_argument('--src-lang', required=True)
    parser.add_argument('--target-lang', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    sources = args.source.read_text(encoding='utf-8').splitlines()
    references = args.reference.read_text(encoding='utf-8').splitlines()
    if len(sources) != len(references) or not sources:
        parser.error('Aligned files must be nonempty and have identical line counts')
    args.out.write_text('\n'.join(json.dumps({'id': i + 1, 'source': s, 'reference': r,
        'src_lang': args.src_lang, 'target_lang': args.target_lang}, ensure_ascii=False)
        for i, (s, r) in enumerate(zip(sources, references))), encoding='utf-8')


if __name__ == '__main__':
    main()
