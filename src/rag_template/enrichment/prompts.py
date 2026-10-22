"""
prompts.py: the prompt sets used by the enricher.

A PromptSet builds the (system, user) messages for each LLM stage:

    metadata      summary + tags + triplets for a chunk
    questions     Pass 1: question candidates with a verbatim source quote (one call per level)
    answer        Pass 2: a reference answer written from the source quote only
    combined_qa   (only `combined` sets) questions AND answers in a single call per chunk

Every stage knows the chunk's content type (prose | table | math | code) because good questions about
a function are not good questions about a paragraph. Sets are registered by name in PROMPT_SETS and
chosen with RAG_PROMPT_SET (or `LLMClient(prompts=...)`).

    grounded           strict, extractive rules; no examples
    fewshot            grounded + a worked good/bad example per content type (default)
    combined_fewshot   fewshot, but one call per chunk returns questions and answers (fewer calls;
                       the answer is not written from a clean quote-only context, so check the
                       rejection rate on your model)

The wording was tuned on a small local model. Prompts are the cheapest thing to change and the easiest
to make worse: measure on a gold set before and after.
"""

from dataclasses import dataclass
from typing import Dict

DEFLECTION_SENTINEL = "NOT_ENOUGH_INFORMATION"


@dataclass(frozen=True)
class Prompt:
    system: str
    user: str


# ------------------------------------------------------------------------------- levels

_LEVELS_PROSE = {
    "Easy": "RECALL: a single fact, definition, name or number that the chunk states outright",
    "Medium": "EXPLAIN: how or why something works, exactly as the chunk explains it (one mechanism or one cause)",
    "Hard": "CONNECT: combine two or more statements from the chunk (compare two things, or link a cause to an "
    "effect the chunk states); everything needed must still be in the chunk",
}
_LEVELS_MATH = {
    "Easy": "definition or notation: ask what a symbol, term, or operator means",
    "Medium": "computation: ask what the formula computes or what its components represent",
    "Hard": "derivation or proof: ask why the formula takes this form, what assumption it relies on, or what happens if a constraint is relaxed",
}
_LEVELS_CODE = {
    "Easy": "WHAT: what a named function, class, constant or parameter is for, what it returns, or which value it uses",
    "Medium": "HOW: how the code does it: the order of steps, which helpers it calls, how errors or edge cases are handled",
    "Hard": "WHY / CONNECT: why the code is written that way as far as the code or its comments say, or how two parts "
    "of the chunk depend on each other; everything needed must still be in the chunk",
}

_QUESTION_RULES = """\
1. Answerable from the TARGET CHUNK alone. Do not use outside knowledge.
2. Self-contained: a reader who has not seen the chunk must understand the question. Never write
   "the passage", "the text", "the chunk", "the section", "the author", "the figure", or "according to".
   Name the concept explicitly instead.
3. One concept per question. No two-part questions.
4. "source_quote" is copied word for word from the chunk (one to three sentences, at least 40 characters)
   and contains everything needed to answer.
5. Each question targets a different fact or mechanism.
6. Do not write answers here."""

_QUESTION_RULES_CODE = """\
1. Answerable from the TARGET CHUNK alone. Do not use outside knowledge about the library or project.
2. Self-contained: name the function, class or variable explicitly. Never write "this function",
   "the code", "the snippet" or "the chunk".
3. One concept per question. No two-part questions.
4. "source_quote" is copied character for character from the chunk (one to six consecutive lines of code
   or comments, at least 25 characters) and contains everything needed to answer.
5. Each question targets a different behaviour.
6. Do not write answers here."""

_ANSWER_RULES = """\
1. Answer in 1-2 sentences (at most 45 words).
2. Use ONLY what the KEY PASSAGE says. Reuse its own terms, names and numbers. Do not add examples,
   purposes, benefits, background or comparisons that it does not state.
3. For how/why questions, state the mechanism in the passage's own causal wording.
4. Start directly with the substance. Do not repeat the question. Do not write "the passage", "the text",
   "the source" or "according to".
5. No hedging (never "likely", "may", "possibly", "could").
6. If the KEY PASSAGE does not answer the question, output EXACTLY: NOT_ENOUGH_INFORMATION"""

_ANSWER_RULES_CODE = """\
1. Answer in 1-3 sentences (at most 60 words).
2. Use ONLY what the KEY PASSAGE shows. Put every identifier, argument, constant and literal you mention
   in `backticks`, spelled exactly as in the code. Never mention a name that is not in the passage.
3. Describe behaviour, not intent that the code does not show. Do not guess what callers do.
4. Start directly with the substance. Do not repeat the question. Do not write "the code", "the snippet"
   or "the passage".
5. If the KEY PASSAGE does not answer the question, output EXACTLY: NOT_ENOUGH_INFORMATION"""

# ----------------------------------------------------------------------------- examples

_EX_CHUNK = (
    "Photosynthesis takes place in the chloroplasts. In the light-dependent reactions, chlorophyll absorbs "
    "light and splits water, releasing oxygen. The Calvin cycle then uses ATP and NADPH to fix carbon "
    "dioxide into glucose."
)
_EX_CODE = '''def retry(fn, attempts=3, delay=0.5):
    """Call fn until it succeeds."""
    for i in range(attempts):
        try:
            return fn()
        except OSError:
            time.sleep(delay * 2 ** i)
    raise RuntimeError("gave up")'''


