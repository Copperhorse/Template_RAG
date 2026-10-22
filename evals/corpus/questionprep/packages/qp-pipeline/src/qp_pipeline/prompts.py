"""
prompts.py: the prompt sets used by the Enricher.

A PromptSet builds the (system, user) messages for each LLM stage:

    metadata      summary + tags + triplets for a chunk
    questions     Pass 1: question candidates with a verbatim source quote (one call per difficulty)
    answer        Pass 2: a reference answer written from the source quote
    combined_qa   (only `combined` sets) questions AND answers in a single call per chunk

Sets are registered by name in PROMPT_SETS and chosen with the QP_PROMPT_SET environment
variable (or `LLMClient(prompts=...)`). The default is `fewshot`, the best set measured in
evals/eval_enrichment.py (see evals/report.md). `baseline` reproduces the original prompts exactly
(pinned by tests/golden/enricher_baseline_prompts.json); the others are experiments.
"""

import os
from dataclasses import dataclass
from typing import Dict

DEFLECTION_SENTINEL = "NOT_ENOUGH_INFORMATION"


@dataclass(frozen=True)
class Prompt:
    system: str
    user: str


# --------------------------------------------------------------------------- baseline


class PromptSet:
    """The original prompts. Subclasses override single pieces."""

    name = "baseline"
    combined = False
    # Sentence appended to system prompts that tells reasoning models to think tersely. It was
    # written for LFM2.5; `nohint` removes it.
    reasoning_hint = "If you reason before answering, keep each reasoning step to 5 words or fewer. "

    # ---- stage 1: metadata

    def metadata(self, text: str, context: str) -> Prompt:
        system = (
            "You are a precise Technical Knowledge Graph Extractor. "
            f"{self.reasoning_hint}"
            + (
                "Stop reasoning the moment you have identified the tags, triplets, and summary — "
                "do not verify them a second time. "
                if self.reasoning_hint
                else ""
            )
            + "Extract information ONLY from the TEXT CHUNK — never from context. "
            "Always output valid JSON following the exact schema provided."
        )
        user = f"""
   ### BACKGROUND CONTEXT (strictly for orientation — DO NOT extract tags, triplets, or summary from here):
   {context}

   ### TEXT CHUNK — THIS IS YOUR ONLY SOURCE:
   {text}

   ### TASK:
   Analyse ONLY the TEXT CHUNK above and return EXACTLY this JSON structure.

   ### STRICT RULES:
   1. Tags: 2–5 noun phrases that appear explicitly in the TEXT CHUNK. Use lowercase_with_underscores.
      Examples: "weak_labels", "gan_training", "entity_augmentation", "semi_supervised_learning".
      Do not invent tags. Do not use generic tags like "data" or "machine_learning".
   2. Triplets: Create meaningful subject-predicate-object triples where BOTH subject and object appear in the TEXT CHUNK.
      Predicate must be a single verb or short verb phrase (e.g. "uses", "generates", "improves", "specializes_for").
      Aim for 1–4 high-quality triplets. If none are meaningful, return an empty list.
   3. Summary: Write exactly 2 complete sentences. Sentence 1: state the core technical concept or claim. Sentence 2: name the specific methods, techniques, or entities mentioned. Never start with 'The text', 'This chunk', or 'This section'.

   {{
   "summary": "[2-sentence factual summary]",
   "tags": ["tag1", "tag2", ...],
   "triplets": [
       {{"subject": "Entity", "predicate": "verb_phrase", "object": "Entity"}}
   ]
   }}
   """
        return Prompt(system, user)

    # ---- stage 2: question candidates

    def difficulty_instructions(self, content_type: str) -> Dict[str, str]:
        if content_type == "math":
            return {
                "Easy": "definition or notation — ask what a symbol, term, or operator means",
                "Medium": "computation — ask what the formula computes or what its components represent",
                "Hard": "derivation or proof — ask why the formula takes this form, what assumption it relies on, or what happens if a constraint is relaxed",
            }
        return {
            "Easy": "factual recall — ask about specific definitions, names, or stated facts",
            "Medium": "conceptual / mechanism — ask how or why something works",
            "Hard": "analytical / critical — ask about limitations, trade-offs, or comparisons",
        }

    def questions(
        self, chunk_content: str, context: str, difficulty: str, instruction: str, per_diff: int
    ) -> Prompt:
        system = (
            "You are an Expert Technical Interviewer. "
            f"{self.reasoning_hint}"
            "Output ONLY valid JSON."
        )
        user = f"""
### BACKGROUND CONTEXT (for understanding only — DO NOT use this for questions):
{context}

### TARGET TEXT CHUNK (You MUST extract questions and quotes ONLY from here):
{chunk_content}

### TASK:
Generate up to {per_diff} '{difficulty}' questions ({instruction}).

### STRICT RULES (NEVER VIOLATE):
1. NEVER copy, reuse, or paraphrase any example question or phrasing that appears anywhere in this prompt.
2. Do NOT use the word "X" or the phrase "is a bottleneck" in any question unless those exact words are in the chunk.
3. Every "question" MUST be answerable using ONLY the TARGET TEXT CHUNK.
4. Every "source_quote" MUST be verbatim sentence(s) from the TARGET TEXT CHUNK that actually contain the answer (minimum 25 characters).
5. Never generate answers here.
6. Every question MUST target a DIFFERENT concept, fact, or mechanism from the chunk.

Output ONLY:
{{"qa_pairs": [ {{"question": "...", "source_quote": "...", "difficulty": "{difficulty}"}}, ... ] }}
"""
        return Prompt(system, user)

    # ---- stage 3: reference answer

    def answer(self, question: str, chunk_content: str, source_quote: str = "") -> Prompt:
        system = (
            "You are a knowledgeable technical interviewer writing model reference answers. "
            "Your answers should read like what a well-prepared human candidate would say — "
            "complete, explanatory, and grounded in the source text. "
            "Output ONLY the answer text — no preamble, no meta-commentary."
        )
        quote_block = (
            f"\n### KEY PASSAGE (this is the specific part of the source that answers the question):\n{source_quote.strip()}\n"
            if source_quote and len(source_quote.strip()) >= 25
            else ""
        )
        user = f"""
### SOURCE TEXT:
{chunk_content}
{quote_block}
### QUESTION:
{question}

### INSTRUCTIONS:
Write a reference answer that a well-prepared human candidate would give in a technical interview.
{"Focus your answer ONLY on explaining the KEY PASSAGE above." if quote_block else ""}

Rules (must follow exactly):
1. Use ONLY information stated in the SOURCE TEXT. Do not add outside knowledge.
2. Do NOT repeat the question or its premise. Start directly with the substance.
3. Explain using the exact details from the text — no added commentary.
4. NO EXTRAPOLATION: Do not add "this helps", "this is important because", "researchers can", or any concluding sentence unless the text itself says it.
5. Write in plain, clear prose (maximum 3 sentences). No bullet points.
6. If the text gives specific values, thresholds, or named techniques, include them.
7. If the core subject is completely absent from the source text, output EXACTLY: NOT_ENOUGH_INFORMATION
"""
        return Prompt(system, user)

    def combined_qa(self, chunk_content: str, context: str, per_diff: int, content_type: str) -> Prompt:
        raise NotImplementedError(f"prompt set '{self.name}' is not a combined set")


