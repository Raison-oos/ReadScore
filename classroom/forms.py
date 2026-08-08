import re

from django import forms
from django.forms import inlineformset_factory
from .models import Classroom, Test, Question

TIMER_PATTERN = re.compile(r"^(\d{1,2}):([0-5]\d):([0-5]\d)$")


class ClassForm(forms.ModelForm):
    name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "glass-input",
            "placeholder": "e.g. Grade 6 - Section A",
            "autocomplete": "off",
        }),
        error_messages={"required": "Class name cannot be empty."},
    )

    class Meta:
        model = Classroom
        fields = ["name"]


class TestForm(forms.ModelForm):
    passage = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "passage-text",
            "id": "passageText",
            "rows": 14,
            "placeholder": "Paste or write the reading passage here.",
        }),
        required=True,
        error_messages={"required": "Passage cannot be empty."},
    )
    # hh:mm:ss entered next to the "Passage timer" toggle; converted to
    # Test.passage_timer_seconds in clean().
    passage_timer_value = forms.CharField(required=False)

    class Meta:
        model = Test
        fields = ["passage", "separate_page", "shown_in_test", "passage_timer"]

    def clean(self):
        cleaned = super().clean()
        timer_enabled = cleaned.get("passage_timer")
        separate_page = cleaned.get("separate_page")

        if timer_enabled and not separate_page:
            self.add_error("passage_timer", "Passage timer requires \"Separate page\" to be enabled.")

        if timer_enabled:
            value = cleaned.get("passage_timer_value", "").strip()
            match = TIMER_PATTERN.match(value)
            if not match:
                self.add_error("passage_timer_value", "Enter the timer as hh:mm:ss.")
            else:
                hours, minutes, seconds = (int(part) for part in match.groups())
                total_seconds = hours * 3600 + minutes * 60 + seconds
                if total_seconds <= 0:
                    self.add_error("passage_timer_value", "Timer must be greater than zero.")
                else:
                    cleaned["passage_timer_seconds"] = total_seconds
        else:
            cleaned["passage_timer_seconds"] = None

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.passage_timer_seconds = self.cleaned_data.get("passage_timer_seconds")
        if commit:
            instance.save()
        return instance


class QuestionForm(forms.ModelForm):
    question = forms.CharField(
        widget=forms.TextInput(attrs={"class": "qa-input", "placeholder": "Suggested Question?"}),
        required=True,
        error_messages={"required": "Question is required."},
    )
    answer_key = forms.CharField(
        widget=forms.Textarea(attrs={"class": "qa-input", "placeholder": "Answer Key"}),
        required=True,
        error_messages={"required": "Answer key is required."},
    )

    class Meta:
        model = Question
        fields = ["question", "answer_key"]


QuestionFormSet = inlineformset_factory(
    Test,
    Question,
    form=QuestionForm,
    fields=["question", "answer_key"],
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)

class ClassCodeForm(forms.Form):
    class_code = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'id': 'classCodeInput',
            'class': 'glass-input',     # Crucial for student_classroom.js to query it
            'placeholder': 'Enter Class Code',
            'autocomplete': 'off',
            'maxlength': '20'
        }),
        error_messages={"required": "Please enter a class code."},
    )

    def clean_class_code(self):
        code = self.cleaned_data["class_code"].strip().upper()
        if not Classroom.objects.filter(class_code=code).exists():
            raise forms.ValidationError("No class found with that code.")
        return code