from django.urls import path
from .views import (
    CreateQuestionView,
    QuestionDetailView,
    AnswerQuestionView,
    CommentOnAnswerView,
    AcceptAnswerView,
    UpvoteAnswerView,
    DownvoteAnswerView,
    SearchTag,
    TagsDetailView,
    FilterQuestionsView
)

urlpatterns = [
    path('question-create/', CreateQuestionView.as_view(), name='create-question'),
    path('questions/', QuestionDetailView.as_view(), name='view-question'),
    path('filterquestions/', FilterQuestionsView.as_view(), name='filter-question'),
    path('search-tag/', SearchTag.as_view(), name='view-tags'),
    path('TagsDetail/', TagsDetailView.as_view(), name='tags-detail'),
    path('questions/<int:pk>/answers/', AnswerQuestionView.as_view(), name='answer-question'),
    path('answers/<int:pk>/comment/', CommentOnAnswerView.as_view(), name='comment-on-answer'),
    path('answers/<int:pk>/accept/', AcceptAnswerView.as_view(), name='accept-answer'),
    path('answers/<int:pk>/upvote/', UpvoteAnswerView.as_view(), name='upvote-answer'),
    path('answers/<int:pk>/downvote/', DownvoteAnswerView.as_view(), name='downvote-answer'),
]
