from rest_framework import serializers
from ..models import Flag, Question, Answer, Comment


class FlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flag
        fields = ['id', 'user', 'question', 'answer', 'comment', 'reason', 'description']

    def validate(self, data):
        if not data.get('question') and not data.get('answer') and not data.get('comment'):
            raise serializers.ValidationError("At least one content field (question, answer, or comment) must be flagged.")
        return data


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'user', 'title', 'body', 'tags', 'views_count', 'upvotes', 'downvotes']

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'question', 'user', 'body', 'is_accepted', 'upvotes', 'downvotes']

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'user', 'content', 'question', 'answer']