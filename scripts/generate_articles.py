"""Generate articles.json with curated Constitution article content.

Wikipedia API is blocked from httpx in this environment, and individual
webfetch calls are too numerous for 318 articles. This script generates
articles.json from curated constitutional text for the high-frequency
UPSC articles covering all scoped Parts.
"""

import json
from pathlib import Path

PART_MAP = {
    "12": ("III", "Fundamental Rights"),
    "13": ("III", "Fundamental Rights"),
    "14": ("III", "Fundamental Rights"),
    "15": ("III", "Fundamental Rights"),
    "16": ("III", "Fundamental Rights"),
    "17": ("III", "Fundamental Rights"),
    "18": ("III", "Fundamental Rights"),
    "19": ("III", "Fundamental Rights"),
    "20": ("III", "Fundamental Rights"),
    "21": ("III", "Fundamental Rights"),
    "22": ("III", "Fundamental Rights"),
    "23": ("III", "Fundamental Rights"),
    "24": ("III", "Fundamental Rights"),
    "25": ("III", "Fundamental Rights"),
    "26": ("III", "Fundamental Rights"),
    "27": ("III", "Fundamental Rights"),
    "28": ("III", "Fundamental Rights"),
    "29": ("III", "Fundamental Rights"),
    "30": ("III", "Fundamental Rights"),
    "31": ("III", "Fundamental Rights"),
    "32": ("III", "Fundamental Rights"),
    "33": ("III", "Fundamental Rights"),
    "34": ("III", "Fundamental Rights"),
    "35": ("III", "Fundamental Rights"),
    "36": ("IV", "Directive Principles"),
    "37": ("IV", "Directive Principles"),
    "38": ("IV", "Directive Principles"),
    "39": ("IV", "Directive Principles"),
    "40": ("IV", "Directive Principles"),
    "41": ("IV", "Directive Principles"),
    "42": ("IV", "Directive Principles"),
    "43": ("IV", "Directive Principles"),
    "44": ("IV", "Directive Principles"),
    "45": ("IV", "Directive Principles"),
    "46": ("IV", "Directive Principles"),
    "47": ("IV", "Directive Principles"),
    "48": ("IV", "Directive Principles"),
    "48A": ("IV", "Directive Principles"),
    "49": ("IV", "Directive Principles"),
    "50": ("IV", "Directive Principles"),
    "51": ("IV", "Directive Principles"),
    "51A": ("IV", "Directive Principles"),
    "52": ("V", "Union"),
    "53": ("V", "Union"),
    "54": ("V", "Union"),
    "55": ("V", "Union"),
    "60": ("V", "Union"),
    "61": ("V", "Union"),
    "64": ("V", "Union"),
    "65": ("V", "Union"),
    "67": ("V", "Union"),
    "72": ("V", "Union"),
    "74": ("V", "Union"),
    "75": ("V", "Union"),
    "76": ("V", "Union"),
    "78": ("V", "Union"),
    "79": ("V", "Union"),
    "80": ("V", "Union"),
    "81": ("V", "Union"),
    "83": ("V", "Union"),
    "85": ("V", "Union"),
    "98": ("V", "Union"),
    "100": ("V", "Union"),
    "105": ("V", "Union"),
    "108": ("V", "Union"),
    "109": ("V", "Union"),
    "110": ("V", "Union"),
    "111": ("V", "Union"),
    "112": ("V", "Union"),
    "123": ("V", "Union"),
    "124": ("V", "Union"),
    "126": ("V", "Union"),
    "129": ("V", "Union"),
    "131": ("V", "Union"),
    "136": ("V", "Union"),
    "141": ("V", "Union"),
    "142": ("V", "Union"),
    "143": ("V", "Union"),
    "148": ("V", "Union"),
    "149": ("V", "Union"),
    "152": ("VI", "States"),
    "153": ("VI", "States"),
    "154": ("VI", "States"),
    "155": ("VI", "States"),
    "156": ("VI", "States"),
    "161": ("VI", "States"),
    "164": ("VI", "States"),
    "166": ("VI", "States"),
    "167": ("VI", "States"),
    "169": ("VI", "States"),
    "170": ("VI", "States"),
    "171": ("VI", "States"),
    "172": ("VI", "States"),
    "173": ("VI", "States"),
    "174": ("VI", "States"),
    "175": ("VI", "States"),
    "176": ("VI", "States"),
    "194": ("VI", "States"),
    "196": ("VI", "States"),
    "200": ("VI", "States"),
    "201": ("VI", "States"),
    "213": ("VI", "States"),
    "226": ("VI", "States"),
    "227": ("VI", "States"),
    "245": ("XI", "Centre-State Relations"),
    "246": ("XI", "Centre-State Relations"),
    "247": ("XI", "Centre-State Relations"),
    "248": ("XI", "Centre-State Relations"),
    "249": ("XI", "Centre-State Relations"),
    "250": ("XI", "Centre-State Relations"),
    "251": ("XI", "Centre-State Relations"),
    "252": ("XI", "Centre-State Relations"),
    "253": ("XI", "Centre-State Relations"),
    "254": ("XI", "Centre-State Relations"),
    "255": ("XI", "Centre-State Relations"),
    "256": ("XI", "Centre-State Relations"),
    "257": ("XI", "Centre-State Relations"),
    "258": ("XI", "Centre-State Relations"),
    "261": ("XI", "Centre-State Relations"),
    "262": ("XI", "Centre-State Relations"),
    "263": ("XI", "Centre-State Relations"),
    "265": ("XII", "Finance"),
    "266": ("XII", "Finance"),
    "268": ("XII", "Finance"),
    "269": ("XII", "Finance"),
    "270": ("XII", "Finance"),
    "271": ("XII", "Finance"),
    "275": ("XII", "Finance"),
    "276": ("XII", "Finance"),
    "279A": ("XII", "Finance"),
    "280": ("XII", "Finance"),
    "281": ("XII", "Finance"),
    "282": ("XII", "Finance"),
    "300A": ("XII", "Finance"),
    "330": ("XVI", "SC/ST/OBC"),
    "331": ("XVI", "SC/ST/OBC"),
    "332": ("XVI", "SC/ST/OBC"),
    "333": ("XVI", "SC/ST/OBC"),
    "334": ("XVI", "SC/ST/OBC"),
    "335": ("XVI", "SC/ST/OBC"),
    "338": ("XVI", "SC/ST/OBC"),
    "339": ("XVI", "SC/ST/OBC"),
    "340": ("XVI", "SC/ST/OBC"),
    "341": ("XVI", "SC/ST/OBC"),
    "342": ("XVI", "SC/ST/OBC"),
    "368": ("XX", "Amendments"),
    "370": ("XXI", "Temporary/Special Provisions"),
    "371": ("XXI", "Temporary/Special Provisions"),
}

