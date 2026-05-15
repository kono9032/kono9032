#!/bin/bash
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install markdownlint-cli for README linting
if ! command -v markdownlint &> /dev/null; then
  npm install -g markdownlint-cli
fi
