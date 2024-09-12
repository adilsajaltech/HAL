from django import forms
from models import Question
from captcha.fields import CaptchaField

class QuestionForm(forms.ModelForm):
    captcha = CaptchaField()

    class Meta:
        model = Question
        fields = ['title', 'body', 'tags', 'captcha']
