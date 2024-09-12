from django.urls import path
from .views import (
    CreateQuestionView,
    QuestionDetailView,
    AnswerQuestionView,
    CommentOnAnswerView,
    AcceptAnswerView,
    UpvoteAnswerView,
    DownvoteAnswerView
)

urlpatterns = [
    path('question-create/', CreateQuestionView.as_view(), name='create-question'),
    path('questions/<int:pk>/', QuestionDetailView.as_view(), name='view-question'),
    path('questions/<int:pk>/answers/', AnswerQuestionView.as_view(), name='answer-question'),
    path('answers/<int:pk>/comment/', CommentOnAnswerView.as_view(), name='comment-on-answer'),
    path('answers/<int:pk>/accept/', AcceptAnswerView.as_view(), name='accept-answer'),
    path('answers/<int:pk>/upvote/', UpvoteAnswerView.as_view(), name='upvote-answer'),
    path('answers/<int:pk>/downvote/', DownvoteAnswerView.as_view(), name='downvote-answer'),
]