class NoHintPrompts(PromptSet):
    """Baseline without the LFM-specific 'reasoning steps of 5 words' instruction."""

    name = "nohint"
    reasoning_hint = ""


# -------------------------------------------------------------------------- grounded

_GROUNDED_DIFFICULTY = {
    "Easy": "RECALL — a single fact, definition, name or number that the chunk states outright",
    "Medium": "EXPLAIN — how or why something works, exactly as the chunk explains it (one mechanism or one cause)",
    "Hard": "CONNECT — combine two or more statements from the chunk (compare two things, or link a cause to an "
    "effect the chunk states); everything needed must still be in the chunk",
}

_GROUNDED_QUESTION_RULES = """\
1. Answerable from the TARGET TEXT CHUNK alone. Do not use outside knowledge.
2. Self-contained: a reader who has not seen the chunk must understand the question. Never write
   "the passage", "the text", "the chunk", "the section", "the author", "the figure", or "according to".
   Name the concept explicitly instead.
3. One concept per question. No two-part questions.
4. "source_quote" is copied word for word from the chunk (one to three sentences, at least 40 characters)
   and contains everything needed to answer.
5. Each question targets a different fact or mechanism.
6. Do not write answers here."""

_GROUNDED_ANSWER_RULES = """\
1. Answer in 1–2 sentences (at most 45 words).
2. Use ONLY what the KEY PASSAGE says. Reuse its own terms, names and numbers. Do not add examples,
   purposes, benefits, background or comparisons that it does not state.
3. Start directly with the substance. Do not repeat the question. Do not write "the passage", "the text",
   "the source" or "according to".
4. No hedging (never "likely", "may", "possibly", "could").
5. If the KEY PASSAGE does not answer the question, output EXACTLY: NOT_ENOUGH_INFORMATION"""


