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
from .utils import search_tags

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
        id_ = data.get('id', 0)  
        if not id_:
            return JsonResponse({'error': 'Search query value is required or not valid'}, status=400)

        page = data.get('page', "0")  
        if not str(page).isdigit() :
            page = 0
    
        else : 
            page = int(page)
        results = Question.objects.filter(id = id_)
        if not results :
            return JsonResponse({'error': 'Searched question is not found'}, status=400)
        else :
            results = results.first()
            
        response_data = {
                'id': results.id,  
                'title': results.title,
                'body': results.body,
                'user': results.user.username,
                'tags': [tag.name for tag in results.tags.all()],
                'views_count': results.views_count,
                'upvotes': results.upvotes,
                'downvotes': results.downvotes,
            }
        results.views_count += 1
        results.save()
        return JsonResponse({'data': response_data}, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class FilterQuestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        query = data.get('query', '')  
        filter_by = data.get('filter_by', '')  
        sort_order = data.get('sort_order', 'desc')  
        page = data.get('page', "1")  
        
        if not str(page).isdigit():
            page = 1
        else:
            page = int(page)

        if not query:
            return JsonResponse({'error': 'Search query is required'}, status=400)
        
        search = QuestionDocument.search().query("multi_match", query=query, fields=['title', 'body', 'tags'], type="best_fields", fuzziness='AUTO').sort('_score')
        
        try :
            if filter_by == 'date':
                search = search.sort('-created') if sort_order == 'desc' else search.sort('created')
            elif filter_by == 'popularity':
                search = search.sort('_score') 
            results = search.execute()
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        
        response_data = [
            {
                'id': hit.meta.id, 
                'title': hit.title,
                'body': hit.body,
                'user': hit.user,
                'tags': list(hit.tags), 
                'views_count': hit.views_count,
                'upvotes': hit.upvotes,
                'downvotes': hit.downvotes,
                'created': hit.created,
                'popularity': (hit.upvotes * 5) + (hit.views_count * 0.1)  
            }
            for hit in results
        ]

        if filter_by == 'popularity':
            response_data.sort(key=lambda x: x['popularity'], reverse=(sort_order == 'desc'))
        
        final_data = {}
        total_pages = math.ceil(len(response_data) / 10)
        final_data['total_pages'] = total_pages
        
        if page > 0 :
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
class SearchTag(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        query = data.get('query', '')  
        if not query:
            return JsonResponse({'error': 'Search query is required'}, status=400)

        page = data.get('page', "0")  
        if not str(page).isdigit():
            page = 0
        else:
            page = int(page)

        
        try:
            results = search_tags(query=query)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        
        response_data = [
            {
                'id': hit.meta.id,  
                'name': hit.name,
                'description': hit.description,
            }
            for hit in results
        ]

        
        final_data = {}
        items_per_page = 10
        total_pages = math.ceil(len(response_data) / items_per_page)
        final_data['total_pages'] = total_pages

        if page > 0 :
            if page < 1 or page > total_pages:
                return JsonResponse({'error': f"Page number must be between 1 and {total_pages}."}, status=status.HTTP_400_BAD_REQUEST)
            ending_ = page * 10
            starting_ = page - 10
        else :
            ending_ = 10
            starting_ = 0
        final_data['tags'] = response_data[starting_ : ending_]
        final_data['next_page'] = page + 1 if total_pages >= page + 1 else 1
        
        
        

        
        
        

        
        
        

        return JsonResponse({'data': final_data}, status=200)

@method_decorator(csrf_exempt, name='dispatch')
class TagsDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        query = data.get('query', '')  
        if not query:
            return JsonResponse({'error': 'Search query is required'}, status=400)

        page = data.get('page', "0")  
        if not str(page).isdigit():
            page = 0
        else:
            page = int(page)
        
        tags = Tag.objects.filter(name = query)
        results = Question.objects.filter(tags=tags.first())
        response_data = [
            {
                'id': hit.id,  
                'title': hit.title,
                'body': hit.body,
                'user': hit.user.username,
                'tags': [tag.name for tag in hit.tags.all()],
                'views_count': hit.views_count,
                'upvotes': hit.upvotes,
                'downvotes': hit.downvotes,
            }
            for hit in results
        ]

        
        final_data = {}
        items_per_page = 10
        total_pages = math.ceil(len(response_data) / items_per_page)
        final_data['total_pages'] = total_pages

        if page > 0 :
            if page < 1 or page > total_pages:
                return JsonResponse({'error': f"Page number must be between 1 and {total_pages}."}, status=status.HTTP_400_BAD_REQUEST)
            ending_ = page * 10
            starting_ = page - 10
        else :
            ending_ = 10
            starting_ = 0
        final_data['tags'] = response_data[starting_ : ending_]
        final_data['next_page'] = page + 1 if total_pages >= page + 1 else 1
        
        
        

        
        
        

        
        
        

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
