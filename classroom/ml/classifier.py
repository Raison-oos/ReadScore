import json
import torch
from pathlib import Path
from transformers import BertForSequenceClassification, BertTokenizerFast

MODEL_DIR = Path(__file__).resolve().parent / "bloom_taxonomy_model"

# Maps the model's own label strings to the choice codes used in
# models.BloomsLevel. Keep this in sync if you ever rename either side.
LABEL_TO_CHOICE = {
    "Remember": "REMEMBER",
    "Understand": "UNDERSTAND",
    "Apply": "APPLY",
    "Analyze": "ANALYZE",
    "Evaluate": "EVALUATE",
    "Create": "CREATE",
}

class BloomClassifier:
    """
    Loads the fine-tuned BERT model once and reuses it for every prediction.
    Access via the module-level get_classifier() below rather than
    instantiating this directly, so Django doesn't reload the model
    (weights + tokenizer) on every request.
    """

    def __init__(self, model_path=MODEL_DIR):
        self.model_path = str(model_path)
        self.bert_model = BertForSequenceClassification.from_pretrained(self.model_path)
        # Uses tokenizer.json (fast tokenizer format) rather than vocab.txt
        self.bert_tokenizer = BertTokenizerFast.from_pretrained(self.model_path)
        self.bert_model.eval()

        with open(f"{self.model_path}/label_mapping.json", "r") as f:
            self.mapping = json.load(f)
            self.id_to_label = self.mapping["id_to_label"]

    def bloom_score(self, question):
        inputs = self.bert_tokenizer(
            question, return_tensors="pt", truncation=True, padding=True, max_length=128
        )
        with torch.no_grad():
            outputs = self.bert_model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            pred_idx = torch.argmax(probs, dim=1).item()
        return self.id_to_label[str(pred_idx)], probs[0][pred_idx].item()


_classifier = None


def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = BloomClassifier()
    return _classifier


def classify_blooms(question_text: str) -> str:
    """
    Returns one of: REMEMBER, UNDERSTAND, APPLY, ANALYZE, EVALUATE, CREATE
    (matches models.BloomsLevel choice codes).
    """
    label, _confidence = get_classifier().bloom_score(question_text)
    return LABEL_TO_CHOICE.get(label, "REMEMBER")