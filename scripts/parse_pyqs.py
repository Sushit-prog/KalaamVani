"""Parse mainspolity.txt into pyqs.json."""

import json
import re
from pathlib import Path


def parse_mainspolity(filepath: Path) -> list[dict]:
    """Parse mainspolity.txt into structured question dicts."""
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")

    questions: list[dict] = []
    current_year = None
    current_question_lines: list[str] = []
    current_question_num = None
    year_counters: dict[int, int] = {}

    def flush_question():
        nonlocal current_question_lines, current_question_num
        if current_question_num is None or current_year is None:
            current_question_lines = []
            return
        full_text = " ".join(current_question_lines).strip()
        full_text = re.sub(r"\s+", " ", full_text)

        word_limit = None
        wl_match = re.search(r"\((\d+)\s*words?\)\s*$", full_text)
        if wl_match:
            word_limit = int(wl_match.group(1))
            full_text = full_text[: wl_match.start()].strip()

        seq = year_counters[current_year]
        year_counters[current_year] += 1
        questions.append(
            {
                "question_id": f"MAINS-{current_year}-{seq:03d}",
                "year": current_year,
                "exam": "Mains",
                "question_text": full_text,
                "options": None,
                "correct_option": None,
                "word_limit": word_limit,
                "explanation": None,
                "model_answer": None,
                "must_mention_concepts": None,
                "topic": None,
                "difficulty": None,
                "reviewed": False,
            }
        )
        current_question_lines = []
        current_question_num = None

    for line in lines:
        stripped = line.strip()

        year_match = re.match(r"^(20\d{2})\s*$", stripped)
        if year_match:
            flush_question()
            current_year = int(year_match.group(1))
            if current_year not in year_counters:
                year_counters[current_year] = 1
            continue

        if current_year is None:
            continue

        q_match = re.match(r"^(\d+)\.\s*(.+)", stripped)
        if q_match:
            flush_question()
            current_question_num = int(q_match.group(1))
            current_question_lines = [q_match.group(2)]
            continue

        if current_question_num is not None and stripped:
            current_question_lines.append(stripped)

    flush_question()
    return questions


