from rest_framework import serializers
from models import Flag


class FlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flag
        fields = ['id', 'user', 'question', 'answer', 'comment', 'reason', 'description']

    def validate(self, data):
        if not data.get('question') and not data.get('answer') and not data.get('comment'):
            raise serializers.ValidationError("At least one content field (question, answer, or comment) must be flagged.")
        return data
