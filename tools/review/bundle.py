"""Bundle reviewer JSON files into the app's review page.

python3 tools/review/bundle.py docs/animation-review/<revision>

Copies review-form.json, review-visuals.json and review-anatomy.json (whichever
exist) into src/animation/reviews.json, which the /debug/animations page shows.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    root = Path(sys.argv[1])
    reviewers = []
    for role in ('form', 'visuals', 'anatomy'):
        path = root / f'review-{role}.json'
        if path.exists():
            reviewers.append(json.loads(path.read_text()))
    bundle = {'revision': root.name, 'reviewers': reviewers}
    (ROOT / 'src/animation/reviews.json').write_text(json.dumps(bundle, indent=1) + '\n')
    print(f'{len(reviewers)} reviews bundled for {root.name}')


if __name__ == '__main__':
    main()
