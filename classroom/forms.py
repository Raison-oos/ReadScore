from django import forms
from django.forms import inlineformset_factory
from .models import Test, Question


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

    class Meta:
        model = Test
        fields = ["passage"]


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

#Student Answer
class TestCodeForm(forms.Form):
    test_code = forms.CharField(
        max_length=20,
        required=True,
        #widget=forms.TextInput(attrs={"placeholder": "Enter test code"}),
        widget=forms.TextInput(attrs={
            'id': 'classCodeInput',     
            'class': 'glass-input',     # Crucial for student_dashboard.js to query it
            'placeholder': 'Enter Class Code',
            'autocomplete': 'off',
            'maxlength': '20'
        }),
        error_messages={"required": "Please enter a test code."},
    )

    def clean_test_code(self):
        code = self.cleaned_data["test_code"].strip().upper()
        if not Test.objects.filter(test_code=code).exists():
            raise forms.ValidationError("No test found with that code.")
        return code