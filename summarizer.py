"""
summarizer.py
Free, local, offline text summarization using the `sumy` library.
No API key, no external calls, no cost.
"""

import nltk

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.summarizers.lsa import LsaSummarizer

ALGORITHMS = {
    "lexrank": LexRankSummarizer,
    "textrank": TextRankSummarizer,
    "lsa": LsaSummarizer,
}


def ensure_nltk_data() -> None:
    """Download the tokenizer data sumy needs, if it isn't already present.
    Safe to call every startup — it's a no-op after the first successful run."""
    for pkg in ("punkt", "punkt_tab"):
        try:
            nltk.data.find(f"tokenizers/{pkg}")
        except LookupError:
            try:
                nltk.download(pkg, quiet=True)
            except Exception:
                # Older nltk versions don't have punkt_tab at all — that's fine.
                pass


def summarize_text(text: str, sentence_count: int = 3, algorithm: str = "lexrank") -> str:
    """
    Summarize `text` down to `sentence_count` sentences using the given algorithm.
    Returns the summary as a single string.
    """
    algorithm = algorithm.lower()
    summarizer_cls = ALGORITHMS.get(algorithm, LexRankSummarizer)

    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = summarizer_cls()

    sentences = summarizer(parser.document, sentence_count)
    summary = " ".join(str(sentence) for sentence in sentences)

    return summary if summary.strip() else text[:500]


def word_count(text: str) -> int:
    return len(text.split())
