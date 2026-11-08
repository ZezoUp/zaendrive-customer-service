"""Small, explicit input/output checks for the rental assistant's scope.

These rules block common instruction overrides and programming requests without
asking the model to judge its own behaviour. They are not a general semantic
classifier or a guarantee against every possible prompt attack.
"""

import re
import unicodedata
from dataclasses import dataclass

OUT_OF_SCOPE = "I can only help with ZaenDrive rentals, vehicles and rental conditions."
PRIVATE_INSTRUCTIONS = "I cannot share internal instructions or API settings."


def normalized(text):
    text = unicodedata.normalize("NFKC", text).casefold()
    # Remove zero-width formatting characters, not ordinary word boundaries.
    return " ".join("".join(c for c in text if unicodedata.category(c) != "Cf").split())


@dataclass(frozen=True)
class GuardDecision:
    category: str
    answer: str


PRIVATE_PATTERNS = [
    r"\b(?:print|show|reveal|repeat|display|expose|give|tell|what|dump|output)\b.{0,100}\b(?:system[ -]prompt|hidden[ -](?:prompt|instructions)|internal[ -]instructions|api[ -](?:key|secret)|secret[ -]key)\b",
    r"\b(?:zeige|verrate|drucke|wiederhole|nenne)\b.{0,100}\b(?:system[ -]?prompt|interne[nr]? anweisungen|api[ -]schl[uü]ssel)\b",
]
PROGRAMMING_TOPIC = r"(?:python|javascript|typescript|java|c\+\+|c#|sql|bash|programming|coding|source code|sorting|sortieralgorithmus|algorithm|algorithms|merge[ -]?sort|quick[ -]?sort)"
PROGRAMMING_PATTERNS = [
    r"\b(?:write|implement|explain|create|generate|provide|teach|show|give|describe|schreib\w*|erkl[aä]r\w*|implementier\w*)\b.{0,140}" + PROGRAMMING_TOPIC,
    r"\b(?:how|what)\b.{0,70}" + PROGRAMMING_TOPIC,
    r"\b(?:python|javascript|typescript|sql|bash)\s+(?:code|script|implementation|tutorial|sorting)\b",
    r"\b(?:sorted|merge_sort|quick_sort)\s*\(",
]
OVERRIDE_PATTERNS = [
    r"\b(?:ignore|disregard|forget|override)\s+(?:all\s+)?(?:the\s+)?(?:(?:previous|prior|above|earlier)\s+)?(?:instructions|system\s+(?:prompt|instructions|rules)|your\s+(?:instructions|rules|rental rules))\b",
    r"\byou are\s+(?:now\s+)?(?:an?\s+)?(?:unrestricted|unlimited|unfiltered|uncensored)\s+(?:assistant|ai|chatbot)\b",
    r"\bignoriere\s+(?:alle\s+)?(?:(?:bisherigen|vorherigen)\s+)?(?:anweisungen|regeln)\b",
    r"\bdu bist\s+(?:jetzt\s+)?(?:ein\s+)?(?:unbeschr[aä]nkter|uneingeschr[aä]nkter)\s+assistent\b",
]


def inspect_input(question):
    text = normalized(question)
    if any(re.search(pattern, text) for pattern in PRIVATE_PATTERNS):
        return GuardDecision("private_instructions", PRIVATE_INSTRUCTIONS)
    if any(re.search(pattern, text) for pattern in PROGRAMMING_PATTERNS):
        return GuardDecision("programming_request", OUT_OF_SCOPE)
    if any(re.search(pattern, text) for pattern in OVERRIDE_PATTERNS):
        return GuardDecision("instruction_override", OUT_OF_SCOPE)
    return None


def inspect_output(answer):
    text = normalized(answer)
    if re.search(r"(?:^|\n)\s*(?:1\.\s*)?ROLE AND GOAL\b", answer, re.I) or (
        "3. interaction rules" in text and "4. refusals and special cases" in text
    ):
        return GuardDecision("internal_prompt_output", PRIVATE_INSTRUCTIONS)
    code_fence = r"```\s*(?:python|py\b|javascript|js\b|typescript|java\b|sql\b|bash\b|shell\b|c\+\+|cpp\b)"
    code_definition = r"(?:^|\n)\s*(?:def\s+\w+\s*\(|class\s+\w+\s*[:(]|function\s+\w+\s*\()"
    code_expression = r"\b(?:sorted\s*\(|list\.sort\s*\(|merge_sort\s*\(|quick_sort\s*\()"
    if re.search(code_fence, text) or re.search(code_definition, answer) or re.search(code_expression, text):
        return GuardDecision("programming_output", OUT_OF_SCOPE)
    return None
