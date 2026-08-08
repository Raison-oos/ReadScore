from django.contrib import admin

from .models import BLOOM_WEIGHTS, Question, StudentAnswer, Test, TestResult


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ("order", "question", "answer_key", "blooms_level")
    readonly_fields = ("blooms_level",)


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("test_code", "created_by", "created_at", "question_count")
    readonly_fields = ("test_code", "created_at")
    inlines = [QuestionInline]

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = "Questions"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("test", "order", "question", "answer_key", "blooms_level")
    list_filter = ("blooms_level",)
    readonly_fields = ("blooms_level",)


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "question",
        "test",
        "answer_text",
        "bert_score",
        "bloom_weight",
        "normalized_weight",
        "weighted_score",
        "submitted_at",
    )

    list_filter = ("test",)

    def bloom_weight(self, obj):
        return BLOOM_WEIGHTS.get(obj.question.blooms_level, 1)

    bloom_weight.short_description = "Bloom Weight"

    def normalized_weight(self, obj):
        total = sum(
            BLOOM_WEIGHTS.get(q.blooms_level, 1)
            for q in obj.test.questions.all()
        )

        if total == 0:
            return 0

        weight = BLOOM_WEIGHTS.get(obj.question.blooms_level, 1)
        return round(weight / total, 4)

    normalized_weight.short_description = "Normalized Weight"

    def weighted_score(self, obj):
        total = sum(
            BLOOM_WEIGHTS.get(q.blooms_level, 1)
            for q in obj.test.questions.all()
        )

        if total == 0:
            return 0

        weight = BLOOM_WEIGHTS.get(obj.question.blooms_level, 1)

        return round(
            obj.bert_score *
            (weight / total),
            4,
        )

    weighted_score.short_description = "Contribution"


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "test",
        "question_count",
        "total_bloom_weight",
        "raw_weighted_score",
        "final_score",
        "phil_iri_level",
        "computed_at",
    )

    list_filter = (
        "phil_iri_level",
        "test",
    )

    def question_count(self, obj):
        return obj.test.questions.count()

    question_count.short_description = "Questions"

    def total_bloom_weight(self, obj):
        return sum(
            BLOOM_WEIGHTS.get(q.blooms_level, 1)
            for q in obj.test.questions.all()
        )

    total_bloom_weight.short_description = "Σ Bloom Weight"

    def raw_weighted_score(self, obj):
        answers = StudentAnswer.objects.filter(
            student=obj.student,
            test=obj.test
        ).select_related("question")

        total_weight = sum(
            BLOOM_WEIGHTS.get(a.question.blooms_level, 1)
            for a in answers
        )

        if total_weight == 0:
            return 0

        score = 0

        for answer in answers:
            weight = BLOOM_WEIGHTS.get(answer.question.blooms_level, 1)
            score += (
                answer.bert_score *
                (weight / total_weight)
            )

        return round(score, 4)

    raw_weighted_score.short_description = "Σ Weighted Score"