def _examples_prose(with_answer: bool) -> str:
    ans = lambda a: f', "answer": "{a}"' if with_answer else ""  # noqa: E731
    return f"""
### EXAMPLE (different topic, do not reuse its wording)
Chunk: "{_EX_CHUNK}"
GOOD:
 {{"question": "What does the Calvin cycle use to fix carbon dioxide into glucose?", "source_quote": "The Calvin cycle then uses ATP and NADPH to fix carbon dioxide into glucose."{ans("The Calvin cycle uses ATP and NADPH to fix carbon dioxide into glucose.")}, "difficulty": "Easy"}}
 {{"question": "What happens to water in the light-dependent reactions?", "source_quote": "In the light-dependent reactions, chlorophyll absorbs light and splits water, releasing oxygen."{ans("Chlorophyll absorbs light and splits water, releasing oxygen.")}, "difficulty": "Medium"}}
BAD (never do this):
 {{"question": "According to the passage, why is photosynthesis important?", ...}}  <- refers to "the passage" and asks for something the chunk does not state
"""


def _examples_code(with_answer: bool) -> str:
    ans = lambda a: f', "answer": "{a}"' if with_answer else ""  # noqa: E731
    return f"""
### EXAMPLE (different code, do not reuse its wording)
Chunk:
{_EX_CODE}
GOOD:
 {{"question": "What does retry raise when every attempt fails?", "source_quote": "raise RuntimeError(\\"gave up\\")"{ans("It raises `RuntimeError` with the message `gave up`.")}, "difficulty": "Easy"}}
 {{"question": "How does retry wait between attempts?", "source_quote": "time.sleep(delay * 2 ** i)"{ans("It sleeps for `delay * 2 ** i` seconds, so the wait doubles after each failed attempt.")}, "difficulty": "Medium"}}
BAD (never do this):
 {{"question": "What does this function do?", ...}}  <- not self-contained
 {{"question": "Why does retry only catch OSError?", ...}}  <- the code gives no reason
"""


# ----------------------------------------------------------------------------- prompt sets


class PromptSet:
    """Grounded, extractive prompts. Subclasses add examples or switch to one combined call."""

    name = "grounded"
    combined = False

    # ---- levels

    def difficulty_instructions(self, content_type: str) -> Dict[str, str]:
        if content_type == "math":
            return dict(_LEVELS_MATH)
        if content_type == "code":
            return dict(_LEVELS_CODE)
        return dict(_LEVELS_PROSE)

    def _rules(self, content_type: str):
        if content_type == "code":
            return _QUESTION_RULES_CODE, _ANSWER_RULES_CODE
        return _QUESTION_RULES, _ANSWER_RULES

    def _examples(self, content_type: str, with_answer: bool) -> str:
        return ""

    def _answer_examples(self, content_type: str) -> str:
        return ""

    # ---- stage 1: metadata

    def metadata(self, text: str, context: str, content_type: str = "prose") -> Prompt:
        system = (
            "You are a precise Knowledge Graph Extractor. "
            "Extract information ONLY from the TEXT CHUNK, never from the context. "
            "Always output valid JSON following the exact schema provided."
        )
        if content_type == "code":
            tag_rule = "2-5 identifiers or concepts that appear in the code (function, class or variable names, protocols, algorithms). Use lowercase_with_underscores."
            summary_rule = "Write exactly 2 complete sentences. Sentence 1: what the code does. Sentence 2: the notable inputs, outputs, side effects or error handling. Never start with 'The code', 'This chunk' or 'This function'."
            triplet_rule = 'Subject-predicate-object triples where BOTH subject and object are names from the code (e.g. {"subject": "retry", "predicate": "calls", "object": "time.sleep"}).'
        else:
            tag_rule = "2-5 noun phrases that appear explicitly in the TEXT CHUNK. Use lowercase_with_underscores. Do not use generic tags like \"data\" or \"overview\"."
            summary_rule = "Write exactly 2 complete sentences. Sentence 1: state the core concept or claim. Sentence 2: name the specific methods, techniques, or entities mentioned. Never start with 'The text', 'This chunk', or 'This section'."
            triplet_rule = 'Subject-predicate-object triples where BOTH subject and object appear in the TEXT CHUNK. The predicate is one verb or short verb phrase (e.g. "uses", "generates", "specializes_for").'
        user = f"""
### BACKGROUND CONTEXT (orientation only. DO NOT extract tags, triplets, or summary from here):
{context}

### TEXT CHUNK (your only source):
{text}

### TASK
Analyse ONLY the TEXT CHUNK and return EXACTLY this JSON structure.

### RULES
1. Tags: {tag_rule} Do not invent tags.
2. Triplets: {triplet_rule} Aim for 1-4 high-quality triplets; return an empty list if none are meaningful.
3. Summary: {summary_rule}

{{
"summary": "[2-sentence factual summary]",
"tags": ["tag1", "tag2"],
"triplets": [{{"subject": "Entity", "predicate": "verb_phrase", "object": "Entity"}}]
}}
"""
        return Prompt(system, user)

    # ---- stage 2: question candidates

    def questions(self, chunk_content: str, context: str, difficulty: str, instruction: str, per_diff: int, content_type: str = "prose") -> Prompt:
        q_rules, _ = self._rules(content_type)
        system = "You are an expert who writes precise questions from a source text. Output ONLY valid JSON."
        user = f"""\
### BACKGROUND CONTEXT (orientation only, never a source for questions):
{context}

### TARGET CHUNK (the only source):
{chunk_content}

### TASK
Write up to {per_diff} '{difficulty}' question(s). Level: {instruction}.

### RULES
{q_rules}
{self._examples(content_type, with_answer=False)}
### OUTPUT (JSON only)
{{"qa_pairs": [ {{"question": "...", "source_quote": "...", "difficulty": "{difficulty}"}} ]}}
"""
        return Prompt(system, user)

    # ---- stage 3: reference answer

    def answer(self, question: str, chunk_content: str, source_quote: str = "", content_type: str = "prose") -> Prompt:
        _, a_rules = self._rules(content_type)
        system = (
            "You write short model answers to questions. You state only what the source says, "
            "in its own words, and never add anything from outside it. Output ONLY the answer text."
        )
        has_quote = bool(source_quote and len(source_quote.strip()) >= 25)
        passage = source_quote.strip() if has_quote else chunk_content
        label = "KEY PASSAGE" if has_quote else "SOURCE TEXT"
        user = f"""\
### {label}
{passage}

### QUESTION
{question}

### RULES
{a_rules}
{self._answer_examples(content_type)}"""
        return Prompt(system, user)

    def combined_qa(self, chunk_content: str, context: str, per_diff: int, content_type: str) -> Prompt:
        raise NotImplementedError(f"prompt set '{self.name}' is not a combined set")


