import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from sentence_transformers import CrossEncoder
from bert_score import BERTScorer


class AnswerScorer:
    def __init__(self):
        # ---- QA ----
        self.qa_pipeline = pipeline(
            "question-answering",
            model="deepset/deberta-v3-large-squad2",
        )

        # ---- BERTScore: semantic similarity between student answer and answer key ----
        # rescale_with_baseline=False avoids needing an extra baseline-stats
        # download, which matters for the offline-first setup.
        self.bert_scorer = BERTScorer(lang="en", rescale_with_baseline=False)

    # -------------------------------------------------------------
    # Existing low-level model calls (unchanged)
    # -------------------------------------------------------------

    def bert_score(self, answer: str, reference: str) -> float:
        """
        Semantic similarity (F1) between the student's answer and the
        teacher's answer key — this is BERTScore in the formula.
        """
        P, R, F1 = self.bert_scorer.score([answer], [reference])
        return F1.item()

    # -------------------------------------------------------------
    # Formula: FinalScore = Σ G_i * BERTScore_i * (b_i / Σb_j)
    # -------------------------------------------------------------

    def score_question(self, story: str, question: str, answer: str, correct_answer: str) -> dict:
        """
        Computes G_i (gate) and BERTScore_i for a single question.
        The Bloom's weight (b_i) and normalization (Σb_j) are applied
        afterward, at the test level, since they need every question's
        weight to normalize correctly — see aggregate_final_score().
        """
        bertscore = self.bert_score(answer, correct_answer)
        #is_correct = bertscore > 0.6 

        return {
            "bert_score": bertscore,
            #"is_correct": is_correct,
        }

    @staticmethod
    def aggregate_final_score(question_scores: list, bloom_weights: list) -> float:
        """
        Applies the Bloom's-weighted normalization across all questions
        in a test: Σ [G_i * BERTScore_i * (b_i / Σb_j)]

        question_scores: list of dicts from score_question(), one per question
        bloom_weights: list of b_i values (same order/length as question_scores)

        Returns a value in [0, 1] — multiply by 100 for a percentage.
        """
        total_weight = sum(bloom_weights)
        if total_weight == 0:
            return 0.0

        final = 0.0
        for q_score, b_i in zip(question_scores, bloom_weights):
            final += q_score["bert_score"] * (b_i / total_weight)

        return final


_scorer = None


def get_scorer() -> AnswerScorer:
    global _scorer
    if _scorer is None:
        _scorer = AnswerScorer()
    return _scorer