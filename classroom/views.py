from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Test, generate_test_code, Question, StudentAnswer
from .forms import TestForm, QuestionFormSet, TestCodeForm
from .ml.classifier import classify_blooms
from django.shortcuts import get_object_or_404
from django.db import transaction


@login_required
def classroom_view(request):
    if getattr(request.user, "role", None) == "TEACHER":
        return render(request, 'classroom/teacher_classroom.html')

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
            return redirect("classroom:dashboard")
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
            for question in questions:
                answer_text = previous_answers[question.id]
                is_correct = (
                    answer_text.lower() == question.answer_key.strip().lower()
                )
                StudentAnswer.objects.update_or_create(
                    student=request.user,
                    question=question,
                    defaults={
                        "test": test,
                        "answer_text": answer_text,
                        "is_correct": is_correct,
                    },
                )

        messages.success(request, "Your answers have been submitted.")
        return redirect("classroom:classroom")#redirect to exam result

    return render(request, "classroom/student_dashboard.html", {
        "test": test,
        "questions": questions,
    })