SELECTED_20: dict[str, dict] = {
    "MAINS-2017-006": {
        "model_answer": (
            "The right to privacy is protected as an intrinsic part of the "
            "right to life and personal liberty under Article 21. In K.S. "
            "Puttaswamy v. Union of India (2017), the Supreme Court declared "
            "privacy a fundamental right, tracing it to dignity and liberty. "
            "The Court held that the right extends to informational privacy, "
            "bodily autonomy, and decisions relating to personal identity."
        ),
        "must_mention_concepts": [
            {"keyword": "Article 21", "source_article": "21"},
            {"keyword": "right to life and personal liberty", "source_article": "21"},
            {"keyword": "Puttaswamy judgment", "source_article": "21"},
            {"keyword": "dignity", "source_article": "21"},
            {"keyword": "informational privacy", "source_article": "21"},
        ],
        "topic": "Fundamental Rights",
        "difficulty": 3,
    },
    "MAINS-2024-002": {
        "model_answer": (
            "Article 21 protects the right to life and personal liberty, which "
            "the Supreme Court has interpreted to include the right to privacy "
            "and bodily integrity. In the context of DNA testing to establish "
            "paternity, courts must balance the right to know one's parentage "
            "against the right to privacy and dignity of the individuals "
            "concerned, including the child."
        ),
        "must_mention_concepts": [
            {"keyword": "Article 21", "source_article": "21"},
            {"keyword": "right to privacy", "source_article": "21"},
            {"keyword": "bodily integrity", "source_article": "21"},
            {"keyword": "paternity", "source_article": "21"},
        ],
        "topic": "Fundamental Rights",
        "difficulty": 3,
    },
    "MAINS-2023-007": {
        "model_answer": (
            "Constitutional gender justice is rooted in Article 14 (equality "
            "before law), Article 15(1) (prohibition of discrimination on "
            "sex), Article 16 (equal opportunity in public employment), and "
            "Article 44 (Uniform Civil Code under DPSP). Landmark cases like "
            "Vishaka v. State of Rajasthan laid down guidelines for workplace "
            "sexual harassment, later codified in the POSH Act, 2013."
        ),
        "must_mention_concepts": [
            {"keyword": "Article 14", "source_article": "14"},
            {"keyword": "Article 15", "source_article": "15"},
            {"keyword": "Article 16", "source_article": "16"},
            {"keyword": "Article 44", "source_article": "44"},
            {"keyword": "Vishaka judgment", "source_article": "14"},
        ],
        "topic": "Fundamental Rights",
        "difficulty": 3,
    },
    "MAINS-2024-003": {
        "model_answer": (
            "Indian secularism (Sarva Dharma Sambhava) differs from the US "
            "First Amendment's strict wall of separation. India's Article 25 "
            "guarantees freedom of religion while allowing state regulation "
            "of secular activities. The Indian model involves equal respect "
            "for all religions rather than complete exclusion of religion "
            "from public life, as reflected in Articles 25-28."
        ),
        "must_mention_concepts": [
            {"keyword": "Sarva Dharma Sambhava", "source_article": "25"},
            {"keyword": "Article 25", "source_article": "25"},
            {"keyword": "First Amendment USA", "source_article": "25"},
            {"keyword": "equal respect", "source_article": "25"},
        ],
        "topic": "Secularism",
        "difficulty": 3,
    },
    "MAINS-2019-005": {
        "model_answer": (
            "France follows laicite (strict state secularism) with complete "
            "separation of church and state. India could learn from France's "
            "codified secular framework and institutional mechanisms. However, "
            "France's blanket ban on religious symbols in public spaces "
            "conflicts with India's pluralistic ethos. India's model of "
            "principled distance, allowing state intervention in religion "
            "for social reform, is arguably more suited to diverse societies."
        ),
        "must_mention_concepts": [
            {"keyword": "laicite", "source_article": "25"},
            {"keyword": "principled distance", "source_article": "25"},
            {"keyword": "Article 25-28", "source_article": "25"},
            {"keyword": "pluralism", "source_article": "25"},
        ],
        "topic": "Secularism",
        "difficulty": 4,
    },
    "MAINS-2024-005": {
        "model_answer": (
            "The cabinet system has led to the concentration of executive "
            "power in the Prime Minister and Cabinet, reducing Parliament's "
            "role from a deliberative legislature to a forum for rubber-"
            "stamping decisions. TheAnti-Defection Law (10th Schedule) further "
            "restricts free voting, while the decline of private members' "
            "bills and reduced sitting days weaken parliamentary supremacy."
        ),
        "must_mention_concepts": [
            {"keyword": "cabinet system", "source_article": "74"},
            {"keyword": "Article 74", "source_article": "74"},
            {"keyword": "10th Schedule", "source_article": "74"},
            {"keyword": "parliamentary sovereignty", "source_article": "74"},
        ],
        "topic": "Parliament",
        "difficulty": 4,
    },
    "MAINS-2019-009": {
        "model_answer": (
            "The Attorney General of India (Article 76) is the chief legal "
            "adviser to the Government of India. He has the right of audience "
            "in all courts and can participate in Parliamentary proceedings "
            "but cannot vote. He holds office during the pleasure of the "
            "President and must be qualified to be a Supreme Court judge."
        ),
        "must_mention_concepts": [
            {"keyword": "Article 76", "source_article": "76"},
            {"keyword": "right of audience", "source_article": "76"},
            {"keyword": "pleasure of the President", "source_article": "76"},
        ],
        "topic": "Parliament",
        "difficulty": 2,
    },
    "MAINS-2020-009": {
        "model_answer": (
            "Rajya Sabha has evolved from a weak revising chamber to a "
            "powerful federal chamber representing state interests. Its "
            "transformations include: amending the Constitution under "
            "Article 368, its role in approving state-legislation under "
            "Article 249, and its increased use of the Anti-Defection Law. "
            "The Chairman (Vice-President) has casting vote power, adding "
            "to its institutional significance."
        ),
        "must_mention_concepts": [
            {"keyword": "Article 310", "source_article": "310"},
            {"keyword": "federal chamber", "source_article": "310"},
            {"keyword": "Article 249", "source_article": "249"},
            {"keyword": "Anti-Defection Law", "source_article": "310"},
        ],
        "topic": "Parliament",
        "difficulty": 3,
    },
    "MAINS-2022-006": {
        "model_answer": (
            "Under Article 213, the Governor can promulgate ordinances when "
            "the legislature is not in session. However, re-promulgation "
            "without placing them before the legislature violates the spirit "
            "of representative democracy, as held in D.C. Wadhwa v. State of "
            "Bihar. The Supreme Court has ruled that repeated re-promulgation "
            "amounts to executive legislation bypassing democratic scrutiny."
        ),
        "must_mention_concepts": [
            {"keyword": "Article 213", "source_article": "213"},
            {"keyword": "ordinance power", "source_article": "213"},
            {"keyword": "D.C. Wadhwa case", "source_article": "213"},
            {"keyword": "re-promulgation", "source_article": "213"},
        ],
        "topic": "Executive",
        "difficulty": 3,
    },
    "MAINS-2022-003": {
        "model_answer": (
            "The Vice-President is the ex-officio Chairman of Rajya Sabha "
            "(Article 64) and second-highest constitutional functionary. "
            "The Chairman presides over Rajya Sabha sessions, maintains "
            "order, and has a casting vote. The Vice-President can be "
            "removed by a resolution of Rajya Sabha passed by effective "
            "majority and agreed to by Lok Sabha (Article 67(b))."
        ),
        "must_mention_concepts": [
            {"keyword": "Article 64", "source_article": "64"},
            {"keyword": "ex-officio Chairman", "source_article": "64"},
            {"keyword": "casting vote", "source_article": "64"},
            {"keyword": "Article 67", "source_article": "67"},
        ],
        "topic": "Executive",
        "difficulty": 2,
    },
    "MAINS-2019-007": {
        "model_answer": (
            "Article 368 grants Parliament the power to amend the Constitution "
            "but this power is not absolute. The Supreme Court in Kesavananda "
            "Bharati v. State of Kerala (1973) established the Basic Structure "
            "doctrine, holding that Parliament cannot amend or destroy the "
            "basic features of the Constitution. This includes federalism, "
            "judicial review, secularism, and democratic character of polity."
        ),
        "must_mention_concepts": [
            {"keyword": "Article 368", "source_article": "368"},
            {"keyword": "Basic Structure doctrine", "source_article": "368"},
            {"keyword": "Kesavananda Bharati", "source_article": "368"},
            {"keyword": "limited power", "source_article": "368"},
        ],
        "topic": "Amendments",
        "difficulty": 3,
    },
    "MAINS-2025-007": {
        "model_answer": (
            "Parliament's amending power under Article 368 is subject to "
            "both procedural limitations (special majority under Art. 368(2) "
            "and ratification by half the state legislatures under Art. 368(2) "
            "for federal provisions) and substantive limitations (the Basic "
            "Structure doctrine). Procedurally, a bill must be passed by "
            "special majority in both Houses. Substantively, it cannot violate "
            "fundamental features like judicial review, federalism, or "
            "democratic governance."
        ),
        "must_mention_concepts": [
            {"keyword": "Article 368", "source_article": "368"},
            {"keyword": "special majority", "source_article": "368"},
            {"keyword": "ratification", "source_article": "368"},
            {"keyword": "Basic Structure", "source_article": "368"},
        ],
        "topic": "Amendments",
        "difficulty": 4,
    },
    "MAINS-2015-002": {
        "model_answer": (
            "Cooperative federalism emphasises collaboration between Centre "
            "and States for national development. Existing drawbacks include "
            "centralised planning, overlapping jurisdictions, and fiscal "
            "dependency of states on the Centre. NITI Aayog was established "
            "to promote cooperative federalism through the Governing Council "
            "mechanism. The GST Council under Article 279A is another example "
            "of cooperative federalism in action."
        ),
        "must_mention_concepts": [
            {"keyword": "cooperative federalism", "source_article": "246"},
            {"keyword": "NITI Aayog", "source_article": "246"},
            {"keyword": "GST Council", "source_article": "279A"},
            {"keyword": "Article 279A", "source_article": "279A"},
        ],
        "topic": "Federalism",
        "difficulty": 3,
    },
    "MAINS-2021-005": {
        "model_answer": (
            "The CBI's jurisdiction to investigate cases within states requires "
            "consent of the state government under Section 6 of the Delhi "
            "Special Police Establishment Act, 1946. However, this consent "
            "is not absolute — the Supreme Court held in cases involving "
            "Article 356 that the Centre can direct CBI investigations in "
            "cases involving all-India ramifications without state consent, "
            "reflecting the federal character of India."
        ),
        "must_mention_concepts": [
            {"keyword": "CBI", "source_article": "246"},
            {"keyword": "Section 6 DSPE Act", "source_article": "246"},
            {"keyword": "state consent", "source_article": "246"},
            {"keyword": "federal character", "source_article": "246"},
        ],
        "topic": "Federalism",
        "difficulty": 4,
    },
    "MAINS-2024-004": {
        "model_answer": (
            "Recent reforms in Centre-State relations include the 101st "
            "Constitutional Amendment (GST), replacing the Planning Commission "
            "with NITI Aayog, and devolution recommendations of the 15th "
            "Finance Commission. Trust-building measures include greater fiscal "
            "devolution, empowering GST Council for cooperative decision-making, "
            "and regular Inter-State Council meetings under Article 263."
        ),
        "must_mention_concepts": [
            {"keyword": "101st Amendment", "source_article": "246"},
            {"keyword": "GST", "source_article": "246"},
            {"keyword": "NITI Aayog", "source_article": "246"},
            {"keyword": "Article 263", "source_article": "263"},
            {"keyword": "Finance Commission", "source_article": "280"},
        ],
        "topic": "Federalism",
        "difficulty": 3,
    },
    "MAINS-2023-001": {
        "model_answer": (
            "Constitutional judicial independence is guaranteed through "
            "provisions like Article 124 (appointment by collegium), Article "
            "121 (restrictions on Parliament discussing judges' conduct), and "
            "fixed service conditions. Independence of the judiciary is part "
            "of the Basic Structure doctrine (L. Chandra Kumar v. Union of "
            "India). Without independent courts, constitutional rights become "
            "unenforceable, making judicial independence a prerequisite of "
            "democracy."
        ),
        "must_mention_concepts": [
            {"keyword": "Article 124", "source_article": "124"},
            {"keyword": "collegium", "source_article": "124"},
            {"keyword": "Basic Structure", "source_article": "124"},
            {"keyword": "Article 121", "source_article": "121"},
        ],
        "topic": "Judiciary",
        "difficulty": 3,
    },
    "MAINS-2023-008": {
        "model_answer": (
            "The collegium system evolved through the Three Judges Cases "
            "(1982, 1993, 1998). In India, the Chief Justice and senior "
            "judges recommend appointments; the executive can only raise "
            "objections. In the USA, the President nominates and the Senate "
            "confirms (Article II, Section 2). Advantages of collegium: "
            "insulates judiciary from political pressure. Disadvantages: "
            "lack of transparency, no fixed procedure, and potential for "
            "judicial cronyism."
        ),
        "must_mention_concepts": [
            {"keyword": "collegium system", "source_article": "124"},
            {"keyword": "Three Judges Cases", "source_article": "124"},
            {"keyword": "Chief Justice", "source_article": "124"},
            {"keyword": "Senate confirmation", "source_article": "124"},
        ],
        "topic": "Judiciary",
        "difficulty": 4,
    },
    "MAINS-2017-002": {
        "model_answer": (
            "In Supreme Court Advocates-on-Record Association v. Union of "
            "India (2015), the Supreme Court struck down the National Judicial "
            "Appointments Commission (NJAC) Act, 2014 and the 99th Constitutional "
            "Amendment as unconstitutional. The Court held that the collegium "
            "system is part of the basic structure and NJAC would compromise "
            "judicial independence by allowing executive dominance in judge "
            "appointments."
        ),
        "must_mention_concepts": [
            {"keyword": "NJAC", "source_article": "124"},
            {"keyword": "99th Amendment", "source_article": "124"},
            {"keyword": "collegium", "source_article": "124"},
            {"keyword": "basic structure", "source_article": "124"},
        ],
        "topic": "Judiciary",
        "difficulty": 3,
    },
    "MAINS-2025-006": {
        "model_answer": (
            "Constitutional morality refers to adherence to constitutional "
            "principles, values, and procedures. As held in Kesavananda Bharati "
            "and Navtej Johar, it acts as a check on both high functionaries "
            "and citizens. In balancing judicial independence with accountability, "
            "constitutional morality demands that judges maintain independence "
            "while being accountable through in-house procedures, judicial "
            "standards bills, and the collegium's internal review mechanisms."
        ),
        "must_mention_concepts": [
            {"keyword": "constitutional morality", "source_article": "14"},
            {"keyword": "Kesavananda Bharati", "source_article": "368"},
            {"keyword": "judicial independence", "source_article": "124"},
            {"keyword": "judicial accountability", "source_article": "124"},
        ],
        "topic": "Judiciary",
        "difficulty": 4,
    },
    "MAINS-2018-003": {
        "model_answer": (
            "Under Article 360, the President can proclaim a Financial Emergency "
            "if the President is satisfied that the financial stability or credit "
            "of India or any part thereof is threatened. During such emergency, "
            "the Centre can give directions to any state on financial matters, "
            "reduce salaries of government employees (including judges), and "
            "reserve money bills for Presidential consideration. No Financial "
            "Emergency has been proclaimed so far in India."
        ),
        "must_mention_concepts": [
            {"keyword": "Article 360", "source_article": "360"},
            {"keyword": "Financial Emergency", "source_article": "360"},
            {"keyword": "financial stability", "source_article": "360"},
            {"keyword": "salary reduction", "source_article": "360"},
        ],
        "topic": "Emergency",
        "difficulty": 2,
    },
}


def enrich_selected(questions: list[dict]) -> list[dict]:
    """Populate model_answer/must_mention_concepts for the 20 selected questions."""
    for q in questions:
        qid = q["question_id"]
        if qid in SELECTED_20:
            info = SELECTED_20[qid]
            q["model_answer"] = info["model_answer"]
            q["must_mention_concepts"] = info["must_mention_concepts"]
            q["topic"] = info["topic"]
            q["difficulty"] = info["difficulty"]
            q["reviewed"] = False
    return questions


def main():
    input_path = Path("mainspolity.txt")
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    questions = parse_mainspolity(input_path)
    questions = enrich_selected(questions)

    output_path = output_dir / "pyqs.json"
    output_path.write_text(
        json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Parsed {len(questions)} questions to {output_path}")
    enriched = [q for q in questions if q["model_answer"] is not None]
    print(
        f"Enriched {len(enriched)} questions with model_answer + must_mention_concepts"
    )
    for q in enriched:
        print(f"  {q['question_id']} ({q['topic']}, difficulty={q['difficulty']})")


if __name__ == "__main__":
    main()
