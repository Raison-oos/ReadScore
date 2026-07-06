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

    Each of the three checks below (grounded / relevant / similar) is
    independent: call whichever ones you need, or all three. Nothing
    here combines them into a single correctness verdict — that's left
    up to the caller.
    """

    def __init__(self):
        # ---- NLI: is the answer grounded in the passage? ----
        self.nli_name = "MoritzLaurer/deberta-v3-base-mnli-fever-anli"
        self.nli_tokenizer = AutoTokenizer.from_pretrained(self.nli_name)
        self.nli_model = AutoModelForSequenceClassification.from_pretrained(self.nli_name)
        self.nli_model.eval()

        # ---- QNLI: does the answer address the question? ----
        self.qnli_name = "cross-encoder/qnli-distilroberta-base"
        self.qnli_model = CrossEncoder(self.qnli_name)

        # ---- QA: is the answer similar to what a QA model extracts? ----
        self.qa_pipeline = pipeline(
            "question-answering",
            model="deepset/deberta-v3-large-squad2",
        )

    # -------------------------------------------------------------
    # Low-level model calls
    # -------------------------------------------------------------

    def nli_score(self, context: str, hypothesis: str) -> torch.Tensor:
        """
        Softmax probs for this deberta checkpoint's label order:
        index 0 = entailment, 1 = neutral, 2 = contradiction.
        """
        inputs = self.nli_tokenizer(
            context, hypothesis, return_tensors="pt", truncation=True
        )
        with torch.no_grad():
            logits = self.nli_model(**inputs).logits
            probs = F.softmax(logits, dim=-1)[0]
        return probs

    def qnli_score(self, question: str, answer: str) -> float:
        score = self.qnli_model.predict([(question, answer)])[0]
        return torch.sigmoid(torch.tensor(score)).item()

    def qa_score(self, context: str, question: str, answer: str):
        """
        Extracts the QA model's own answer from the passage, then checks
        bidirectional entailment between that extracted answer and the
        student's answer (paraphrase-style equivalence, not exact match).
        """
        qa_result = self.qa_pipeline(question=question, context=context)
        expected_answer = qa_result["answer"]

        forward = self.nli_score(expected_answer, answer)
        backward = self.nli_score(answer, expected_answer)

        return max(forward[0], backward[0]), expected_answer

    # -------------------------------------------------------------
    # Independent evaluations — call any subset you need
    # -------------------------------------------------------------

    def evaluate_grounded(self, story: str, answer: str) -> dict:
        """Is the answer grounded in / supported by the passage?"""
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
        """Does the answer actually address the question?"""
        qnli_relevance = self.qnli_score(question, answer)

        is_relevant = qnli_relevance > 0.6

        return {
            "is_relevant": int(is_relevant),
            "question_relevance": qnli_relevance,
        }

    def evaluate_similar(self, story: str, question: str, answer: str) -> dict:
        """Is the answer similar to what a QA model extracts as correct?"""
        answer_entailment, expected_answer = self.qa_score(story, question, answer)
        answer_entailment = answer_entailment.item()

        is_similar = answer_entailment > 0.6

        return {
            "is_similar": int(is_similar),
            "answer_entailment": answer_entailment,
            "expected_answer": expected_answer,
        }


_scorer = None


def get_scorer() -> AnswerScorer:
    global _scorer
    if _scorer is None:
        _scorer = AnswerScorer()
    return _scorer