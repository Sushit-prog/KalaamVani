"""Extract individual Constitution articles from fetched Wikisource Part HTML.

Parses the parse-API JSON files, finds all article-number boundaries in the
rendered text, and extracts each article's verbatim text (between its boundary
and the next article's boundary). Saves per-article text files.
"""

import json
import re
import html as htmlmod
from pathlib import Path

PROVENANCE_DIR = Path(__file__).parent.parent / "data" / "raw" / "provenance"

# Articles that will get fetched_from_wikisource provenance
FETCHED_ARTICLES = {
    "13",
    "14",
    "16",
    "19",
    "21",
    "32",
    "36",
    "51A",
    "55",
    "110",
    "154",
    "352",
    "368",
    "370",
}

ARTICLES_BY_PART = {
    "part_iii": {"13", "14", "16", "19", "21", "32"},
    "part_iva": {"51A"},
    "part_iv": {"36"},
    "part_v": {"55", "110"},
    "part_vi": {"154"},
    "part_xviii": {"352"},
    "part_xx": {"368"},
    "part_xxi": {"370"},
}


def strip_html(html_text: str) -> str:
    text = re.sub(
        r"<(script|style)[^>]*>.*?</\1>", "", html_text, flags=re.DOTALL | re.IGNORECASE
    )
    text = re.sub(r"<[^>]+>", " ", text)
    text = htmlmod.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def find_all_boundaries(text: str) -> list[tuple[int, str]]:
    """Find positions of all `N. ` article-number boundaries in the text.

    Returns a sorted list of (position, article_number) tuples. Only counts
    plausible article numbers (1-3 digit with optional A/B/C... suffix) that
    appear at word boundaries.
    """
    boundaries = []
    # Match article numbers like 12, 13, 51A, 48A, 300A, 21A etc.
    pattern = r"(?:^|\s)(\d{1,3}[A-Z]?)\.\s"
    for m in re.finditer(pattern, text):
        num = m.group(1)
        base = re.sub(r"[^0-9]", "", num)
        if not base:
            continue
        n = int(base)
        # Article numbers in Part III run 12-35; Part IV 36-51; Part V 52-151;
        # Part VI 152-237; Part XVIII 352-360; Part XX 368; Part XXI 369-392.
        # Keep numbers in a plausible range (>= 12, <= 395) and ignore
        # stray numbers like "3." from references or "1789." from footnotes.
        if 12 <= n <= 395:
            boundaries.append((m.start(), num))
    # Deduplicate same-number at same-ish position, keep first
    seen = {}
    for pos, num in boundaries:
        if num not in seen:
            seen[num] = pos
    result = [(pos, num) for num, pos in seen.items()]
    result.sort(key=lambda x: x[0])
    return result


def extract_articles(part_name: str) -> dict[str, str]:
    part_file = PROVENANCE_DIR / f"{part_name}.json"
    with open(part_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    full_text = strip_html(data["parse"]["text"]["*"])
    boundaries = find_all_boundaries(full_text)

    # Map number -> (start_pos, next_pos)
    segments = {}
    for i, (pos, num) in enumerate(boundaries):
        end = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(full_text)
        segments[num] = (pos, end)

    articles = {}
    for num, (start, end) in segments.items():
        text = full_text[start:end].strip()
        text = re.sub(rf"^{re.escape(num)}\.\s*", "", text).strip()
        # Strip section markers (only these are stripped; prose is kept verbatim)
        text = re.sub(
            r"==\s*(?:Notes?|References?|See also)\s*==", "", text, flags=re.IGNORECASE
        )
        text = re.sub(r"\s*\n==\s*$", "", text).strip()
        text = re.sub(r"\s+", " ", text).strip()
        articles[num] = text
    return articles


def main():
    all_extracted = {}
    for part_name in ARTICLES_BY_PART:
        needed = ARTICLES_BY_PART[part_name]
        part_articles = extract_articles(part_name)
        for num in needed:
            if num in part_articles and part_articles[num].strip():
                all_extracted[num] = part_articles[num].strip()
                print(f"{part_name}: article {num} = {len(all_extracted[num])} chars")
            else:
                print(f"{part_name}: article {num} MISSING/EMPTY")

    # Save per-article text files
    out_dir = PROVENANCE_DIR / "articles"
    out_dir.mkdir(exist_ok=True)
    for num, text in all_extracted.items():
        (out_dir / f"article_{num}.txt").write_text(text, encoding="utf-8")

    # Save summary
    summary = {
        num: {
            "chars": len(text),
            "fetched": num in FETCHED_ARTICLES,
            "part": next(
                part for part, nums in ARTICLES_BY_PART.items() if num in nums
            ),
        }
        for num, text in all_extracted.items()
    }
    (PROVENANCE_DIR / "extraction_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print(f"\nTotal extracted: {len(all_extracted)} articles")
    for num in sorted(
        all_extracted, key=lambda x: (len(x) > 2, int(re.sub(r"[^0-9]", "", x) or "0"))
    ):
        print(
            f"  Art {num}: {len(all_extracted[num])} chars  fetched={summary[num]['fetched']}"
        )


if __name__ == "__main__":
    main()
