"""
validator.py: the strict lexical -> bi-encoder -> NLI chain, used for maths chunks.

Maths answers are paraphrases of rigid formulas, so word-overlap gates (verify.py) are too noisy and
an entailment model earns its cost. Needs the `local` extra. Gates, in order:

  structure   1-5 sentences
  1 lexical   >= 30% of the answer's content words occur in the chunk
  2 bi-enc    cosine(answer, quote | chunk)
  3 NLI       contradiction -> reject; entailment -> needs a minimum bi-encoder score; otherwise the
              bi-encoder score is scaled down by the entailment probability
  4 question  "why"/"how" questions need a causal word in the answer
"""

import re
from typing import Set, Tuple

from rag_template import models


def _content_words(t: str) -> Set[str]:
    return {w.lower() for w in re.findall(r"[a-zA-Z]{4,}", t)}


class AnswerValidator:
    SIMILARITY_THRESHOLD = 0.50
    LEXICAL_OVERLAP_THRESHOLD = 0.30
    ENTAILMENT_THRESHOLD = 0.60
    CONTRADICTION_THRESHOLD = 0.60
    MIN_SENTENCES = 1
    MAX_SENTENCES = 5
    CAUSAL = {"because", "due to", "as a result", "therefore", "leads to", "causes", "through", "allows", "enables", "since"}

    def __init__(self, bi_model_name: str = models.BI_ENCODER_NAME, ce_model_name: str = models.NLI_CROSS_ENCODER_NAME):
        self.bi_encoder = models.get_bi_encoder(bi_model_name)
        self.cross_encoder = models.get_cross_encoder(ce_model_name)

    def validate(self, question: str, answer: str, chunk: str, source_quote: str) -> Tuple[bool, str]:
        import numpy as np
        from sentence_transformers import util

        if not answer or not answer.strip():
            return False, "Empty answer"
        count = self._sentence_count(answer)
        if not (self.MIN_SENTENCES <= count <= self.MAX_SENTENCES):
            return False, f"Structural fail: {count} sentences"

        # GATE 1: lexical
        a_words = _content_words(answer)
        if not a_words:
            return False, "No content words in answer"
        overlap = len(_content_words(chunk) & a_words) / len(a_words)
        if overlap < self.LEXICAL_OVERLAP_THRESHOLD:
            return False, f"Lexical fail: overlap={overlap:.2f} (gate is {self.LEXICAL_OVERLAP_THRESHOLD})"

        # GATE 2: bi-encoder (answer vs quote and vs chunk)
        ans, quote, chk = self.bi_encoder.encode([answer, source_quote, chunk], convert_to_tensor=True)
        bi_score = max(util.cos_sim(ans, quote).item(), util.cos_sim(ans, chk).item())

        # GATE 3: NLI (answer vs quote); label order of nli-deberta: contradiction, entailment, neutral
        logits = self.cross_encoder.predict([[source_quote, answer]])
        e = np.exp(np.array(logits[0], dtype=np.float64) - np.max(logits[0]))
        p_contra, p_entail, p_neutral = (e / e.sum())[:3]

        if p_contra > self.CONTRADICTION_THRESHOLD:
            return False, f"NLI Contradiction ({p_contra:.2f} > {self.CONTRADICTION_THRESHOLD})"
        if p_entail > self.ENTAILMENT_THRESHOLD:
            if bi_score < 0.40:
                return False, f"Entailed ({p_entail:.2f}), but bi-score too low ({bi_score:.2f})"
        else:
            adjusted = bi_score * (0.50 + 0.50 * p_entail)
            if adjusted < self.SIMILARITY_THRESHOLD:
                return False, f"Neutral NLI ({p_neutral:.2f}) dragged down bi-score: {adjusted:.2f} < {self.SIMILARITY_THRESHOLD}"

        # GATE 4: question heuristics
        if question.strip().lower().startswith(("why", "how")):
            low = answer.lower()
            words = set(low.split())
            if not any((w in low) if " " in w else (w in words) for w in self.CAUSAL):
                return False, "Why/How-question lacks causal/mechanism phrase"
        return True, ""

    @staticmethod
    def _sentence_count(text: str) -> int:
        return len([s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if len(s) > 5])
