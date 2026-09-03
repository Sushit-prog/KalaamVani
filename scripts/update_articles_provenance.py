"""Update articles.json with fetched Wikisource article text + provenance.

- 14 articles get provenance: 'fetched_from_wikisource' with verbatim text
- All others get provenance: 'curated_not_verified'
- Adds amendment-cutoff provenance metadata to fetched articles.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent.parent
ARTICLES_JSON = BASE / "data" / "processed" / "articles.json"
PROVENANCE_DIR = BASE / "data" / "raw" / "provenance"

# article_number -> (Part file, source_url, title)
FETCHED = {
    "13": (
        "part_iii",
        "https://en.wikisource.org/wiki/Constitution_of_India_(2020)/Part_III",
        "Laws inconsistent with or in derogation of the fundamental rights",
    ),
    "14": (
        "part_iii",
        "https://en.wikisource.org/wiki/Constitution_of_India_(2020)/Part_III",
        "Equality before law",
    ),
    "16": (
        "part_iii",
        "https://en.wikisource.org/wiki/Constitution_of_India_(2020)/Part_III",
        "Equality of opportunity in matters of public employment",
    ),
    "19": (
        "part_iii",
        "https://en.wikisource.org/wiki/Constitution_of_India_(2020)/Part_III",
        "Protection of certain rights regarding freedom of speech, etc.",
    ),
    "21": (
        "part_iii",
        "https://en.wikisource.org/wiki/Constitution_of_India_(2020)/Part_III",
        "Protection of life and personal liberty",
    ),
    "32": (
        "part_iii",
        "https://en.wikisource.org/wiki/Constitution_of_India_(2020)/Part_III",
        "Remedies for enforcement of rights conferred by this Part",
    ),
    "36": (
        "part_iv",
        "https://en.wikisource.org/wiki/Constitution_of_India_(2020)/Part_IV",
        "Definition",
    ),
    "51A": (
        "part_iva",
        "https://en.wikisource.org/wiki/Constitution_of_India_(2020)/Part_IVA",
        "Fundamental duties",
    ),
    "55": (
        "part_v",
        "https://en.wikisource.org/wiki/Constitution_of_India_(2020)/Part_V",
        "Manner of election of President",
    ),
    "110": (
        "part_v",
        "https://en.wikisource.org/wiki/Constitution_of_India_(2020)/Part_V",
        'Definition of "Money Bills"',
    ),
    "154": (
        "part_vi",
        "https://en.wikisource.org/wiki/Constitution_of_India_(2020)/Part_VI",
        "Executive power of State",
    ),
    "352": (
        "part_xviii",
        "https://en.wikisource.org/wiki/Constitution_of_India_(2020)/Part_XVIII",
        "Proclamation of Emergency",
    ),
    "368": (
        "part_xx",
        "https://en.wikisource.org/wiki/Constitution_of_India_(2020)/Part_XX",
        "Power of Parliament to amend the Constitution and procedure therefor",
    ),
    "370": (
        "part_xxi",
        "https://en.wikisource.org/wiki/Constitution_of_India_(2020)/Part_XXI",
        "Temporary provisions with respect to the State of Jammu and Kashmir",
    ),
}

FETCHED_AT = datetime.now(timezone.utc).isoformat()

PROVENANCE_NOTE = {
    "current_as_of": "2020-09-09",
    "amendment_cutoff": "Constitution (One Hundred and Fourth Amendment) Act, 2019",
    "note": "Static Wikisource snapshot dated 9 September 2020; amendments after the 104th Amendment Act (2019) are not reflected",
}


def load_fetched_text(num: str) -> str:
    f = PROVENANCE_DIR / "articles" / f"article_{num}.txt"
    return f.read_text(encoding="utf-8").strip()


def main():
    with open(ARTICLES_JSON, encoding="utf-8") as f:
        articles = json.load(f)

    # Short keywords helper for fetched articles (light curation from text)
    def make_keywords(num: str, text: str) -> list:
        # Keyword extraction (concise, based on article content)
        base = {
            "13": [
                "void",
                "judicial review",
                "inconsistent",
                "fundamental rights",
                "derogation",
            ],
            "14": ["equality before law", "equal protection", "state", "person"],
            "16": [
                "public employment",
                "equality of opportunity",
                "reservation",
                "citizen",
            ],
            "19": [
                "freedom of speech",
                "freedom of assembly",
                "association",
                "movement",
                "profession",
            ],
            "21": ["life", "personal liberty", "procedure established by law"],
            "32": [
                "writs",
                "habeas corpus",
                "mandamus",
                "prohibition",
                "quo warranto",
                "certiorari",
                "Supreme Court",
            ],
            "36": ["state", "definition", "Part III", "directive principles"],
            "51A": ["fundamental duties", "citizen", "Constitution", "42nd Amendment"],
            "55": [
                "President",
                "election",
                "electoral college",
                "proportional representation",
            ],
            "110": ["money bill", "Lok Sabha", "Speaker", "tax", "Parliament"],
            "154": ["governor", "executive power", "state"],
            "352": [
                "emergency",
                "war",
                "external aggression",
                "armed rebellion",
                "President",
            ],
            "368": [
                "amendment",
                "special majority",
                "Parliament",
                "constituent power",
                "ratification",
            ],
            "370": [
                "Jammu and Kashmir",
                "temporary provisions",
                "President",
                "Constituent Assembly",
            ],
        }
        return base.get(num, [])

    fetched_nums = set(FETCHED.keys())
    updated = 0
    for a in articles:
        num = a["article_number"]
        if num in fetched_nums:
            text = load_fetched_text(num)
            part_file, source_url, title = FETCHED[num]
            a["title"] = title
            a["text"] = text
            a["keywords"] = make_keywords(num, text)
            a["provenance"] = "fetched_from_wikisource"
            a["source_url"] = source_url
            a["fetched_at"] = FETCHED_AT
            a.update(PROVENANCE_NOTE)
            updated += 1
        else:
            a["provenance"] = "curated_not_verified"
            a["current_as_of"] = PROVENANCE_NOTE["current_as_of"]
            a["amendment_cutoff"] = PROVENANCE_NOTE["amendment_cutoff"]

    with open(ARTICLES_JSON, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)

    print(f"Updated {updated} articles to fetched_from_wikisource")
    print(f"Total articles: {len(articles)}")


if __name__ == "__main__":
    main()