class FewShotPrompts(PromptSet):
    """Grounded prompts plus a worked example (from an unrelated topic) of good and bad output."""

    name = "fewshot"

    def _examples(self, content_type: str, with_answer: bool) -> str:
        return _examples_code(with_answer) if content_type == "code" else _examples_prose(with_answer)

    def _answer_examples(self, content_type: str) -> str:
        if content_type == "code":
            return """
### EXAMPLE (different code)
KEY PASSAGE: "time.sleep(delay * 2 ** i)"
QUESTION: How does retry wait between attempts?
GOOD: It sleeps for `delay * 2 ** i` seconds, so the wait doubles after each failed attempt.
BAD: It uses `exponential_backoff` with jitter to avoid thundering herds. (names and behaviour the passage does not show)
"""
        return """
### EXAMPLE (different topic)
KEY PASSAGE: "The Calvin cycle then uses ATP and NADPH to fix carbon dioxide into glucose."
QUESTION: What does the Calvin cycle use to fix carbon dioxide into glucose?
GOOD: The Calvin cycle uses ATP and NADPH to fix carbon dioxide into glucose.
BAD: The Calvin cycle uses ATP and NADPH, which helps plants grow and is important for the food chain. (adds things the passage does not say)
"""


class CombinedFewShotPrompts(FewShotPrompts):
    """One call per chunk returns the questions AND their answers."""

    name = "combined_fewshot"
    combined = True

    def _examples(self, content_type: str, with_answer: bool = True) -> str:
        return super()._examples(content_type, with_answer=True)

    def combined_qa(self, chunk_content: str, context: str, per_diff: int, content_type: str) -> Prompt:
        levels = self.difficulty_instructions(content_type)
        level_lines = "\n".join(f"- {name}: {text}" for name, text in levels.items())
        q_rules, a_rules = self._rules(content_type)
        system = "You are an expert who writes precise questions and short, faithful model answers from a source text. Output ONLY valid JSON."
        user = f"""\
### BACKGROUND CONTEXT (orientation only, never a source):
{context}

### TARGET CHUNK (the only source):
{chunk_content}

### TASK
Write up to {per_diff} question(s) for EACH level, each with a model answer:
{level_lines}

### QUESTION RULES
{q_rules}

### ANSWER RULES (the answer must be supported by that question's source_quote)
{a_rules}
{self._examples(content_type, with_answer=True)}
### OUTPUT (JSON only)
{{"qa_pairs": [ {{"question": "...", "source_quote": "...", "answer": "...", "difficulty": "Easy|Medium|Hard"}} ]}}
"""
        return Prompt(system, user)


PROMPT_SETS: Dict[str, PromptSet] = {p.name: p for p in (PromptSet(), FewShotPrompts(), CombinedFewShotPrompts())}
DEFAULT_PROMPT_SET = "fewshot"


def get_prompt_set(name: str = "") -> PromptSet:
    """Resolve a prompt set by name (default: fewshot)."""
    name = (name or DEFAULT_PROMPT_SET).strip().lower()
    try:
        return PROMPT_SETS[name]
    except KeyError:
        raise ValueError(f"unknown prompt set '{name}'; choose from {sorted(PROMPT_SETS)}") from None