class GroundedPrompts(NoHintPrompts):
    """Stricter, extractive prompts: difficulty by cognitive level, self-contained questions,
    short answers that may only restate the source quote."""

    name = "grounded"
    question_rules = _GROUNDED_QUESTION_RULES
    answer_rules = _GROUNDED_ANSWER_RULES

    def difficulty_instructions(self, content_type: str) -> Dict[str, str]:
        if content_type == "math":
            return super().difficulty_instructions(content_type)
        return dict(_GROUNDED_DIFFICULTY)

    def questions(
        self, chunk_content: str, context: str, difficulty: str, instruction: str, per_diff: int
    ) -> Prompt:
        system = "You are an expert interviewer who writes precise questions from a source text. Output ONLY valid JSON."
        user = f"""\
### BACKGROUND CONTEXT (orientation only, never a source for questions):
{context}

### TARGET TEXT CHUNK (the only source):
{chunk_content}

### TASK
Write up to {per_diff} '{difficulty}' question(s). Level: {instruction}.

### RULES
{self.question_rules}
{self._examples()}
### OUTPUT (JSON only)
{{"qa_pairs": [ {{"question": "...", "source_quote": "...", "difficulty": "{difficulty}"}} ]}}
"""
        return Prompt(system, user)

    def _examples(self) -> str:  # hook for the few-shot subclass
        return ""

    def answer(self, question: str, chunk_content: str, source_quote: str = "") -> Prompt:
        system = (
            "You write short model answers for interview questions. You state only what the source "
            "says, in its own words, and never add anything from outside it. Output ONLY the answer text."
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
{self.answer_rules}
{self._answer_examples()}"""
        return Prompt(system, user)

    def _answer_examples(self) -> str:
        return ""

    def combined_qa(self, chunk_content: str, context: str, per_diff: int, content_type: str) -> Prompt:
        levels = self.difficulty_instructions(content_type)
        level_lines = "\n".join(f"- {name}: {text}" for name, text in levels.items())
        system = (
            "You are an expert interviewer who writes precise questions and short, faithful model "
            "answers from a source text. Output ONLY valid JSON."
        )
        user = f"""\
### BACKGROUND CONTEXT (orientation only, never a source):
{context}

### TARGET TEXT CHUNK (the only source):
{chunk_content}

### TASK
Write up to {per_diff} question(s) for EACH level, each with a model answer:
{level_lines}

### QUESTION RULES
{self.question_rules}

### ANSWER RULES (the answer must be supported by that question's source_quote)
{self.answer_rules}
{self._examples()}
### OUTPUT (JSON only)
{{"qa_pairs": [ {{"question": "...", "source_quote": "...", "answer": "...", "difficulty": "Easy|Medium|Hard"}} ]}}
"""
        return Prompt(system, user)


# --------------------------------------------------------------------------- few-shot

_EXAMPLE_CHUNK = (
    "Photosynthesis takes place in the chloroplasts. In the light-dependent reactions, chlorophyll absorbs "
    "light and splits water, releasing oxygen. The Calvin cycle then uses ATP and NADPH to fix carbon "
    "dioxide into glucose."
)


class FewShotPrompts(GroundedPrompts):
    """Grounded prompts plus a worked example (from an unrelated domain) of good and bad output."""

    name = "fewshot"

    def _examples(self) -> str:
        return f"""
### EXAMPLE (different topic, do not reuse its wording)
Chunk: "{_EXAMPLE_CHUNK}"
GOOD:
 {{"question": "What does the Calvin cycle use to fix carbon dioxide into glucose?", "source_quote": "The Calvin cycle then uses ATP and NADPH to fix carbon dioxide into glucose.", "difficulty": "Easy"}}
 {{"question": "What happens to water in the light-dependent reactions?", "source_quote": "In the light-dependent reactions, chlorophyll absorbs light and splits water, releasing oxygen.", "difficulty": "Medium"}}
BAD (never do this):
 {{"question": "According to the passage, why is photosynthesis important?", ...}}  <- refers to "the passage" and asks for something the chunk does not state
"""

    def _answer_examples(self) -> str:
        return """
### EXAMPLE (different topic)
KEY PASSAGE: "The Calvin cycle then uses ATP and NADPH to fix carbon dioxide into glucose."
QUESTION: What does the Calvin cycle use to fix carbon dioxide into glucose?
GOOD: The Calvin cycle uses ATP and NADPH to fix carbon dioxide into glucose.
BAD: The Calvin cycle uses ATP and NADPH, which helps plants grow and is important for the food chain. (adds things the passage does not say)
"""


class CombinedPrompts(GroundedPrompts):
    """Grounded rules, but questions and answers come from ONE call per chunk (fewer calls)."""

    name = "combined"
    combined = True


class CombinedFewShotPrompts(FewShotPrompts):
    name = "combined_fewshot"
    combined = True

    def _examples(self) -> str:
        return f"""
### EXAMPLE (different topic, do not reuse its wording)
Chunk: "{_EXAMPLE_CHUNK}"
GOOD:
 {{"question": "What does the Calvin cycle use to fix carbon dioxide into glucose?", "source_quote": "The Calvin cycle then uses ATP and NADPH to fix carbon dioxide into glucose.", "answer": "The Calvin cycle uses ATP and NADPH to fix carbon dioxide into glucose.", "difficulty": "Easy"}}
BAD (never do this):
 {{"question": "According to the passage, why is photosynthesis important?", "answer": "It helps plants grow and feeds the whole food chain.", ...}}  <- refers to "the passage", and the answer adds things the chunk does not state
"""


# ------------------------------------------------------------------------ bloom + few-shot

# Bloom's taxonomy squeezed into the three stored tiers (the DB only allows Easy/Medium/Hard).
# Apply/Analyze stays grounded: the situation is new, but every fact needed comes from the chunk.
_BLOOM_DIFFICULTY = {
    "Easy": "REMEMBER — a single fact, definition, name or number that the chunk states outright",
    "Medium": "UNDERSTAND — explain how or why something works, exactly as the chunk explains it "
    "(one mechanism or one cause)",
    "Hard": "APPLY / ANALYZE — a short situation or a comparison (\"what would happen if…\", \"how does X "
    "differ from Y\", \"which of these applies when…\") whose answer combines two or more facts the chunk "
    "states; everything needed must still be in the chunk",
}

_BLOOM_QUESTION_RULES = """\
1. Answerable from the TARGET TEXT CHUNK alone. Do not use outside knowledge.
2. Self-contained: a reader who has not seen the chunk must understand the question. Never write
   "the passage", "the text", "the chunk", "the section", "the author", "the figure", or "according to".
   Name the concept explicitly instead.
3. One concept per question. No two-part questions.
4. "source_quote" is copied word for word from the chunk (one to three consecutive sentences, at least
   40 characters) and contains everything needed to answer. A Hard question may need all three sentences.
5. Each question targets a different fact or mechanism.
6. Do not write answers here."""

_BLOOM_ANSWER_RULES = """\
1. As short as the question allows, at most 70 words. Easy answers are one sentence.
2. Use ONLY what the KEY PASSAGE says. Reuse its own terms, names and numbers. Do not add examples,
   purposes, benefits, background or comparisons that it does not state.
3. For how/why questions, state the mechanism in the passage's own causal wording.
4. Start directly with the substance. Do not repeat the question. Do not write "the passage", "the text",
   "the source" or "according to".
5. No hedging (never "likely", "may", "possibly", "could").
6. If the KEY PASSAGE does not answer the question, output EXACTLY: NOT_ENOUGH_INFORMATION"""


class BloomFewShotPrompts(FewShotPrompts):
    """Few-shot prompts whose three tiers follow Bloom's taxonomy (Remember / Understand /
    Apply-Analyze) instead of Recall / Explain / Connect."""

    name = "bloom_fewshot"
    question_rules = _BLOOM_QUESTION_RULES
    answer_rules = _BLOOM_ANSWER_RULES

    def difficulty_instructions(self, content_type: str) -> Dict[str, str]:
        if content_type == "math":
            return super().difficulty_instructions(content_type)
        return dict(_BLOOM_DIFFICULTY)

    def _examples(self) -> str:
        return f"""
