#!/bin/bash
set -e

echo "Preparing NLTK tokenizer data..."
python -c "
import nltk
for pkg in ('punkt', 'punkt_tab'):
    try:
        nltk.download(pkg, quiet=False)
        print(f'Downloaded {pkg}')
    except Exception as e:
        print(f'Warning: could not download {pkg}: {e}')
"

echo "Starting Smart1SummaryBot..."
exec python bot.py
