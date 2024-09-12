from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Question, Answer, Comment, Tag
import json
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework import status

@method_decorator(csrf_exempt, name='dispatch')
class CreateQuestionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User must be logged in to create a question'}, status=403)
        data = json.loads(request.body)
        title = data.get('title')
        body = data.get('body')
        tags = data.get('tags', [])

        if not title or not body:
            return JsonResponse({'error': 'Title and body are required'}, status=400)

        question = Question.objects.create(user=request.user, title=title, body=body)
        tag_objects = []
        for tag in tags : 
            Tag_obj, _ = Tag.objects.get_or_create(name=tag)
            tag_objects.append(Tag_obj)
            
        question.tags.set(tag_objects)
        question.save()

        return JsonResponse({'message': 'Question created successfully', 'question_id': question.id}, status=201)

@method_decorator(csrf_exempt, name='dispatch')
class QuestionDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk, *args, **kwargs):
        question = get_object_or_404(Question, pk=pk)
        question.views_count += 1
        question.save()

        response_data = {
            'id': question.id,
            'title': question.title,
            'body': question.body,
            'tags': [tag.name for tag in question.tags.all()],
            'user': question.user.username,
            'views_count': question.views_count,
            'upvotes': question.upvotes,
            'downvotes': question.downvotes,
            'answers': [
                {
                    'id': answer.id,
                    'body': answer.body,
                    'user': answer.user.username,
                    'is_accepted': answer.is_accepted,
                    'upvotes': answer.upvotes,
                    'downvotes': answer.downvotes,
                }
                for answer in question.answers.all()
            ],
        }

        return JsonResponse(response_data, status=200)

@method_decorator(csrf_exempt, name="dispatch")
class AnswerQuestionView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User must be logged in to create a question'}, status=status.HTTP_401_UNAUTHORIZED)
        
        question = get_object_or_404(Question, pk=pk)
        data = json.loads(request.body)
        body = data.get('body')

        if not body:
            return JsonResponse({'error': 'Answer body is required'}, status=400)

        answer = Answer.objects.create(user=request.user, question=question, body=body)
        return JsonResponse({'message': 'Answer created successfully', 'answer_id': answer.id}, status=201)

@method_decorator(csrf_exempt, name="dispatch")
class CommentOnAnswerView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk, *args, **kwargs):
        answer = get_object_or_404(Answer, pk=pk)
        data = json.loads(request.body)
        content = data.get('content')

        if not content:
            return JsonResponse({'error': 'Comment content is required'}, status=400)

        comment = Comment.objects.create(user=request.user, answer=answer, content=content)
        return JsonResponse({'message': 'Comment created successfully', 'comment_id': comment.id}, status=201)

@method_decorator(csrf_exempt, name="dispatch")
class AcceptAnswerView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk, *args, **kwargs):
        answer = get_object_or_404(Answer, pk=pk)
        question = answer.question

        if request.user != question.user:
            return JsonResponse({'error': 'Only the question author can accept an answer'}, status=403)

        question.answers.update(is_accepted=False)
        answer.is_accepted = True
        answer.save()

        return JsonResponse({'message': 'Answer accepted successfully'}, status=200)

@method_decorator(csrf_exempt, name="dispatch")
class UpvoteAnswerView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk, *args, **kwargs):
        answer = get_object_or_404(Answer, pk=pk)
        answer.upvotes += 1
        answer.save()

        return JsonResponse({'message': 'Answer upvoted successfully', 'upvotes': answer.upvotes}, status=200)

@method_decorator(csrf_exempt, name="dispatch")
class DownvoteAnswerView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk, *args, **kwargs):
        answer = get_object_or_404(Answer, pk=pk)
        answer.downvotes += 1
        answer.save()

        return JsonResponse({'message': 'Answer downvoted successfully', 'downvotes': answer.downvotes}, status=200)
