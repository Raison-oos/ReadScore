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

    def clean(self):
        if not self.passage or not self.passage.strip():
            raise ValidationError({"passage": "Passage cannot be empty."})

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
    student = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="student_answers")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="student_answers")
    answer_text = models.TextField()

    is_correct = models.BooleanField(null=True, blank=True)

    # Debug/breakdown fields — not used for grading logic itself, just
    # to see which stage of determine_correctness passed or failed.
    # null = check never ran (short-circuited by an earlier failed stage).
    is_grounded = models.BooleanField(null=True, blank=True)
    is_relevant = models.BooleanField(null=True, blank=True)
    is_similar = models.BooleanField(null=True, blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "question")

    def clean(self):
        if not self.answer_text or not self.answer_text.strip():
            raise ValidationError({"answer_text": "Answer cannot be empty."})

    def __str__(self):
        return f"{self.student} — {self.question}"