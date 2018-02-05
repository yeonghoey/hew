#!/usr/bin/env bash

set -euo pipefail

readonly REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

rm -rf "${REPO}/dist"
python "${REPO}/setup.py" bdist_wheel
twine upload "${REPO}/dist/*"