### EXAMPLE (different topic, do not reuse its wording)
Chunk: "{_EXAMPLE_CHUNK}"
GOOD:
 {{"question": "What does the Calvin cycle use to fix carbon dioxide into glucose?", "source_quote": "The Calvin cycle then uses ATP and NADPH to fix carbon dioxide into glucose.", "difficulty": "Easy"}}
 {{"question": "How does chlorophyll release oxygen in the light-dependent reactions?", "source_quote": "In the light-dependent reactions, chlorophyll absorbs light and splits water, releasing oxygen.", "difficulty": "Medium"}}
 {{"question": "How do the light-dependent reactions differ from the Calvin cycle in what they do?", "source_quote": "In the light-dependent reactions, chlorophyll absorbs light and splits water, releasing oxygen. The Calvin cycle then uses ATP and NADPH to fix carbon dioxide into glucose.", "difficulty": "Hard"}}
BAD (never do this):
 {{"question": "According to the passage, why is photosynthesis important?", ...}}  <- refers to "the passage" and asks for something the chunk does not state
 {{"question": "Which stage would stop first if no light reached the chloroplast?", ...}}  <- looks like a scenario, but the chunk never says where ATP and NADPH come from
"""

    def _answer_examples(self) -> str:
        return """
### EXAMPLES (different topic)
KEY PASSAGE: "The Calvin cycle then uses ATP and NADPH to fix carbon dioxide into glucose."
QUESTION: What does the Calvin cycle use to fix carbon dioxide into glucose?
GOOD: The Calvin cycle uses ATP and NADPH to fix carbon dioxide into glucose.

