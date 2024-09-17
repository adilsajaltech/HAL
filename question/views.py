from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Question, Answer, Comment, Tag
import json, math
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework import status
from .documents import QuestionDocument, AnswerDocument, CommentDocument, TagDocument

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
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        query = data.get('query', '')  # Get the search query from the request
        if not query:
            return JsonResponse({'error': 'Search query is required'}, status=400)

        page = data.get('page', "0")  # Get the search query from the request
        if not str(page).isdigit() :
            page = 0
    
        else : 
            page = int(page)
            
        search = QuestionDocument.search().query("multi_match", query=query, fields=['title', 'body', 'tags'], type="best_fields", fuzziness='AUTO').sort('_score')
        results = search.execute()
        
        # Prepare the response data
        response_data = [
            {
                'id': hit.meta.id,  # Access the ID via `meta.id`
                'title': hit.title,
                'body': hit.body,
                'user': hit.user,
                'tags': list(hit.tags),  # Convert AttrList to Python list
                'views_count': hit.views_count,
                'upvotes': hit.upvotes,
                'downvotes': hit.downvotes,
            }
            for hit in results
        ]
        
        final_data = {}
        total_pages = math.ceil(len(response_data) / 10)
        final_data['total_pages'] = total_pages
        
        if not page == 0 :
            if page < 1 or page > total_pages:
                return JsonResponse({'error': f"Page number must be between 1 and {total_pages}."}, status=status.HTTP_400_BAD_REQUEST)
            ending_ = page * 10
            starting_ = page - 10
        else :
            ending_ = 10
            starting_ = 0
        final_data['questions'] = response_data[starting_ : ending_]
        final_data['next_page'] = page + 1 if total_pages >= page + 1 else 1

        return JsonResponse({'data': final_data}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class TagView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        query = data.get('query', '')  # Get the search query from the request
        if not query:
            return JsonResponse({'error': 'Search query is required'}, status=400)

        page = data.get('page', "0")  # Get the page number from the request
        if not str(page).isdigit():
            page = 0
        else:
            page = int(page)

        # Perform search on the Tag model using Elasticsearch
        search = TagDocument.search(index="tags").query("multi_match", query=query, fields=['name', 'description'], type="best_fields", fuzziness='AUTO').sort('_score')
        results = search.execute()

        # Prepare the response data
        response_data = [
            {
                'id': hit.meta.id,  # Access the ID via `meta.id`
                'name': hit.name,
                'description': hit.description,
            }
            for hit in results
        ]

        # Pagination logic
        final_data = {}
        items_per_page = 10
        total_pages = math.ceil(len(response_data) / items_per_page)
        final_data['total_pages'] = total_pages

        if page < 1 or page > total_pages:
            return JsonResponse({'error': f"Page number must be between 1 and {total_pages}."}, status=400)

        # Calculate the range of items to return for the requested page
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page

        # Add paginated tags to the final response
        final_data['tags'] = response_data[start_index:end_index]
        final_data['next_page'] = page + 1 if page + 1 <= total_pages else 1

        return JsonResponse({'data': final_data}, status=200)

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
