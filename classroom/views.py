import csv
import io
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import escape

from accounts.models import User

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
def remove_student(request, class_code, student_id):
    class_room = get_object_or_404(Classroom, class_code=class_code, created_by=request.user)
    enrollment = get_object_or_404(Enrollment, student_id=student_id, classroom=class_room)
    if request.method == "POST":
        student_name = enrollment.student.get_full_name() or enrollment.student.username
        enrollment.delete()
        messages.success(request, f'Removed {student_name} from "{class_room.name}".')
    return redirect("classroom:class_detail", class_code=class_room.class_code)


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

            messages.success(request, f'Test "{test.title}" saved.')
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
    }
    return render(request, "classroom/teacher_dashboard.html", context)


@login_required
def delete_test(request, test_code):
    test = get_object_or_404(Test, test_code=test_code, created_by=request.user)
    class_code = test.classroom_id
    if request.method == "POST":
        title = test.title
        test.delete()
        messages.success(request, f'Test "{title}" deleted.')
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


def _score_breakdown(answers):
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
    return breakdown


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
        "breakdown": _score_breakdown(answers),
        "final_score": result.final_score if result else 0,
        "phil_iri_level": result.get_phil_iri_level_display() if result else "—",
        "CORRECT_THRESHOLD_PERCENT": round(CORRECT_THRESHOLD * 100),
    })


@login_required
def teacher_test_results(request, test_code):
    test = get_object_or_404(Test, test_code=test_code, created_by=request.user)

    answers_by_student = {}
    for answer in (
        StudentAnswer.objects
        .filter(test=test)
        .select_related("question", "student")
        .order_by("question__order")
    ):
        answers_by_student.setdefault(answer.student_id, []).append(answer)

    results_by_student = {r.student_id: r for r in TestResult.objects.filter(test=test)}

    roster = []
    if test.classroom:
        enrollments = test.classroom.enrollments.select_related("student").order_by("student__username")
        for enrollment in enrollments:
            student = enrollment.student
            student_answers = answers_by_student.get(student.id, [])
            result = results_by_student.get(student.id)

            if result:
                status = "finished"
            elif student_answers:
                status = "unfinished"
            else:
                status = "not_started"

            roster.append({
                "student": student,
                "breakdown": _score_breakdown(student_answers),
                "result": result,
                "status": status,
                "answered_count": len(student_answers),
            })

    return render(request, "classroom/teacher_test_results.html", {
        "test": test,
        "classroom": test.classroom,
        "roster": roster,
        "total_questions": test.questions.count(),
        "CORRECT_THRESHOLD_PERCENT": round(CORRECT_THRESHOLD * 100),
    })


def _export_filename(test, extension):
    base = f"{test.title or 'test'}_{test.test_code}"
    base = re.sub(r"[^A-Za-z0-9_-]+", "_", base).strip("_")
    return f"{base}.{extension}"


def _export_txt(test, students_data):
    lines = [f"TEST: {test.title or 'Untitled Test'}"]
    if test.classroom:
        lines.append(f"CLASS: {test.classroom.name}")
    lines += ["", "PASSAGE:", test.passage, ""]

    for data in students_data:
        student = data["student"]
        result = data["result"]
        lines.append("=" * 40)
        lines.append(f"STUDENT: {student.get_full_name() or student.username} ({student.email})")
        if result:
            lines.append(f"STATUS: Finished | SCORE: {result.final_score}% | LEVEL: {result.get_phil_iri_level_display()}")
        else:
            lines.append("STATUS: Not finished")
        lines.append("")

        if data["breakdown"]:
            for i, item in enumerate(data["breakdown"], start=1):
                question = item["answer"].question
                lines.append(f"Q{i} ({question.get_blooms_level_display()}): {question.question}")
                lines.append(f"Answer: {item['answer'].answer_text}")
                lines.append(f"Match: {item['match_percent']}%")
                lines.append("")
        else:
            lines.append("No answers submitted.")
            lines.append("")

    response = HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{_export_filename(test, "txt")}"'
    return response


