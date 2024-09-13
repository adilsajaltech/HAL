from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class TimeStampModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        

class Question(TimeStampModel):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')
    title = models.CharField(max_length=255)
    body = models.TextField()
    tags = models.ManyToManyField('Tag', related_name='questions')
    views_count = models.IntegerField(default=0)
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

class Answer(TimeStampModel):
    id = models.BigAutoField(primary_key=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    body = models.TextField()
    is_accepted = models.BooleanField(default=False)
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'Answer to {self.question.title}'

class Comment(TimeStampModel):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'Comment by {self.user.email}'

class Tag(TimeStampModel):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
    


class Flag(TimeStampModel):
    FLAG_TYPES = [
        ('SPAM', 'Spam'),
        ('INAPPROPRIATE', 'Inappropriate'),
        ('OFF_TOPIC', 'Off-Topic'),
        ('OTHER', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flags')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True, related_name='flags')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True, related_name='flags')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='flags')
    reason = models.CharField(choices=FLAG_TYPES, max_length=20)
    description = models.TextField(null=True, blank=True)  # Additional information about the flag
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f'Flag by {self.user.email} on {self.reason}'
    
class Vote(models.Model):
    VOTE_TYPE_CHOICES = [
        ('UPVOTE', 'Upvote'),
        ('DOWNVOTE', 'Downvote'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True, related_name='votes')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True, related_name='votes')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='votes')
    vote_type = models.CharField(max_length=10, choices=VOTE_TYPE_CHOICES)

    class Meta:
        unique_together = ('user', 'question', 'answer', 'comment', 'vote_type')