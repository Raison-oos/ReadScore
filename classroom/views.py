from .ml.classifier import classify_blooms
from .ml.answer_scorer import get_scorer
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Test, Question, StudentAnswer, TestResult, generate_test_code, BloomsLevel
from .forms import TestForm, QuestionFormSet, TestCodeForm
from django.shortcuts import get_object_or_404
from django.db import transaction


@login_required
def classroom_view(request):
    if getattr(request.user, "role", None) == "TEACHER":
        tests = Test.objects.filter(created_by=request.user).order_by("-created_at")
        return render(request, "classroom/teacher_classroom.html", {"tests": tests})

    if request.method == "POST":
        form = TestCodeForm(request.POST)
        if form.is_valid():
            return redirect("classroom:take_test", test_code=form.cleaned_data["test_code"])
    else:
        form = TestCodeForm()
    return render(request, "classroom/student_classroom.html", {"form": form})

@login_required
def dashboard_view(request):
    if getattr(request.user, "role", None) != "TEACHER":
        return render(request, "classroom/student_dashboard.html")

    if request.method == "POST":
        test_form = TestForm(request.POST)
        formset = QuestionFormSet(request.POST, instance=Test(), prefix="questions")

        if test_form.is_valid() and formset.is_valid():
            with transaction.atomic():
                test = test_form.save(commit=False)
                test.test_code = generate_test_code()
                test.created_by = request.user
                test.save()

                order = 1
                for question in formset.save(commit=False):
                    question.test = test
                    question.blooms_level = classify_blooms(question.question)
                    question.order = order
                    question.save()
                    order += 1

                for obj in formset.deleted_objects:
                    obj.delete()

            messages.success(request, f"Test saved. Code: {test.test_code}")
            return redirect("classroom:classroom")
        else:
            messages.error(request, "Please fix the errors below.")

    else:
        test_form = TestForm()
        formset = QuestionFormSet(instance=Test(), prefix="questions")

    context = {
        "test_form": test_form,
        "formset": formset,
        "pending_test_code": request.POST.get("test_code") if request.method == "POST" else generate_test_code(),
    }
    return render(request, "classroom/teacher_dashboard.html", context)

#delete button
@login_required
def delete_test(request, test_code):
    test = get_object_or_404(Test, test_code=test_code, created_by=request.user)
    if request.method == "POST":
        test.delete()
        messages.success(request, f"Test {test_code} deleted.")
    return redirect("classroom:classroom")


#student answer
@login_required
def take_test(request, test_code):
    test = get_object_or_404(Test, test_code=test_code)
    questions = test.questions.all()

    if request.method == "POST":
        errors = {}
        previous_answers = {}

        for question in questions:
            answer_text = request.POST.get(f"answer_{question.id}", "").strip()
            previous_answers[question.id] = answer_text

            if not answer_text:
                errors[question.id] = "Please answer this question."

        if errors:
            return render(request, "classroom/student_dashboard.html", {
                "test": test,
                "questions": questions,
                "errors": errors,
                "previous_answers": previous_answers,
            })

        with transaction.atomic():
            scorer = get_scorer()

            BLOOM_WEIGHTS = {
            BloomsLevel.REMEMBERING: 1,
            BloomsLevel.UNDERSTANDING: 2,
            BloomsLevel.APPLYING: 3,
            BloomsLevel.ANALYZING: 4,
            BloomsLevel.EVALUATING: 5,
            BloomsLevel.CREATING: 6,
            }

            question_scores = []
            bloom_weights = []

            for question in questions:
                answer_text = previous_answers[question.id]

                result = scorer.score_question(
                    test.passage,
                    question.question,
                    answer_text,
                    question.answer_key,
                )

                question_scores.append(result)

                # CHANGE THIS LINE TO MATCH YOUR MODEL
                bloom_weights.append(BLOOM_WEIGHTS[question.blooms_level])

                StudentAnswer.objects.update_or_create(
                    student=request.user,
                    question=question,
                    defaults={
                        "test": test,
                        "answer_text": answer_text,
                        "gate_score": result["gate_score"],
                        "bert_score": result["bert_score"],
                        "is_correct": result["is_correct"],
                        "is_grounded": result["is_grounded"],
                        "is_relevant": result["is_relevant"],
                    },
                )

            final_score = scorer.aggregate_final_score(
                question_scores,
                bloom_weights,
            )

            final_percentage = round(final_score * 100, 2)

            level = TestResult.level_for_score(final_percentage)

            TestResult.objects.update_or_create(
                student=request.user,
                test=test,
                defaults={
                    "final_score": final_percentage,
                    "phil_iri_level": level,
                },
            )

        messages.success(request, "Your answers have been submitted.")
        return redirect("classroom:student_result", test_code=test.test_code)

    return render(request, "classroom/student_dashboard.html", {
        "test": test,
        "questions": questions,
    })

@login_required
def student_result(request, test_code):
    test = get_object_or_404(Test, test_code=test_code)
    answers = (
        StudentAnswer.objects
        .filter(student=request.user, test=test)
        .select_related("question")
        .order_by("question__order")
    )
    result = TestResult.objects.filter(student=request.user, test=test).first()

    return render(request, "classroom/student_result.html", {
        "test": test,
        "answers": answers,
        "final_score": result.final_score if result else 0,
        "phil_iri_level": result.get_phil_iri_level_display() if result else "—",
    })