def _export_csv(test, students_data):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Student", "Email", "Status", "Final Score", "Phil-IRI Level",
        "Question", "Bloom's Level", "Answer", "Match %",
    ])

    for data in students_data:
        student = data["student"]
        result = data["result"]
        status = "Finished" if result else "Not finished"
        score = result.final_score if result else ""
        level = result.get_phil_iri_level_display() if result else ""

        if data["breakdown"]:
            for item in data["breakdown"]:
                question = item["answer"].question
                writer.writerow([
                    student.get_full_name() or student.username,
                    student.email,
                    status,
                    score,
                    level,
                    question.question,
                    question.get_blooms_level_display(),
                    item["answer"].answer_text,
                    item["match_percent"],
                ])
        else:
            writer.writerow([
                student.get_full_name() or student.username,
                student.email, status, score, level, "", "", "", "",
            ])

    response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{_export_filename(test, "csv")}"'
    return response


def _export_pdf(test, students_data):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    small = ParagraphStyle("small", parent=styles["BodyText"], fontSize=9, textColor="#475569")

    def p(text, style=styles["BodyText"]):
        return Paragraph(escape(text).replace("\n", "<br/>"), style)

    story = [p(test.title or "Untitled Test", styles["Heading1"])]
    if test.classroom:
        story.append(p(f"Class: {test.classroom.name}", small))
    story.append(Spacer(1, 12))
    story.append(p("Passage", styles["Heading2"]))
    story.append(p(test.passage))

    for data in students_data:
        student = data["student"]
        result = data["result"]
        story.append(PageBreak())
        story.append(p(student.get_full_name() or student.username, styles["Heading2"]))
        story.append(p(student.email, small))
        if result:
            story.append(p(f"Status: Finished | Score: {result.final_score}% | Level: {result.get_phil_iri_level_display()}", small))
        else:
            story.append(p("Status: Not finished", small))
        story.append(Spacer(1, 10))

        if data["breakdown"]:
            for i, item in enumerate(data["breakdown"], start=1):
                question = item["answer"].question
                story.append(p(f"Q{i} ({question.get_blooms_level_display()}): {question.question}"))
                story.append(p(f"Answer: {item['answer'].answer_text}"))
                story.append(p(f"Match: {item['match_percent']}%", small))
                story.append(Spacer(1, 8))
        else:
            story.append(p("No answers submitted."))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{_export_filename(test, "pdf")}"'
    return response


@login_required
def export_test_results(request, test_code):
    test = get_object_or_404(Test, test_code=test_code, created_by=request.user)
    if request.method != "POST":
        return redirect("classroom:teacher_test_results", test_code=test.test_code)

    enrolled_student_ids = set()
    if test.classroom:
        enrolled_student_ids = set(test.classroom.enrollments.values_list("student_id", flat=True))

    single_student_id = request.POST.get("single_student_id")
    if single_student_id and single_student_id.isdigit():
        selected_ids = {int(single_student_id)}
    elif request.POST.get("scope") == "selected":
        selected_ids = {int(sid) for sid in request.POST.getlist("student_ids") if sid.isdigit()}
    else:
        selected_ids = set(enrolled_student_ids)

    selected_ids &= enrolled_student_ids

    if not selected_ids:
        messages.error(request, "No students selected to export.")
        return redirect("classroom:teacher_test_results", test_code=test.test_code)

    students = User.objects.filter(id__in=selected_ids).order_by("username")

    answers_by_student = {}
    for answer in (
        StudentAnswer.objects
        .filter(test=test, student_id__in=selected_ids)
        .select_related("question", "student")
        .order_by("student__username", "question__order")
    ):
        answers_by_student.setdefault(answer.student_id, []).append(answer)

    results_by_student = {
        r.student_id: r
        for r in TestResult.objects.filter(test=test, student_id__in=selected_ids)
    }

    students_data = [
        {
            "student": student,
            "breakdown": _score_breakdown(answers_by_student.get(student.id, [])),
            "result": results_by_student.get(student.id),
        }
        for student in students
    ]

    export_format = request.POST.get("format", "txt")
    if export_format == "csv":
        return _export_csv(test, students_data)
    if export_format == "pdf":
        return _export_pdf(test, students_data)
    return _export_txt(test, students_data)