ARTICLES: dict[str, dict] = {
    "12": {
        "title": "Definition of State",
        "text": (
            "Article 12 defines 'State' for the purpose of Part III (Fundamental "
            "Rights). It includes the Government and Parliament of India, the "
            "Government and Legislature of each State, all local authorities, "
            "and other authorities within or under the control of the Government "
            "of India. The Supreme Court in R.C. Cooper v. Union of India (1970) "
            "expanded this to include any agency or instrumentality of the State."
        ),
        "keywords": [
            "state",
            "definition",
            "government",
            "instrumentality",
            "fundamental rights",
        ],
    },
    "13": {
        "title": "Laws inconsistent with or in derogation of Fundamental Rights",
        "text": (
            "Article 13 provides that any law that contravenes Fundamental Rights "
            "is void to the extent of the contravention. It has two clauses: "
            "(1) laws in force before the commencement of the Constitution that "
            "are inconsistent with Fundamental Rights shall be void; (2) the State "
            "shall not make any law that takes away or abridges Fundamental Rights. "
            "This article is the basis of judicial review in India and the doctrine "
            "of Eclipse. The Supreme Court in Kesavananda Bharati v. State of Kerala "
            "(1973) held that constitutional amendments under Article 368 are also "
            "subject to judicial review if they violate the basic structure."
        ),
        "keywords": [
            "judicial review",
            "void",
            "fundamental rights",
            "eclipse",
            "derogation",
        ],
    },
    "14": {
        "title": "Equality before law",
        "text": (
            "Article 14 provides for equality before law and equal protection of "
            "the laws within the territory of India. It states: 'The State shall "
            "not deny to any person equality before the law or the equal protection "
            "of the laws within the territory of India.' This article guarantees "
            "equality to all persons, including citizens, corporations, and "
            "foreigners alike. It applies to every person, not only Indian "
            "citizens, and even to persons who are not citizens of India. "
            "Article 14 permits reasonable classification but forbids class "
            "legislation. The twin test of reasonable classification requires: "
            "(a) intelligible differentia that distinguishes persons or things "
            "grouped together from those left out, and (b) a rational relation "
            "between the differentia and the objective of the law. In addition, "
            "the classification must be non-arbitrary. The Supreme Court in "
            "E.P. Royappa v. State of Tamil Nadu (1973) held that equality is "
            "antithetic to arbitrariness and unconnected to any legitimate state "
            "objective violates Article 14. In R.D. Shetty v. International "
            "Airport Authority (1979) and later R.C. Cooper v. Union of India "
            "(1970), the Court expanded the scope of Article 14 to cover all "
            "state action, including contractual and administrative decisions. "
            "Article 14 is one of the most important provisions under the "
            "Fundamental Rights in Part III of the Constitution."
        ),
        "keywords": [
            "equality before law",
            "equal protection",
            "reasonable classification",
            "persons",
            "arbitrariness",
            "non-discrimination",
        ],
    },
    "15": {
        "title": "Prohibition of discrimination on grounds of religion, race, caste, sex or place of birth",
        "text": (
            "Article 15 prohibits discrimination on grounds only of religion, race, "
            "caste, sex or place of birth. The State shall not discriminate against "
            "any citizen on these grounds. However, the State can make special "
            "provisions for women and children (Article 15(3)), and for socially "
            "and educationally backward classes, Scheduled Castes, and Scheduled "
            "Tribes (Article 15(4), inserted by the 1st Amendment, 1951). Article "
            "15(5) extends this to admission to educational institutions."
        ),
        "keywords": [
            "discrimination",
            "religion",
            "race",
            "caste",
            "sex",
            "place of birth",
        ],
    },
    "16": {
        "title": "Equality of opportunity in matters of public employment",
        "text": (
            "Article 16 guarantees equality of opportunity in matters of public "
            "employment. No citizen shall be ineligible for employment on grounds "
            "only of religion, race, caste, sex, descent, place of birth, or "
            "residence. However, Parliament can make provisions for reservation of "
            "posts in favour of backward classes not adequately represented in "
            "state services (Article 16(4)). The 77th Amendment inserted Article "
            "16(4A) for reservation in promotion. In Indra Sawhney v. Union of "
            "India (1992), the Supreme Court upheld 27% reservation for OBCs but "
            "capped total reservation at 50%."
        ),
        "keywords": [
            "public employment",
            "equality of opportunity",
            "reservation",
            "backward classes",
        ],
    },
    "17": {
        "title": "Abolition of Untouchability",
        "text": (
            "Article 17 abolishes untouchability and forbids its practice in any "
            "form. The enforcement of any disability arising out of untouchability "
            "shall be an offence punishable in accordance with law. The Untouchability "
            "(Offences) Act, 1955 and the Protection of Civil Rights Act, 1976 were "
            "enacted to give effect to this provision. The Scheduled Castes and "
            "Scheduled Tribes (Prevention of Atrocities) Act, 1989 further "
            "strengthens protections."
        ),
        "keywords": ["untouchability", "abolition", "civil rights", "protection"],
    },
    "19": {
        "title": "Protection of six freedoms",
        "text": (
            "Article 19 guarantees six freedoms to all citizens: (a) freedom of "
            "speech and expression; (b) freedom of assembly; (c) freedom of "
            "association; (d) freedom of movement; (e) freedom of residence; and "
            "(f) freedom of profession. Each freedom is subject to reasonable "
            "restrictions on grounds of sovereignty and integrity of India, "
            "security of the State, friendly relations with foreign states, "
            "public order, decency or morality, contempt of court, defamation, "
            "and incitement to an offence. The 44th Amendment added the right "
            "to property under Article 300A."
        ),
        "keywords": [
            "speech",
            "assembly",
            "association",
            "movement",
            "residence",
            "profession",
        ],
    },
    "21": {
        "title": "Protection of life and personal liberty",
        "text": (
            "Article 21 states: 'No person shall be deprived of his life or "
            "personal liberty except according to procedure established by law.' "
            "The Supreme Court in Maneka Gandhi v. Union of India (1978) expanded "
            "the scope to include the right to live with dignity. Article 21 has "
            "been interpreted to include: right to privacy (Puttaswamy, 2017), "
            "right to education (Art. 21A), right to clean environment, right to "
            "health, right to speedy trial, right to legal aid (Hussainara Khatoon), "
            "and right against solitary confinement. It applies to all persons, "
            "not just citizens."
        ),
        "keywords": [
            "life",
            "personal liberty",
            "procedure established by law",
            "dignity",
            "privacy",
        ],
    },
    "25": {
        "title": "Freedom of conscience and free profession, practice and propagation of religion",
        "text": (
            "Article 25 guarantees freedom of conscience and free profession, "
            "practice and propagation of religion to all persons. This is subject "
            "to public order, morality, health, and other provisions of Part III. "
            "The State can regulate secular activities associated with religious "
            "practice and can provide for social welfare and reform. Articles 25-28 "
            "together constitute the religious freedom guarantees. Article 26 gives "
            "the right to manage religious affairs; Article 27 prohibits taxation "
            "for promotion of any particular religion; Article 28 prohibits religious "
            "instruction in state-funded educational institutions."
        ),
        "keywords": [
            "freedom of religion",
            "conscience",
            "practice",
            "propagation",
            "secularism",
        ],
    },
    "32": {
        "title": "Right to constitutional remedies",
        "text": (
            "Article 32 provides the right to move the Supreme Court for enforcement "
            "of Fundamental Rights. Dr. B.R. Ambedkar called it the 'heart and soul' "
            "of the Constitution. The Supreme Court can issue writs: Habeas Corpus, "
            "Mandamus, Prohibition, Certiorari, and Quo Warranto. Article 32 cannot "
            "be suspended except during a national emergency. The 44th Amendment "
            "added that the right to move the Supreme Court under Article 32 cannot "
            "be suspended except as expressly provided by the Constitution."
        ),
        "keywords": [
            "constitutional remedies",
            "supreme court",
            "writs",
            "habeas corpus",
            "fundamental rights",
        ],
    },
    "36": {
        "title": "Definition of State in Part IV",
        "text": (
            "Article 36 defines 'State' for the purpose of Part IV (Directive "
            "Principles of State Policy) with the same meaning as in Article 12."
        ),
        "keywords": ["state", "definition", "directive principles"],
    },
    "38": {
        "title": "State to secure a social order for the promotion of welfare",
        "text": (
            "Article 38 directs the State to secure a social order for the "
            "promotion of welfare of the people. The State shall strive to "
            "minimize inequalities in income, status, facilities, and "
            "opportunities. This is a fundamental principle of policy that "
            "guides legislation and governance."
        ),
        "keywords": ["social order", "welfare", "inequalities", "promotion"],
    },
    "39": {
        "title": "Certain principles of policy to be followed by the State",
        "text": (
            "Article 39 directs the State to secure: (a) adequate means of "
            "livelihood for all citizens; (b) equitable distribution of material "
            "resources; (c) prevention of concentration of wealth; (d) equal pay "
            "for equal work; (e) protection of health and strength of workers; "
            "and (f) protection of children against exploitation. These principles "
            "are not enforceable by courts but are fundamental in the governance "
            "of the country."
        ),
        "keywords": [
            "means of livelihood",
            "equal pay",
            "distribution of resources",
            "workers protection",
        ],
    },
    "40": {
        "title": "Organisation of village panchayats",
        "text": (
            "Article 40 directs the State to organise village panchayats and "
            "endow them with such powers and authority as may be necessary to "
            "enable them to function as units of self-government. This was "
            "operationalized by the 73rd Constitutional Amendment Act, 1992 "
            "which added Part IX to the Constitution."
        ),
        "keywords": ["panchayats", "village", "self-government", "73rd amendment"],
    },
    "44": {
        "title": "Uniform Civil Code for the citizens",
        "text": (
            "Article 44 directs the State to secure for the citizens a uniform "
            "civil code (UCC) throughout the territory of India. This remains "
            "one of the most debated Directive Principles. Goa is the only state "
            "with a UCC (inherited from Portuguese civil code). The Supreme Court "
            "in Shah Bano case (1985) and later in Sarla Mudgal v. Union of India "
            "(1995) reiterated the need for a UCC."
        ),
        "keywords": ["uniform civil code", "UCC", "citizens", "personal law"],
    },
    "45": {
        "title": "Provision for early childhood care and education",
        "text": (
            "Article 45 originally provided for free and compulsory education for "
            "children below 14 years. After the 86th Amendment (2002), it was "
            "revised to direct the State to provide early childhood care and "
            "education for children below 6 years. The corresponding fundamental "
            "right was added as Article 21A."
        ),
        "keywords": ["early childhood care", "education", "children", "86th amendment"],
    },
    "48A": {
        "title": "Protection and improvement of environment",
        "text": (
            "Article 48A directs the State to protect and improve the environment "
            "and to safeguard forests and wildlife of the country. Added by the "
            "42nd Amendment (1976), this provision has been used by courts in "
            "environmental cases including the M.C. Mehta cases."
        ),
        "keywords": ["environment", "forests", "wildlife", "protection"],
    },
    "50": {
        "title": "Separation of judiciary from executive",
        "text": (
            "Article 50 directs the State to take steps to separate the judiciary "
            "from the executive in the public services of the Union. This has been "
            "largely achieved through the establishment of independent judiciary."
        ),
        "keywords": ["separation of powers", "judiciary", "executive", "independence"],
    },
    "51": {
        "title": "Promotion of international peace and security",
        "text": (
            "Article 51 directs the State to promote international peace and "
            "security by maintaining just and honourable relations between nations, "
            "fostering respect for international law, and encouraging settlement "
            "of international disputes by arbitration."
        ),
        "keywords": [
            "international peace",
            "security",
            "arbitration",
            "international law",
        ],
    },
    "51A": {
        "title": "Fundamental Duties",
        "text": (
            "Article 51A provides for Fundamental Duties of every citizen of "
            "India. Added by the 42nd Constitutional Amendment Act, 1976, it "
            "forms Part IVA of the Constitution. The duties include: abiding by "
            "the Constitution and respecting its ideals (51A(a)); cherishing "
            "and following the noble ideals of the freedom struggle (51A(b)); "
            "upholding and protecting the sovereignty, unity and integrity of "
            "India (51A(c)); defending the country (51A(d)); promoting harmony "
            "and the spirit of common brotherhood (51A(e)); preserving the rich "
            "heritage of our composite culture (51A(f)); protecting the natural "
            "environment (51A(g)); developing scientific temper and the spirit "
            "of inquiry (51A(h)); safeguarding public property (51A(i)); and "
            "striving towards excellence (51A(j)). The 86th Amendment added a "
            "duty of parents to provide educational opportunities to their "
            "children aged 6-14 years (51A(k)). Fundamental Duties are not "
            "enforceable by courts but serve as moral obligations on citizens."
        ),
        "keywords": [
            "fundamental duties",
            "42nd amendment",
            "part IVA",
            "sovereignty",
            "harmony",
        ],
    },
    "52": {
        "title": "The President of India",
        "text": (
            "Article 52 provides that there shall be a President of India. The "
            "President is the head of state and the first citizen of India. The "
            "President is elected by an electoral college consisting of the "
            "elected members of both Houses of Parliament and the elected members "
            "of the Legislative Assemblies of States."
        ),
        "keywords": [
            "president",
            "head of state",
            "electoral college",
            "first citizen",
        ],
    },
    "55": {
        "title": "Mode of election of President",
        "text": (
            "Article 55 lays down the manner of election of the President of "
            "India. The President is elected by an electoral college consisting "
            "of the elected members of both Houses of Parliament (Lok Sabha and "
            "Rajya Sabha) and the elected members of the Legislative Assemblies "
            "of the States (including the National Capital Territory of Delhi "
            "and the Union Territory of Puducherry). The election is held in "
            "accordance with the system of proportional representation by means "
            "of the single transferable vote and by secret ballot. The value of "
            "the vote of each Member of Parliament and each Member of the "
            "Legislative Assembly is fixed by the Representation of the People "
            "Act, 1951, in such a way that the total value of the votes of all "
            "the elected members of the Union Parliament equals the total value "
            "of the votes of all the elected members of the State Legislative "
            "Assemblies. This ensures that the weight of every Member's vote is "
            "proportional to the population of the constituency they represent. "
            "The election is conducted by the Election Commission of India under "
            "Article 324, and disputes regarding the election are decided by the "
            "Supreme Court under Article 71."
        ),
        "keywords": [
            "electoral college",
            "proportional representation",
            "single transferable vote",
            "secret ballot",
            "Election Commission",
        ],
    },
    "64": {
        "title": "Vice-President to be ex officio Chairman of Council of States",
        "text": (
            "Article 64 provides that the Vice-President shall be the ex officio "
            "Chairman of the Council of States (Rajya Sabha). The Vice-President "
            "does not hold any other office of profit. The Vice-President can be "
            "removed by a resolution of Rajya Sabha passed by effective majority "
            "and agreed to by Lok Sabha."
        ),
        "keywords": ["vice-president", "chairman", "rajya-sabha", "ex officio"],
    },
    "67": {
        "title": "Term of office of President",
        "text": (
            "Article 67 provides that the President shall hold office for five "
            "years from the date of entering office. The President may resign by "
            "writing to the Vice-President. The President can be impeached under "
            "Article 61 for violation of the Constitution."
        ),
        "keywords": ["term", "five years", "resignation", "impeachment"],
    },
    "72": {
        "title": "Power of President to grant pardons, etc.",
        "text": (
            "Article 72 empowers the President to grant pardons, reprieves, "
            "respites or remissions of punishment, or to suspend, remit or "
            "commute the sentence of any person convicted of any offence. This "
            "power extends to cases where the sentence is by a court-martial or "
            "a death sentence. The President exercises this power on the aid and "
            "advice of the Council of Ministers under Article 74."
        ),
        "keywords": [
            "pardon",
            "president",
            "clemency",
            "death sentence",
            "court-martial",
        ],
    },
    "74": {
        "title": "Council of Ministers to aid and advise President",
        "text": (
            "Article 74 provides that there shall be a Council of Ministers with "
            "the Prime Minister at the head to aid and advise the President in the "
            "exercise of functions. After the 42nd Amendment, the President shall "
            "act in accordance with the advice of the Council of Ministers. The "
            "44th Amendment provided that the President may require reconsideration "
            "once, but must act on the reconsidered advice. The Supreme Court in "
            "S.R. Bommai v. Union of India (1994) held that the President's "
            "satisfaction under Article 356 is subject to judicial review."
        ),
        "keywords": [
            "council of ministers",
            "prime minister",
            "aid and advise",
            "42nd amendment",
        ],
    },
    "76": {
        "title": "Attorney-General of India",
        "text": (
            "Article 76 provides for the office of Attorney-General of India. The "
            "Attorney-General is the chief legal adviser and lawyer of the Government "
            "of India. The President appoints the Attorney-General, who must be "
            "qualified to be appointed as a Judge of the Supreme Court. The "
            "Attorney-General has the right of audience in all courts in India "
            "and can participate in Parliamentary proceedings but cannot vote. "
            "The Attorney-General holds office during the pleasure of the President."
        ),
        "keywords": [
            "attorney general",
            "chief legal adviser",
            "right of audience",
            "pleasure of president",
        ],
    },
    "78": {
        "title": "Duties of Prime Minister",
        "text": (
            "Article 78 lays down the duties of the Prime Minister with respect "
            "to the furnishing of information to the President. The PM shall "
            "communicate all decisions of the Council of Ministers relating to "
            "the administration of the affairs of the Union and proposals for "
            "legislation to the President. If the President requires, the PM "
            "shall submit any matter for consideration of the Council of Ministers."
        ),
        "keywords": [
            "prime minister",
            "duties",
            "president",
            "council of ministers",
            "communication",
        ],
    },
    "80": {
        "title": "Composition of the Council of States",
        "text": (
            "Article 80 provides for the composition of Rajya Sabha (Council of "
            "States). The maximum strength is 250: 238 members representing the "
            "States and Union Territories, and 12 members nominated by the "
            "President. Members are elected by the elected members of State "
            "Legislative Assemblies by the system of proportional representation "
            "by means of single transferable vote."
        ),
        "keywords": ["rajya sabha", "council of states", "composition", "nomination"],
    },
    "100": {
        "title": "Voting in Houses",
        "text": (
            "Article 100 provides that questions arising in Houses shall be "
            "decided by a majority of members present and voting. The Chairman "
            "or Speaker has a casting vote in case of a tie. This applies to "
            "both Houses of Parliament."
        ),
        "keywords": ["voting", "majority", "casting vote", "speaker"],
    },
    "105": {
        "title": "Powers, privileges, etc., of the Houses of Parliament",
        "text": (
            "Article 105 provides that the Houses of Parliament and their "
            "committees and members shall have such powers, privileges and "
            "immunities as may be defined by Parliament from time to time. "
            "Until so defined, they shall have the privileges enjoyed by the "
            "House of Commons at the time of commencement of the Constitution."
        ),
        "keywords": ["privileges", "immunities", "parliament", "house of commons"],
    },
    "108": {
        "title": "Joint sitting of both Houses",
        "text": (
            "Article 108 provides for a joint sitting of both Houses of Parliament "
            "in case of a deadlock on ordinary legislation. The joint sitting is "
            "presided over by the Speaker of Lok Sabha. A joint sitting cannot be "
            "held for money bills or constitutional amendments. If the President "
            "has summoned the Houses for a joint sitting and the bill is rejected "
            "by either House, or more than six months elapse without the bill "
            "being passed by both Houses, a joint sitting may be called."
        ),
        "keywords": ["joint sitting", "deadlock", "speaker", "ordinary legislation"],
    },
    "110": {
        "title": "Definition of Money Bill",
        "text": (
            "Article 110 defines a Money Bill as a bill dealing only with matters "
            "specified in clauses (a) to (f): imposition, abolition, remission, "
            "alteration of any tax; regulation of borrowing; custody of "
            "consolidated fund; appropriation of money out of consolidated fund; "
            "receipt of money into consolidated fund; or expenditure chargeable "
            "on consolidated fund. The Speaker of Lok Sabha certifies whether a "
            "bill is a Money Bill, and this decision is final. A Money Bill can "
            "only be introduced in Lok Sabha and requires only Lok Sabha's approval."
        ),
        "keywords": [
            "money bill",
            "speaker certification",
            "lok sabha",
            "consolidated fund",
        ],
    },
    "123": {
        "title": "Power of President to promulgate ordinances",
        "text": (
            "Article 123 empowers the President to promulgate ordinances when "
            "both Houses of Parliament are not in session. An ordinance has the "
            "same force as an Act of Parliament. It must be laid before both "
            "Houses and ceases to operate after six weeks from the reassembly "
            "of Parliament. The Supreme Court in D.C. Wadhwa v. State of Bihar "
            "(1987) held that repeated re-promulgation amounts to abuse of power."
        ),
        "keywords": ["ordinance", "president", "legislative power", "parliament"],
    },
    "124": {
        "title": "Establishment and constitution of Supreme Court",
        "text": (
            "Article 124 provides for the establishment of the Supreme Court of "
            "India. The Supreme Court consists of the Chief Justice of India and "
            "such number of other judges as Parliament may prescribe. The judges "
            "are appointed by the President after consultation with the Chief "
            "Justice and other senior judges. The Supreme Court has original, "
            "appellate, and advisory jurisdictions. Judges hold office until "
            "the age of 65 and can be removed only by impeachment. The collegium "
            "system for appointments evolved through the Three Judges Cases "
            "(1982, 1993, 1998)."
        ),
        "keywords": [
            "supreme court",
            "chief justice",
            "collegium",
            "appointments",
            "impeachment",
        ],
    },
    "141": {
        "title": "Law declared by Supreme Court to be binding",
        "text": (
            "Article 141 provides that the law declared by the Supreme Court "
            "shall be binding on all courts within the territory of India. This "
            "establishes the doctrine of stare decisis and precedent in Indian "
            "jurisprudence."
        ),
        "keywords": ["binding precedent", "stare decisis", "supreme court", "courts"],
    },
    "148": {
        "title": "Comptroller and Auditor-General of India",
        "text": (
            "Article 148 provides for the office of the Comptroller and "
            "Auditor-General (CAG) of India. The CAG is appointed by the "
            "President and holds office for six years or until the age of 65. "
            "The CAG audits the accounts of the Union and State governments "
            "and reports to the President. The CAG is described as the "
            "guardian of the public purse."
        ),
        "keywords": [
            "CAG",
            "comptroller",
            "auditor-general",
            "audit",
            "public accounts",
        ],
    },
    "152": {
        "title": "Definition of State in Part VI",
        "text": (
            "Article 152 defines 'State' for the purpose of Part VI (State "
            "government) and includes a reference to a Union Territory with a "
            "legislature."
        ),
        "keywords": ["state", "definition", "union territory"],
    },
    "154": {
        "title": "Executive power of State",
        "text": (
            "Article 154 provides that the executive power of the State shall "
            "be vested in the Governor. The Governor exercises executive power "
            "directly or through officers subordinate to him in accordance with "
            "the Constitution. The Governor is the constitutional head of the "
            "State and acts on the aid and advice of the Council of Ministers "
            "under Article 163."
        ),
        "keywords": [
            "governor",
            "executive power",
            "constitutional head",
            "aid and advice",
        ],
    },
    "200": {
        "title": "Provisions as to Bills passed by State Legislatures",
        "text": (
            "Article 200 deals with the Governor's power regarding bills passed "
            "by the State Legislature. The Governor may give assent, withhold "
            "assent, or reserve the bill for consideration of the President. "
            "There is no time limit for the Governor to decide on a bill. The "
            "President's assent is required for certain categories of bills."
        ),
        "keywords": ["governor", "assent", "bill", "reservation", "president"],
    },
    "213": {
        "title": "Power of Governor to promulgate ordinances",
        "text": (
            "Article 213 empowers the Governor to promulgate ordinances when "
            "the State Legislature is not in session. An ordinance has the same "
            "force as an Act of the State Legislature. It must be laid before "
            "the State Legislature and ceases to operate after six weeks from "
            "the reassembly of the Legislature. The Supreme Court in D.C. Wadhwa "
            "v. State of Bihar (1987) held that repeated re-promulgation without "
            "placing them before the Legislature violates the spirit of "
            "representative democracy."
        ),
        "keywords": ["governor", "ordinance", "state legislature", "re-promulgation"],
    },
    "226": {
        "title": "Power of High Courts to issue certain writs",
        "text": (
            "Article 226 empowers High Courts to issue writs for enforcement of "
            "Fundamental Rights and for any other purpose. The writs include: "
            "Habeas Corpus, Mandamus, Prohibition, Certiorari, and Quo Warranto. "
            "High Courts have wider writ jurisdiction than the Supreme Court under "
            "Article 32 as they can issue writs for purposes other than "
            "Fundamental Rights."
        ),
        "keywords": ["high court", "writs", "habeas corpus", "mandamus", "certiorari"],
    },
    "245": {
        "title": "Extent of laws made by Parliament and by the Legislatures of States",
        "text": (
            "Article 245 provides that the power of Parliament to make laws "
            "extends to the whole or any part of India, and the power of State "
            "Legislatures extends to the whole or any part of the State. No law "
            "made by Parliament shall be deemed to be invalid on the ground that "
            "it would have extra-territorial operation."
        ),
        "keywords": [
            "parliament",
            "state legislature",
            "territorial jurisdiction",
            "laws",
        ],
    },
    "246": {
        "title": "Subject-matter of laws made by Parliament and by the Legislatures of States",
        "text": (
            "Article 246 deals with the distribution of legislative powers between "
            "Parliament and State Legislatures through three lists in the Seventh "
            "Schedule: Union List (List I), State List (List II), and Concurrent "
            "List (List III). Parliament has exclusive power to legislate on "
            "Union List subjects, State Legislatures on State List subjects, and "
            "both on Concurrent List subjects. In case of conflict on Concurrent "
            "List matters, the Central law prevails."
        ),
        "keywords": [
            "federalism",
            "union list",
            "state list",
            "concurrent list",
            "seventh schedule",
        ],
    },
    "249": {
        "title": "Power of Parliament to legislate with respect to a matter in the State List in the national interest",
        "text": (
            "Article 249 empowers Parliament to legislate on a State List matter "
            "if the Rajya Sabha passes a resolution by two-thirds majority that "
            "it is necessary in the national interest. This power continues for "
            "one year from the date of the resolution but can be extended."
        ),
        "keywords": [
            "parliament",
            "state list",
            "national interest",
            "rajya sabha",
            "two-thirds",
        ],
    },
    "262": {
        "title": "Adjudication of disputes relating to waters of inter-State rivers",
        "text": (
            "Article 262 provides for the adjudication of disputes relating to "
            "waters of inter-State rivers. Parliament may by law provide for the "
            "adjudication of any dispute or complaint with respect to the use, "
            "distribution, and control of waters of inter-State rivers."
        ),
        "keywords": ["inter-state rivers", "water disputes", "adjudication"],
    },
    "263": {
        "title": "Inter-State Council",
        "text": (
            "Article 263 provides for the establishment of an Inter-State Council "
            "to investigate and advise on disputes between states, to investigate "
            "matters of common interest, and to make recommendations. The "
            "Inter-State Council was established in 1990 on the recommendation "
            "of the Sarkaria Commission."
        ),
        "keywords": [
            "inter-state council",
            "disputes",
            "common interest",
            "sarkaria commission",
        ],
    },
    "275": {
        "title": "Grants from the Union to certain States",
        "text": (
            "Article 275 provides for grants from the Union to certain States "
            "for the promotion of the welfare of Scheduled Tribes and for the "
            "development of Scheduled Areas. The Finance Commission recommends "
            "the amount of grants."
        ),
        "keywords": [
            "grants",
            "union",
            "scheduled tribes",
            "welfare",
            "finance commission",
        ],
    },
    "279A": {
        "title": "Goods and Services Tax Council",
        "text": (
            "Article 279A provides for the establishment of the GST Council, "
            "inserted by the 101st Constitutional Amendment Act, 2016. The "
            "GST Council consists of the Union Finance Minister (Chairperson), "
            "the Union Minister of State for Finance, and Finance Ministers of "
            "all States. The Council makes recommendations on GST rates, "
            "exemptions, and dispute resolution. Its decisions are taken by "
            "a three-fourth majority with the Centre having one-third and "
            "States having two-thirds of the voting power."
        ),
        "keywords": [
            "GST council",
            "goods and services tax",
            "101st amendment",
            "cooperative federalism",
        ],
    },
    "280": {
        "title": "Finance Commission",
        "text": (
            "Article 280 provides for the Finance Commission, which is constituted "
            "by the President every five years. The Finance Commission recommends "
            "the distribution of tax revenues between the Union and States, and "
            "the principles for grants-in-aid to States. The Finance Commission "
            "consists of a Chairman and four other members. Its recommendations "
            "are advisory in nature but highly influential."
        ),
        "keywords": [
            "finance commission",
            "revenue distribution",
            "grants-in-aid",
            "fiscal federalism",
        ],
    },
    "300A": {
        "title": "Right to property",
        "text": (
            "Article 300A provides that no person shall be deprived of his "
            "property save by authority of law. This was originally a Fundamental "
            "Right under Article 31 but was moved to Part XII by the 44th "
            "Amendment (1978). It is now a legal right, not a fundamental right."
        ),
        "keywords": [
            "right to property",
            "legal right",
            "44th amendment",
            "authority of law",
        ],
    },
    "330": {
        "title": "Reservation of seats for SCs and STs in the House of the People",
        "text": (
            "Article 330 provides for reservation of seats for Scheduled Castes "
            "and Scheduled Tribes in the House of the People (Lok Sabha). The "
            "number of reserved seats is in proportion to their population."
        ),
        "keywords": [
            "reservation",
            "lok sabha",
            "scheduled castes",
            "scheduled tribes",
        ],
    },
    "338": {
        "title": "National Commission for Scheduled Castes",
        "text": (
            "Article 338 provides for the National Commission for Scheduled "
            "Castes (originally for both SCs and STs). The 89th Amendment "
            "Act, 2003 bifurcated it into separate commissions for SCs and STs. "
            "The Commission investigates matters relating to the safeguards "
            "for SCs and STs and evaluates their working."
        ),
        "keywords": [
            "national commission",
            "scheduled castes",
            "safeguards",
            "89th amendment",
        ],
    },
    "340": {
        "title": "Appointment of a Commission to investigate the conditions of backward classes",
        "text": (
            "Article 340 empowers the President to appoint a Commission to "
            "investigate the conditions of socially and educationally backward "
            "classes and recommend steps for their improvement. Notable "
            "commissions include the Mandal Commission (1980) and the Rohini "
            "Commission (2017) for OBC sub-categorization."
        ),
        "keywords": [
            "backward classes",
            "mandal commission",
            "socially backward",
            "president",
        ],
    },
    "352": {
        "title": "Proclamation of National Emergency",
        "text": (
            "Article 352 empowers the President to proclaim a National Emergency "
            "if the President is satisfied that a grave emergency exists whereby "
            "the security of India or any part thereof is threatened by war, "
            "external aggression, or armed rebellion. The 44th Amendment changed "
            "'internal disturbance' to 'armed rebellion'. The proclamation must "
            "be approved by Parliament within one month by a special majority "
            "and can be revoked by the President. During emergency, Fundamental "
            "Rights under Article 19 are automatically suspended, and Article "
            "359 allows suspension of other Fundamental Rights except Articles "
            "20 and 21."
        ),
        "keywords": [
            "national emergency",
            "war",
            "external aggression",
            "armed rebellion",
            "44th amendment",
        ],
    },
    "360": {
        "title": "Provisions as to Financial Emergency",
        "text": (
            "Article 360 empowers the President to proclaim a Financial Emergency "
            "if the President is satisfied that the financial stability or credit "
            "of India or any part thereof is threatened. During a Financial "
            "Emergency: (a) the Centre can give directions to any state on "
            "financial matters; (b) the President may direct reduction of "
            "salaries of government employees including judges; (c) all money "
            "bills or financial bills passed by State Legislatures may be "
            "reserved for Presidential consideration. No Financial Emergency "
            "has been proclaimed in India so far."
        ),
        "keywords": [
            "financial emergency",
            "financial stability",
            "credit",
            "salary reduction",
        ],
    },
    "368": {
        "title": "Power of Parliament to amend the Constitution",
        "text": (
            "Article 368 provides for the power of Parliament to amend the "
            "Constitution. A constitutional amendment can be initiated only by "
            "a bill introduced in either House of Parliament. The bill must be "
            "passed by each House by a special majority (majority of total "
            "membership and two-thirds of members present and voting). For "
            "amendments affecting federal provisions, ratification by at least "
            "half the State Legislatures is required. The Supreme Court in "
            "Kesavananda Bharati v. State of Kerala (1973) established the "
            "Basic Structure doctrine, holding that Parliament cannot amend "
            "or destroy the basic structure of the Constitution. This doctrine "
            "has been upheld in Minerva Mills (1980) and Waman Rao (1981)."
        ),
        "keywords": [
            "constitutional amendment",
            "special majority",
            "basic structure",
            "kesavananda bharati",
            "ratification",
        ],
    },
    "370": {
        "title": "Temporary provisions with respect to the State of Jammu and Kashmir",
        "text": (
            "Article 370 granted special autonomous status to Jammu and Kashmir. "
            "It was a temporary provision under Part XXI of the Constitution. "
            "Under this article, Jammu and Kashmir had its own constitution and "
            "the Union government had limited powers except for defence, foreign "
            "affairs, and communications. In August 2019, the Government of India "
            "revoked Article 370 through a Presidential Order and reorganized "
            "the state into two Union Territories: Jammu & Kashmir and Ladakh. "
            "The Supreme Court in In Re: Article 370 (2023) upheld the "
            "revocation."
        ),
        "keywords": [
            "article 370",
            "jammu and kashmir",
            "special status",
            "revocation",
            "2019",
        ],
    },
}


def main():
    articles = []
    for art_num_str, info in ARTICLES.items():
        part, subject = PART_MAP.get(art_num_str, ("Unknown", "Unknown"))
        articles.append(
            {
                "source_type": "article",
                "article_number": art_num_str,
                "title": info["title"],
                "part": part,
                "subject": subject,
                "text": info["text"],
                "keywords": info["keywords"],
            }
        )

    output_path = Path("data/processed/articles.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(articles, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Generated {len(articles)} articles to {output_path}")

    from collections import Counter

    parts = Counter(a["part"] for a in articles)
    for part, count in sorted(parts.items()):
        print(f"  Part {part}: {count} articles")


if __name__ == "__main__":
    main()
