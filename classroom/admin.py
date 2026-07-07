from django.contrib import admin
from .models import Test, Question, StudentAnswer


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
    list_display = ("test", "order", "question","answer_key", "blooms_level")
    list_filter = ("blooms_level",)
    readonly_fields = ("blooms_level",)

@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "student", "question", "test", "answer_text", "is_correct",
        "is_grounded", "is_relevant", "is_similar", "submitted_at",
    )
    list_filter = ("is_correct", "is_grounded", "is_relevant", "is_similar", "test")