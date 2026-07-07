import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from sentence_transformers import CrossEncoder


class AnswerScorer:
    """
    Loads the three correctness-checking models once and reuses them for
    every submission. Access via the module-level get_scorer() below
    rather than instantiating directly, so Django doesn't reload three
    transformer models per request.

    Bloom's Taxonomy classification is NOT handled here — that already
    happens once, at question-creation time, via ml/classifier.py.
    """

    def __init__(self):
        self.nli_name = "MoritzLaurer/deberta-v3-base-mnli-fever-anli"
        self.nli_tokenizer = AutoTokenizer.from_pretrained(self.nli_name)
        self.nli_model = AutoModelForSequenceClassification.from_pretrained(self.nli_name)
        self.nli_model.eval()

        self.qnli_name = "cross-encoder/qnli-distilroberta-base"
        self.qnli_model = CrossEncoder(self.qnli_name)

        self.qa_pipeline = pipeline(
            "question-answering",
            model="deepset/deberta-v3-large-squad2",
        )

    # -------------------------------------------------------------
    # Low-level model calls
    # -------------------------------------------------------------

    def nli_score(self, context: str, hypothesis: str) -> torch.Tensor:
        """Index 0 = entailment, 1 = neutral, 2 = contradiction (this checkpoint)."""
        inputs = self.nli_tokenizer(context, hypothesis, return_tensors="pt", truncation=True)
        with torch.no_grad():
            logits = self.nli_model(**inputs).logits
            probs = F.softmax(logits, dim=-1)[0]
        return probs

    def qnli_score(self, question: str, answer: str) -> float:
        score = self.qnli_model.predict([(question, answer)])[0]
        return torch.sigmoid(torch.tensor(score)).item()

    def qa_score(self, context: str, question: str, answer: str, correct_answer: str) -> dict:
        """
        Compares the student's answer against two references: the QA
        model's own extracted answer, and the teacher's stored answer key.
        """
        qa_result = self.qa_pipeline(question=question, context=context)
        expected_answer = qa_result["answer"]

        qa_forward = self.nli_score(expected_answer, answer)
        qa_backward = self.nli_score(answer, expected_answer)
        qa_entailment = max(qa_forward[0], qa_backward[0]).item()

        key_forward = self.nli_score(correct_answer, answer)
        key_backward = self.nli_score(answer, correct_answer)
        key_entailment = max(key_forward[0], key_backward[0]).item()

        best_entailment = max(qa_entailment, key_entailment)
        best_source = "qa" if qa_entailment >= key_entailment else "key"

        return {
            "qa_entailment": qa_entailment,
            "key_entailment": key_entailment,
            "best_entailment": best_entailment,
            "best_source": best_source,
            "expected_answer": expected_answer,
            "correct_answer": correct_answer,
        }
    # -------------------------------------------------------------
    # Independent evaluations
    # -------------------------------------------------------------

    def evaluate_grounded(self, story: str, answer: str) -> dict:
        story_score = self.nli_score(story, answer)
        story_entailment = story_score[0].item()
        story_neutral = story_score[1].item()
        story_contradiction = story_score[2].item()
        is_grounded = story_entailment > 0.6

        return {
            "is_grounded": int(is_grounded),
            "story_entailment": story_entailment,
            "story_neutral": story_neutral,
            "story_contradiction": story_contradiction,
        }

    def evaluate_relevant(self, question: str, answer: str) -> dict:
        qnli_relevance = self.qnli_score(question, answer)
        is_relevant = qnli_relevance > 0.6

        return {
            "is_relevant": int(is_relevant),
            "question_relevance": qnli_relevance,
        }

    def evaluate_similar(self, story: str, question: str, answer: str, correct_answer: str) -> dict:
        qa_result = self.qa_score(story, question, answer, correct_answer)

        is_similar = qa_result["best_entailment"] > 0.6

        return {
            "is_similar": int(is_similar),
            "best_entailment": qa_result["best_entailment"],
            "best_source": qa_result["best_source"],
            "qa_entailment": qa_result["qa_entailment"],
            "key_entailment": qa_result["key_entailment"],
            "expected_answer": qa_result["expected_answer"],
            "correct_answer": qa_result["correct_answer"],
        }
    # -------------------------------------------------------------
    # Combined grading decision
    # -------------------------------------------------------------

    def determine_correctness(self, story: str, question: str, answer: str, correct_answer: str) -> tuple:
        grounded_result = self.evaluate_grounded(story, answer)
        if not grounded_result["is_grounded"]:
            return False, {
                "stage_failed": "grounded",
                "is_grounded": False,
                "is_relevant": None,
                "is_similar": None,
            }

        relevant_result = self.evaluate_relevant(question, answer)
        if not relevant_result["is_relevant"]:
            return False, {
                "stage_failed": "relevant",
                "is_grounded": True,
                "is_relevant": False,
                "is_similar": None,
            }

        similar_result = self.evaluate_similar(story, question, answer, correct_answer)
        is_correct = bool(similar_result["is_similar"])

        return is_correct, {
            "stage_failed": None if is_correct else "similar",
            "is_grounded": True,
            "is_relevant": True,
            "is_similar": is_correct,
            "best_entailment": similar_result["best_entailment"],
            "best_source": similar_result["best_source"],
        }

_scorer = None


def get_scorer() -> AnswerScorer:
    global _scorer
    if _scorer is None:
        _scorer = AnswerScorer()
    return _scorer