KEY PASSAGE: "In the light-dependent reactions, chlorophyll absorbs light and splits water, releasing oxygen. The Calvin cycle then uses ATP and NADPH to fix carbon dioxide into glucose."
QUESTION: How do the light-dependent reactions differ from the Calvin cycle in what they do?
GOOD: The light-dependent reactions use chlorophyll to absorb light and split water, releasing oxygen, while the Calvin cycle uses ATP and NADPH to fix carbon dioxide into glucose.
BAD: The light-dependent reactions are more important because they power the whole plant. (adds things the passage does not say)
"""


# ---------------------------------------------------------------------------- registry

PROMPT_SETS: Dict[str, PromptSet] = {
    p.name: p
    for p in (
        PromptSet(),
        NoHintPrompts(),
        GroundedPrompts(),
        FewShotPrompts(),
        BloomFewShotPrompts(),
        CombinedPrompts(),
        CombinedFewShotPrompts(),
    )
}

DEFAULT_PROMPT_SET = "fewshot"


def get_prompt_set(name: str = "") -> PromptSet:
    """Resolve a prompt set by name, defaulting to QP_PROMPT_SET, then DEFAULT_PROMPT_SET."""
    name = (name or os.environ.get("QP_PROMPT_SET", "") or DEFAULT_PROMPT_SET).strip().lower()
    try:
        return PROMPT_SETS[name]
    except KeyError:
        raise ValueError(f"unknown prompt set '{name}'; choose from {sorted(PROMPT_SETS)}") from None
