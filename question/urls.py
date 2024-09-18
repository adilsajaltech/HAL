from django.urls import path
from .views import (
    CreateQuestionView,
    QuestionDetailView,
    FilterQuestionsView,
    AnswerQuestionView,
    SearchTag,
    TagsDetailView,
    CommentOnAnswerView,
    AcceptAnswerView,
    UpvoteAnswerView,
    DownvoteAnswerView,
    GetQuestionVersionView,
    UpdateQuestionView,
    GetAllQuestionVersionsView,
    FlagContentView,
    GetAllAnswerVersionsView,
    GetAllCommentVersionsView,
    UpdateAnswerView,
    UserQuestionsView,
    UserAnswersView,
    UserCommentsView,
    UpvoteQuestionView,
    DownvoteQuestionView,
    UpvoteCommentView,
    DownvoteCommentView,
    UpdateCommentView,
    DeleteQuestionView,
    DeleteAnswerView,
    DeleteCommentView
)

urlpatterns = [
    path('question-create/', CreateQuestionView.as_view(), name='create-question'), #
    path('questions/', QuestionDetailView.as_view(), name='view-question'), #
    path('filterquestions/', FilterQuestionsView.as_view(), name='filter-question'),
    path('search-tag/', SearchTag.as_view(), name='view-tags'),
    path('TagsDetail/', TagsDetailView.as_view(), name='tags-detail'),
    path('questions/<int:pk>/create-answers/', AnswerQuestionView.as_view(), name='create-answers'), #
    path('answers/<int:pk>/comments/', CommentOnAnswerView.as_view(), name='create-comment-on-answer'), #
    path('answers/<int:pk>/accept/', AcceptAnswerView.as_view(), name='accept-answer'), #
    path('update-questions/<int:pk>/',UpdateQuestionView.as_view(), name="update-questions"), #
    path('update-answers/<int:pk>/',UpdateAnswerView.as_view(), name="update-answers"), #
    path('update-comments/<int:pk>/',UpdateCommentView.as_view(), name="update-comments"), #
    path('get-all-version-questions/<int:pk>/',GetAllQuestionVersionsView.as_view(), name="get-all-version-questions"), #
    path('question-version/<int:pk>/versions/<int:vid>/',GetQuestionVersionView.as_view(), name="Get-question-version"), #
    path('get-all-version-answers/<int:pk>/',GetAllAnswerVersionsView.as_view(), name="GetAllAnswerVersionsView"), #
    path('get-all-version-comments/<int:pk>/',GetAllCommentVersionsView.as_view(), name="GetAllCommentVersionsView"), #
    path('get-all-questions/', UserQuestionsView.as_view(), name='get-all-questions'), #
    path('get-all-answers/', UserAnswersView.as_view(), name='get-all-answers'), #
    path('get-all-comments/', UserCommentsView.as_view(), name='get-all-comments'), #
    path('question-delete/<int:pk>/', DeleteQuestionView.as_view(), name='delete-question'), #
    path('answer-delete/<int:pk>/', DeleteAnswerView.as_view(), name='delete-answer'), #
    path('comment-delete/<int:pk>/', DeleteCommentView.as_view(), name='delete-comment'), #
    path('flag-content/', FlagContentView.as_view(), name='flag-content'),


    path('answers/<int:pk>/upvote/', UpvoteAnswerView.as_view(), name='upvote_answer'),
    path('answers/<int:pk>/downvote/', DownvoteAnswerView.as_view(), name='downvote_answer'),
    path('questions/<int:pk>/upvote/', UpvoteQuestionView.as_view(), name='upvote_question'),
    path('questions/<int:pk>/downvote/', DownvoteQuestionView.as_view(), name='downvote_question'),
    path('comments/<int:pk>/upvote/', UpvoteCommentView.as_view(), name='upvote_comment'),
    path('comments/<int:pk>/downvote/', DownvoteCommentView.as_view(), name='downvote_comment'),



]
