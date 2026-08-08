import random
import string
from django.db import models
from django.core.exceptions import ValidationError


def generate_test_code():
    while True:
        code = "TC-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Test.objects.filter(test_code=code).exists():
            return code

@property
def status(self):
    """
    missing    = no questions added yet
    unfinished = has questions, but not all have at least one submitted answer
    finished   = every question has at least one submitted student answer
    """
    total_questions = self.questions.count()
    if total_questions == 0:
        return "missing"

    answered_question_ids = set(
        self.student_answers.values_list("question_id", flat=True).distinct()
    )
    if len(answered_question_ids) >= total_questions:
        return "finished"
    return "unfinished"


class BloomsLevel(models.TextChoices):
    REMEMBERING = "REMEMBER", "Remembering"
    UNDERSTANDING = "UNDERSTAND", "Understanding"
    APPLYING = "APPLY", "Applying"
    ANALYZING = "ANALYZE", "Analyzing"
    EVALUATING = "EVALUATE", "Evaluating"
    CREATING = "CREATE", "Creating"


class Test(models.Model):
    test_code = models.CharField(
        max_length=20,
        primary_key=True,
        default=generate_test_code,
        editable=False,
    )
    passage = models.TextField()
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="tests",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Shows the passage on its own page before questions begin.
    separate_page = models.BooleanField(default=False)
    # Keeps the passage visible alongside the questions while students answer.
    shown_in_test = models.BooleanField(default=True)
    # Countdown for how long students can read before questions appear.
    # Only meaningful when separate_page is enabled.
    passage_timer = models.BooleanField(default=False)
    passage_timer_seconds = models.PositiveIntegerField(null=True, blank=True)

    def clean(self):
        if not self.passage or not self.passage.strip():
            raise ValidationError({"passage": "Passage cannot be empty."})
        if self.passage_timer and not self.separate_page:
            raise ValidationError({"passage_timer": "Passage timer requires Separate page to be enabled."})

    def __str__(self):
        return self.test_code


class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="questions")
    order = models.PositiveIntegerField(default=0)
    question = models.TextField()
    answer_key = models.TextField()
    blooms_level = models.CharField(
        max_length=20,
        choices=BloomsLevel.choices,
        editable=False,  # set automatically by the classifier, never by the form
    )

    class Meta:
        ordering = ["order"]

    def clean(self):
        errors = {}
        if not self.question or not self.question.strip():
            errors["question"] = "Question cannot be empty."
        if not self.answer_key or not self.answer_key.strip():
            errors["answer_key"] = "Answer key cannot be empty."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.test.test_code} — Q{self.order}"
    

#Student Answer
class StudentAnswer(models.Model):
    student = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="student_answers")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="student_answers")
    answer_text = models.TextField()

    bert_score = models.FloatField(null=True, blank=True)         # BERTScore_i
    #is_correct = models.BooleanField(null=True, blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "question")

    def clean(self):
        if not self.answer_text or not self.answer_text.strip():
            raise ValidationError({"answer_text": "Answer cannot be empty."})

    def __str__(self):
        return f"{self.student} — {self.question}"


class TestResult(models.Model):
    PHIL_IRI_LEVELS = [
        ("INDEPENDENT", "Independent"),
        ("INSTRUCTIONAL", "Instructional"),
        ("FRUSTRATION", "Frustration"),
    ]

    student = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="test_results")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="results")
    final_score = models.FloatField()  # percentage, 0-100
    phil_iri_level = models.CharField(max_length=20, choices=PHIL_IRI_LEVELS)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "test")

    @staticmethod
    def level_for_score(score: float) -> str:
        if score >= 80:
            return "INDEPENDENT"
        if score >= 59:
            return "INSTRUCTIONAL"
        return "FRUSTRATION"

    def __str__(self):
        return f"{self.student} — {self.test.test_code}: {self.final_score:.1f}%"