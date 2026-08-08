from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClassCodeForm, ClassForm, QuestionFormSet, TestForm
from .ml.answer_scorer import get_scorer
from .ml.classifier import classify_blooms
from .models import (
    BLOOM_WEIGHTS,
    Classroom,
    Enrollment,
    StudentAnswer,
    Test,
    TestResult,
    generate_test_code,
)


@login_required
def classroom_view(request):
    if getattr(request.user, "role", None) == "TEACHER":
        if request.method == "POST":
            form = ClassForm(request.POST)
            if form.is_valid():
                new_class = form.save(commit=False)
                new_class.created_by = request.user
                new_class.save()
                messages.success(request, f"Class created. Code: {new_class.class_code}")
                return redirect("classroom:class_detail", class_code=new_class.class_code)
        else:
            form = ClassForm()

        classes = Classroom.objects.filter(created_by=request.user)
        return render(request, "classroom/teacher_classroom.html", {"classes": classes, "form": form})

    if request.method == "POST":
        form = ClassCodeForm(request.POST)
        if form.is_valid():
            class_room = Classroom.objects.get(class_code=form.cleaned_data["class_code"])
            Enrollment.objects.get_or_create(student=request.user, classroom=class_room)
            return redirect("classroom:class_detail", class_code=class_room.class_code)
    else:
        form = ClassCodeForm()

    classes = Classroom.objects.filter(enrollments__student=request.user).distinct()
    return render(request, "classroom/student_classroom.html", {"form": form, "classes": classes})


@login_required
def class_detail(request, class_code):
    class_room = get_object_or_404(Classroom, class_code=class_code)

    if getattr(request.user, "role", None) == "TEACHER":
        if class_room.created_by_id != request.user.id:
            messages.error(request, "You don't have access to that class.")
            return redirect("classroom:classroom")

        tests = class_room.tests.order_by("-created_at")

        roster = []
        for enrollment in class_room.enrollments.select_related("student").order_by("student__username"):
            student_results = TestResult.objects.filter(student=enrollment.student, test__classroom=class_room)
            average = student_results.aggregate(avg=Avg("final_score"))["avg"]
            roster.append({
                "student": enrollment.student,
                "completed": student_results.count(),
                "average_score": round(average, 1) if average is not None else None,
            })

        return render(request, "classroom/class_detail_teacher.html", {
            "classroom": class_room,
            "tests": tests,
            "roster": roster,
        })

    if not Enrollment.objects.filter(student=request.user, classroom=class_room).exists():
        messages.error(request, "You're not enrolled in that class.")
        return redirect("classroom:classroom")

    results_by_test = {
        result.test_id: result
        for result in TestResult.objects.filter(student=request.user, test__classroom=class_room)
    }

    tests = []
    for test in class_room.tests.order_by("-created_at"):
        result = results_by_test.get(test.test_code)
        total_questions = test.questions.count()

        if result:
            status = "finished"
        elif total_questions == 0:
            status = "missing"
        elif StudentAnswer.objects.filter(student=request.user, test=test).exists():
            status = "unfinished"
        else:
            status = "not_started"

        tests.append({"test": test, "result": result, "status": status})

    return render(request, "classroom/class_detail_student.html", {
        "classroom": class_room,
        "tests": tests,
    })


@login_required
def delete_class(request, class_code):
    class_room = get_object_or_404(Classroom, class_code=class_code, created_by=request.user)
    if request.method == "POST":
        name = class_room.name
        class_room.delete()
        messages.success(request, f'Class "{name}" deleted.')
    return redirect("classroom:classroom")


@login_required
def unenroll_class(request, class_code):
    class_room = get_object_or_404(Classroom, class_code=class_code)
    enrollment = get_object_or_404(Enrollment, student=request.user, classroom=class_room)
    if request.method == "POST":
        enrollment.delete()
        messages.success(request, f'You left "{class_room.name}".')
    return redirect("classroom:classroom")


@login_required
def dashboard_view(request, class_code):
    class_room = get_object_or_404(Classroom, class_code=class_code, created_by=request.user)

    if request.method == "POST":
        test_form = TestForm(request.POST)
        formset = QuestionFormSet(request.POST, instance=Test(), prefix="questions")

        if test_form.is_valid() and formset.is_valid():
            with transaction.atomic():
                test = test_form.save(commit=False)
                test.test_code = generate_test_code()
                test.classroom = class_room
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
            return redirect("classroom:class_detail", class_code=class_room.class_code)
        else:
            messages.error(request, "Please fix the errors below.")

    else:
        test_form = TestForm()
        formset = QuestionFormSet(instance=Test(), prefix="questions")

    context = {
        "classroom": class_room,
        "test_form": test_form,
        "formset": formset,
        "pending_test_code": request.POST.get("test_code") if request.method == "POST" else generate_test_code(),
    }
    return render(request, "classroom/teacher_dashboard.html", context)


@login_required
def delete_test(request, test_code):
    test = get_object_or_404(Test, test_code=test_code, created_by=request.user)
    class_code = test.classroom_id
    if request.method == "POST":
        test.delete()
        messages.success(request, f"Test {test_code} deleted.")
    if class_code:
        return redirect("classroom:class_detail", class_code=class_code)
    return redirect("classroom:classroom")


@login_required
def passage_intro(request, test_code):
    test = get_object_or_404(Test, test_code=test_code)
    if not test.separate_page:
        return redirect("classroom:take_test", test_code=test.test_code)

    session_key = f"passage_seen_{test.test_code}"

    if request.method == "POST":
        request.session[session_key] = True
        return redirect("classroom:take_test", test_code=test.test_code)

    return render(request, "classroom/passage_intro.html", {"test": test})


@login_required
def take_test(request, test_code):
    test = get_object_or_404(Test, test_code=test_code)
    questions = test.questions.all()

    if test.separate_page and not request.session.get(f"passage_seen_{test.test_code}") and request.method != "POST":
        return redirect("classroom:passage_intro", test_code=test.test_code)

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
                bloom_weights.append(BLOOM_WEIGHTS[question.blooms_level])

                StudentAnswer.objects.update_or_create(
                    student=request.user,
                    question=question,
                    defaults={
                        "test": test,
                        "answer_text": answer_text,
                        "bert_score": result["bert_score"],
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


# A semantic match at or above this threshold is shown as "Correct" on the
# result page. It's a display-only cutoff — the actual score is the
# continuous BERTScore, not this pass/fail line.
CORRECT_THRESHOLD = 0.6


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

    total_weight = sum(BLOOM_WEIGHTS.get(a.question.blooms_level, 1) for a in answers) or 1

    breakdown = []
    for answer in answers:
        bloom_weight = BLOOM_WEIGHTS.get(answer.question.blooms_level, 1)
        normalized_weight = bloom_weight / total_weight
        match = answer.bert_score or 0
        breakdown.append({
            "answer": answer,
            "bloom_weight": bloom_weight,
            "weight_share": round(normalized_weight * 100, 1),
            "match_percent": round(match * 100, 1),
            "contribution": round(match * normalized_weight * 100, 1),
            "is_correct": match >= CORRECT_THRESHOLD,
        })

    return render(request, "classroom/student_result.html", {
        "test": test,
        "breakdown": breakdown,
        "final_score": result.final_score if result else 0,
        "phil_iri_level": result.get_phil_iri_level_display() if result else "—",
        "CORRECT_THRESHOLD_PERCENT": round(CORRECT_THRESHOLD * 100),
    })