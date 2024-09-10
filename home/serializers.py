from rest_framework import serializers
from .models import Question, Answer, Comment
from .validators import validate_no_contact_info

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['title', 'body', 'tags']

    def validate_body(self, value):
        user = self.context['request'].user  # Get the user from the request context
        validate_no_contact_info(value, user)  # Pass the user to the validator
        return value


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['body']

    def validate_body(self, value):
        user = self.context['request'].user
        validate_no_contact_info(value, user)
        return value


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content']

    def validate_content(self, value):
        user = self.context['request'].user
        validate_no_contact_info(value, user)
        return value
