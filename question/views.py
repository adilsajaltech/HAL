from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404, get_list_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Question, Answer, Comment, Tag, Flag, Vote
import json, math
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework import status
from .documents import QuestionDocument, AnswerDocument, CommentDocument, TagDocument
from .utils import search_tags
import reversion
from reversion.models import Version
from .content_management.serializer import FlagSerializer, QuestionSerializer, AnswerSerializer, CommentSerializer
from .content_management.validators import validate_no_contact_info, validate_for_malicious_content
from django_ratelimit.decorators import ratelimit
from django.db.models import Q
from user.models import Profile

# Define the rate limit handler
def handle_ratelimit(request, exception):
    return JsonResponse({'error': "You've exceeded the rate limit. Please try again later."}, status=429)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(ratelimit(key='user', rate='10/h', method='POST', block=True), name='dispatch')
class CreateQuestionView(APIView):
    permission_classes = [IsAuthenticated]
    
    @reversion.create_revision()
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User must be logged in to create a question'}, status=403)
        data = json.loads(request.body)
        title = data.get('title')
        body = data.get('body')
        tags = data.get('tags', [])

        if not title or not body:
            return JsonResponse({'error': 'Title and body are required'}, status=400)

        try:
            validate_no_contact_info(title,user=request.user)
            validate_no_contact_info(body,user=request.user)
            for taggy in tags:
                validate_no_contact_info(taggy,user=request.user)
                validate_for_malicious_content(taggy)
            
            validate_for_malicious_content(title)
            validate_for_malicious_content(body)

        except Exception as e:
            return JsonResponse({'error': f'Error Occured During Validation: {e}'}, status=404)

        question = Question.objects.create(user=request.user, title=title, body=body)
        tag_objects = []
        for tag in tags : 
            Tag_obj, _ = Tag.objects.get_or_create(name=tag)
            tag_objects.append(Tag_obj)
            
        question.tags.set(tag_objects)
        question.save()

        # Increase reputation for creating the question
        profile = get_object_or_404(Profile, user=request.user)
        profile.reputation += 20  # Reward for creating a question
        profile.save()

        return JsonResponse({'message': 'Question created successfully', 'question_id': question.id}, status=201)
    
#==================================ADIL================================================================================

@method_decorator(csrf_exempt, name='dispatch')
class UpdateQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    @reversion.create_revision()
    def post(self, request, pk, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User must be logged in to update a question'}, status=403)
        
        data = json.loads(request.body)
        # question_id = data.get('question_id')
        title = data.get('title')
        body = data.get('body')
        tags = data.get('tags', [])

        if title is None and body is None and not tags:
            return JsonResponse({'error': 'Tags, title, and body are required'}, status=400)
        
        try:
            if title:
                validate_no_contact_info(title,user=request.user)
                validate_for_malicious_content(title)
            if body:
                validate_no_contact_info(body,user=request.user)
                validate_for_malicious_content(body)
            if tags:
                for taggy in tags:
                    validate_no_contact_info(taggy,user=request.user)
                    validate_for_malicious_content(taggy)
        except Exception as e:
            return JsonResponse({'error': f'Error Occured During Validation: {e}'}, status=404)

        question = get_object_or_404(Question, pk=pk)

        # Ensure that only the author can update the question
        if question.user != request.user:
            return JsonResponse({'error': 'You are not authorized to update this question'}, status=403)

        if title is not None:
            question.title = title
        if body is not None:
            question.body = body

        # Update tags
        if tags is not None:
            tag_objects = []
            for tag in tags:
                tag_obj, _ = Tag.objects.get_or_create(name=tag)
                tag_objects.append(tag_obj)  
            question.tags.set(tag_objects)
        question.save()

        return JsonResponse({'message': 'Question updated successfully'}, status=200)

class GetQuestionVersionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, vid, *args, **kwargs):
        # Fetch the question object
        question = get_object_or_404(Question, pk=pk)
        
        # Retrieve the specific version
        try:
            # Fetch version data for the specific question and version_id
            version = reversion.get_for_object(question).get(id=vid)
        except reversion.Version.DoesNotExist:
            return JsonResponse({'error': 'Version not found'}, status=404)

        # Format the version data
        question_data = {
            'id': version.object_id,
            'title': version.field_dict.get('title'),
            'body': version.field_dict.get('body'),
            'tags': list(version.field_dict.get('tags', [])),
            'views_count': version.field_dict.get('views_count'),
            'upvotes': version.field_dict.get('upvotes'),
            'downvotes': version.field_dict.get('downvotes'),
        }
        return JsonResponse(question_data)
    
class GetAllQuestionVersionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        # Fetch the question object
        question = get_object_or_404(Question, pk=pk)

        # Retrieve all versions for the specific question
        versions = Version.objects.get_for_object(question)
        
        # Format the version data
        versions_data = []
        for version in versions:
            revision = version.revision
            versions_data.append({
                'version_id': version.id,
                'revision_id': revision.id if revision else None,  # Revision ID
                'date_created': revision.date_created if revision else None,  # Date created from revision
                'title': version.field_dict.get('title'),
                'body': version.field_dict.get('body'),
                'tags': list(version.field_dict.get('tags', [])),
                'views_count': version.field_dict.get('views_count'),
                'upvotes': version.field_dict.get('upvotes'),
                'downvotes': version.field_dict.get('downvotes'),
            })

        return JsonResponse({'versions': versions_data})
    

class GetAllAnswerVersionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        # Fetch the answer object
        answer = get_object_or_404(Answer, pk=pk)

        # Retrieve all versions for the specific answer
        versions = Version.objects.get_for_object(answer)
        
        # Format the version data
        versions_data = []
        for version in versions:
            revision = version.revision
            versions_data.append({
                'version_id': version.id,
                'revision_id': revision.id if revision else None,  # Revision ID
                'date_created': revision.date_created if revision else None,  # Date created from revision
                'body': version.field_dict.get('body'),
                'upvotes': version.field_dict.get('upvotes'),
                'downvotes': version.field_dict.get('downvotes'),
                'is_accepted': version.field_dict.get('is_accepted'),
            })

        return JsonResponse({'versions': versions_data})
    

class GetAllCommentVersionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        # Fetch the comment object
        comment = get_object_or_404(Comment, pk=pk)

        # Retrieve all versions for the specific comment
        versions = Version.objects.get_for_object(comment)
        
        # Format the version data
        versions_data = []
        for version in versions:
            revision = version.revision
            versions_data.append({
                'version_id': version.id,
                'revision_id': revision.id if revision else None,  # Revision ID
                'date_created': revision.date_created if revision else None,  # Date created from revision
                'content': version.field_dict.get('content'),
                'question_id': version.field_dict.get('question_id'),
                'answer_id': version.field_dict.get('answer_id'),
            })

        return JsonResponse({'versions': versions_data})



@method_decorator(csrf_exempt, name='dispatch')
class UpdateAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    @reversion.create_revision()
    def post(self, request, pk, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User must be logged in to update a answer'}, status=403)
        
        data = json.loads(request.body)
        body = data.get('body')

        if body is None:
            return JsonResponse({'error': 'Body are required'}, status=400)

        answer = get_object_or_404(Answer, pk=pk)

        # Ensure that only the author can update the question
        if answer.user != request.user:
            return JsonResponse({'error': 'You are not authorized to update this answer'}, status=403)
        try:
            if body:
                validate_no_contact_info(body,user=request.user)
                validate_for_malicious_content(body)
        except Exception as e:
            return JsonResponse({'error': f'Error Occured During Validation: {e}'}, status=404)

        answer.body = body

        answer.save()

        return JsonResponse({'message': 'Answer updated successfully'}, status=200)
    
@method_decorator(csrf_exempt, name='dispatch')
class UpdateCommentView(APIView):
    permission_classes = [IsAuthenticated]

    @reversion.create_revision()
    def post(self, request, pk, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User must be logged in to update a comment'}, status=403)
        
        data = json.loads(request.body)
        body = data.get('body')

        if body is None:
            return JsonResponse({'error': 'Body are required'}, status=400)

        comment = get_object_or_404(Comment, pk=pk)

        # Ensure that only the author can update the question
        if comment.user != request.user:
            return JsonResponse({'error': 'You are not authorized to update this comment'}, status=403)
        try:
            if body:
                validate_no_contact_info(body,user=request.user)
                validate_for_malicious_content(body)
        except Exception as e:
            return JsonResponse({'error': f'Error Occured During Validation: {e}'}, status=404)

        comment.content = body

        comment.save()

        return JsonResponse({'message': 'Comment updated successfully'}, status=200)



@method_decorator(csrf_exempt, name='dispatch')
class UserQuestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        questions = get_list_or_404(Question, user=request.user)
        serializer = QuestionSerializer(questions, many=True)
        return JsonResponse(serializer.data, safe=False, json_dumps_params={'indent': 2})
    
@method_decorator(csrf_exempt, name='dispatch')
class UserAnswersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        answers = get_list_or_404(Answer, user=request.user)
        serializer = AnswerSerializer(answers, many=True)
        return JsonResponse(serializer.data, safe=False, json_dumps_params={'indent': 2})
    
@method_decorator(csrf_exempt, name='dispatch')
class UserCommentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        comments = get_list_or_404(Comment, user=request.user)
        serializer = CommentSerializer(comments, many=True)
        return JsonResponse(serializer.data, safe=False, json_dumps_params={'indent': 2})


#==================================ADIL================================================================================

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

# @method_decorator(csrf_exempt, name="dispatch")
# @method_decorator(ratelimit(key='user', rate='15/h', method='POST', block=True), name='dispatch')
# class AnswerQuestionView(APIView):
#     permission_classes = [IsAuthenticated]

#     @reversion.create_revision()
#     def post(self, request, pk, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return JsonResponse({'error': 'User must be logged in to create a question'}, status=status.HTTP_401_UNAUTHORIZED)
        
#         question = get_object_or_404(Question, pk=pk)
#         data = json.loads(request.body)
#         body = data.get('body')

#         if not body:
#             return JsonResponse({'error': 'Answer body is required'}, status=400)
        
#         try:
#             if body:
#                 validate_no_contact_info(body,user=request.user)
#                 validate_for_malicious_content(body)
#         except Exception as e:
#             return JsonResponse({'error': f'Error Occured During Validation: {e}'}, status=404)

#         answer = Answer.objects.create(user=request.user, question=question, body=body)
#         return JsonResponse({'message': 'Answer created successfully', 'answer_id': answer.id}, status=201)

@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(ratelimit(key='user', rate='20/h', method='POST', block=True), name='dispatch')
class CommentOnAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    @reversion.create_revision()
    def post(self, request, pk, *args, **kwargs):
        answer = get_object_or_404(Answer, pk=pk)
        question = answer.question
        data = json.loads(request.body)
        content = data.get('content')

        if not content:
            return JsonResponse({'error': 'Comment content is required'}, status=400)
        
        try:
            if content:
                validate_no_contact_info(content,user=request.user)
                validate_for_malicious_content(content)
        except Exception as e:
            return JsonResponse({'error': f'Error Occured During Validation: {e}'}, status=404)

        comment = Comment.objects.create(user=request.user, question=question, answer=answer, content=content)
        
        # Increase reputation for commenting
        profile = get_object_or_404(Profile, user=request.user)
        profile.reputation += 5  # Reward for commenting
        profile.save()


        return JsonResponse({'message': 'Comment created successfully', 'comment_id': comment.id}, status=201)

# @method_decorator(csrf_exempt, name="dispatch")
# class AcceptAnswerView(APIView):
#     permission_classes = [IsAuthenticated]
#     def post(self, request, pk, *args, **kwargs):
#         answer = get_object_or_404(Answer, pk=pk)
#         question = answer.question

#         if request.user != question.user:
#             return JsonResponse({'error': 'Only the question author can accept an answer'}, status=403)

#         question.answers.update(is_accepted=False)
#         answer.is_accepted = True
#         answer.save()

#         return JsonResponse({'message': 'Answer accepted successfully'}, status=200)

    
# class UpvoteAnswerView(APIView):
#     permission_classes = [IsAuthenticated]

#     @method_decorator(csrf_exempt)
#     @method_decorator(ratelimit(key='user', rate='30/h', method='POST', block=True))
#     def post(self, request, pk, *args, **kwargs):
#         user = request.user
#         answer = get_object_or_404(Answer, pk=pk)

#         if answer.user == user:
#             return JsonResponse({'message': 'You cannot upvote your own answer'}, status=400)

#         existing_vote = Vote.objects.filter(user=user, answer=answer).first()

#         if existing_vote:
#             if existing_vote.vote_type == 'UPVOTE':
#                 return JsonResponse({'message': 'Already upvoted'}, status=400)
#             elif existing_vote.vote_type == 'DOWNVOTE':
#                 answer.downvotes -= 1
#                 answer.upvotes += 1
#                 existing_vote.vote_type = 'UPVOTE'
#                 existing_vote.save()
#                 answer.save()
#                 return JsonResponse({'message': 'Vote updated successfully', 'upvotes': answer.upvotes, 'downvotes': answer.downvotes}, status=200)
        
#         Vote.objects.create(user=user, answer=answer, vote_type='UPVOTE')
#         answer.upvotes += 1
#         answer.save()

#         return JsonResponse({'message': 'Answer upvoted successfully', 'upvotes': answer.upvotes}, status=200)


# class DownvoteAnswerView(APIView):
#     permission_classes = [IsAuthenticated]

#     @method_decorator(csrf_exempt)
#     @method_decorator(ratelimit(key='user', rate='30/h', method='POST', block=True))
#     def post(self, request, pk, *args, **kwargs):
#         user = request.user
#         answer = get_object_or_404(Answer, pk=pk)

#         if answer.user == user:
#             return JsonResponse({'message': 'You cannot downvote your own answer'}, status=400)

#         existing_vote = Vote.objects.filter(user=user, answer=answer).first()

#         if existing_vote:
#             if existing_vote.vote_type == 'DOWNVOTE':
#                 return JsonResponse({'message': 'Already downvoted'}, status=400)
#             elif existing_vote.vote_type == 'UPVOTE':
#                 answer.upvotes -= 1
#                 answer.downvotes += 1
#                 existing_vote.vote_type = 'DOWNVOTE'
#                 existing_vote.save()
#                 answer.save()
#                 return JsonResponse({'message': 'Vote updated successfully', 'upvotes': answer.upvotes, 'downvotes': answer.downvotes}, status=200)
        
#         Vote.objects.create(user=user, answer=answer, vote_type='DOWNVOTE')
#         answer.downvotes += 1
#         answer.save()

#         return JsonResponse({'message': 'Answer downvoted successfully', 'downvotes': answer.downvotes}, status=200)
    

class UpvoteQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    @method_decorator(ratelimit(key='user', rate='30/h', method='POST', block=True))
    def post(self, request, pk, *args, **kwargs):
        user = request.user
        question = get_object_or_404(Question, pk=pk)

        if question.user == user:
            return JsonResponse({'message': 'You cannot upvote your own question'}, status=400)

        # existing_vote = Vote.objects.filter(user=user, question=question).first()

        # if existing_vote:
        #     if existing_vote.vote_type == 'UPVOTE':
        #         return JsonResponse({'message': 'Already upvoted'}, status=400)
        #     elif existing_vote.vote_type == 'DOWNVOTE':
        #         question.downvotes -= 1
        #         question.upvotes += 1
        #         existing_vote.vote_type = 'UPVOTE'
        #         existing_vote.save()
        #         question.save()
        #         return JsonResponse({'message': 'Vote updated successfully', 'upvotes': question.upvotes, 'downvotes': question.downvotes}, status=200)
        
        # Vote.objects.create(user=user, question=question, vote_type='UPVOTE')
        # question.upvotes += 1
        # question.save()


        existing_vote = Vote.objects.filter(user=user, question=question).first()

        if existing_vote:
            if existing_vote.vote_type == 'UPVOTE':
                return JsonResponse({'message': 'Already upvoted'}, status=400)
            elif existing_vote.vote_type == 'DOWNVOTE':
                question.downvotes -= 1
                question.upvotes += 1
                existing_vote.vote_type = 'UPVOTE'
                existing_vote.save()
                question.save()

                # Adjust reputation
                profile_question = get_object_or_404(Profile, user=question.user)
                profile_question.reputation += 7
                profile_question.save()

                profile_user = get_object_or_404(Profile, user=user)
                profile_user.reputation += 1  # Small reward for the upvoter
                profile_user.save()

                return JsonResponse({'message': 'Vote updated successfully', 'upvotes': question.upvotes, 'downvotes': question.downvotes}, status=200)

        Vote.objects.create(user=user, question=question, vote_type='UPVOTE')
        question.upvotes += 1
        question.save()

        # Adjust reputation for the first upvote
        profile_question = get_object_or_404(Profile, user=question.user)
        profile_question.reputation += 5
        profile_question.save()

        profile_user = get_object_or_404(Profile, user=user)
        profile_user.reputation += 1  # Small reward for the upvoter
        profile_user.save()

        return JsonResponse({'message': 'Question upvoted successfully', 'upvotes': question.upvotes}, status=200)
    
class DownvoteQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    @method_decorator(ratelimit(key='user', rate='30/h', method='POST', block=True))
    def post(self, request, pk, *args, **kwargs):
        user = request.user
        question = get_object_or_404(Question, pk=pk)

        if question.user == user:
            return JsonResponse({'message': 'You cannot downvote your own question'}, status=400)

        # existing_vote = Vote.objects.filter(user=user, question=question).first()

        # if existing_vote:
        #     if existing_vote.vote_type == 'DOWNVOTE':
        #         return JsonResponse({'message': 'Already downvoted'}, status=400)
        #     elif existing_vote.vote_type == 'UPVOTE':
        #         question.upvotes -= 1
        #         question.downvotes += 1
        #         existing_vote.vote_type = 'DOWNVOTE'
        #         existing_vote.save()
        #         question.save()
        #         return JsonResponse({'message': 'Vote updated successfully', 'upvotes': question.upvotes, 'downvotes': question.downvotes}, status=200)
        
        # Vote.objects.create(user=user, question=question, vote_type='DOWNVOTE')
        # question.downvotes += 1
        # question.save()


        existing_vote = Vote.objects.filter(user=user, question=question).first()

        if existing_vote:
            if existing_vote.vote_type == 'DOWNVOTE':
                return JsonResponse({'message': 'Already downvoted'}, status=400)
            elif existing_vote.vote_type == 'UPVOTE':
                question.upvotes -= 1
                question.downvotes += 1
                existing_vote.vote_type = 'DOWNVOTE'
                existing_vote.save()
                question.save()

                # Adjust reputation
                profile_question = get_object_or_404(Profile, user=question.user)
                profile_question.reputation -= 5
                profile_question.save()

                profile_user = get_object_or_404(Profile, user=user)
                profile_user.reputation -= 1  # Penalty for downvoting
                profile_user.save()

                return JsonResponse({'message': 'Vote updated successfully', 'upvotes': question.upvotes, 'downvotes': question.downvotes}, status=200)

        Vote.objects.create(user=user, question=question, vote_type='DOWNVOTE')
        question.downvotes += 1
        question.save()

        # Adjust reputation for the first downvote
        profile_question = get_object_or_404(Profile, user=question.user)
        profile_question.reputation -= 2
        profile_question.save()

        profile_user = get_object_or_404(Profile, user=user)
        profile_user.reputation -= 1  # Penalty for downvoting
        profile_user.save()

        return JsonResponse({'message': 'Question downvoted successfully', 'downvotes': question.downvotes}, status=200)
    
class UpvoteCommentView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    @method_decorator(ratelimit(key='user', rate='30/h', method='POST', block=True))
    def post(self, request, pk, *args, **kwargs):
        user = request.user
        comment = get_object_or_404(Comment, pk=pk)

        if comment.user == user:
            return JsonResponse({'message': 'You cannot upvote your own comment'}, status=400)

        # existing_vote = Vote.objects.filter(user=user, comment=comment).first()

        # if existing_vote:
        #     if existing_vote.vote_type == 'UPVOTE':
        #         return JsonResponse({'message': 'Already upvoted'}, status=400)
        #     elif existing_vote.vote_type == 'DOWNVOTE':
        #         comment.downvotes -= 1
        #         comment.upvotes += 1
        #         existing_vote.vote_type = 'UPVOTE'
        #         existing_vote.save()
        #         comment.save()
        #         return JsonResponse({'message': 'Vote updated successfully', 'upvotes': comment.upvotes, 'downvotes': comment.downvotes}, status=200)
        
        # Vote.objects.create(user=user, comment=comment, vote_type='UPVOTE')
        # comment.upvotes += 1
        # comment.save()

        existing_vote = Vote.objects.filter(user=user, comment=comment).first()

        if existing_vote:
            if existing_vote.vote_type == 'UPVOTE':
                return JsonResponse({'message': 'Already upvoted'}, status=400)
            elif existing_vote.vote_type == 'DOWNVOTE':
                comment.downvotes -= 1
                comment.upvotes += 1
                existing_vote.vote_type = 'UPVOTE'
                existing_vote.save()
                comment.save()

                # Adjust reputation
                profile_comment = get_object_or_404(Profile, user=comment.user)
                profile_comment.reputation += 3
                profile_comment.save()

                profile_user = get_object_or_404(Profile, user=user)
                profile_user.reputation += 1  # Small reward for the upvoter
                profile_user.save()

                return JsonResponse({'message': 'Vote updated successfully', 'upvotes': comment.upvotes, 'downvotes': comment.downvotes}, status=200)

        Vote.objects.create(user=user, comment=comment, vote_type='UPVOTE')
        comment.upvotes += 1
        comment.save()

        # Adjust reputation for the first upvote
        profile_comment = get_object_or_404(Profile, user=comment.user)
        profile_comment.reputation += 3
        profile_comment.save()

        profile_user = get_object_or_404(Profile, user=user)
        profile_user.reputation += 1  # Small reward for the upvoter
        profile_user.save()

        return JsonResponse({'message': 'Comment upvoted successfully', 'upvotes': comment.upvotes}, status=200)
    
class DownvoteCommentView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    @method_decorator(ratelimit(key='user', rate='30/h', method='POST', block=True))
    def post(self, request, pk, *args, **kwargs):
        user = request.user
        comment = get_object_or_404(Comment, pk=pk)

        if comment.user == user:
            return JsonResponse({'message': 'You cannot downvote your own comment'}, status=400)

        # existing_vote = Vote.objects.filter(user=user, comment=comment).first()

        # if existing_vote:
        #     if existing_vote.vote_type == 'DOWNVOTE':
        #         return JsonResponse({'message': 'Already downvoted'}, status=400)
        #     elif existing_vote.vote_type == 'UPVOTE':
        #         comment.upvotes -= 1
        #         comment.downvotes += 1
        #         existing_vote.vote_type = 'DOWNVOTE'
        #         existing_vote.save()
        #         comment.save()
        #         return JsonResponse({'message': 'Vote updated successfully', 'upvotes': comment.upvotes, 'downvotes': comment.downvotes}, status=200)
        
        # Vote.objects.create(user=user, comment=comment, vote_type='DOWNVOTE')
        # comment.downvotes += 1
        # comment.save()

        existing_vote = Vote.objects.filter(user=user, comment=comment).first()

        if existing_vote:
            if existing_vote.vote_type == 'DOWNVOTE':
                return JsonResponse({'message': 'Already downvoted'}, status=400)
            elif existing_vote.vote_type == 'UPVOTE':
                comment.upvotes -= 1
                comment.downvotes += 1
                existing_vote.vote_type = 'DOWNVOTE'
                existing_vote.save()
                comment.save()

                # Adjust reputation
                profile_comment = get_object_or_404(Profile, user=comment.user)
                profile_comment.reputation -= 3
                profile_comment.save()

                profile_user = get_object_or_404(Profile, user=user)
                profile_user.reputation -= 1  # Penalty for downvoting
                profile_user.save()

                return JsonResponse({'message': 'Vote updated successfully', 'upvotes': comment.upvotes, 'downvotes': comment.downvotes}, status=200)

        Vote.objects.create(user=user, comment=comment, vote_type='DOWNVOTE')
        comment.downvotes += 1
        comment.save()

        # Adjust reputation for the first downvote
        profile_comment = get_object_or_404(Profile, user=comment.user)
        profile_comment.reputation -= 2
        profile_comment.save()

        profile_user = get_object_or_404(Profile, user=user)
        profile_user.reputation -= 1  # Penalty for downvoting
        profile_user.save()

        return JsonResponse({'message': 'Comment downvoted successfully', 'downvotes': comment.downvotes}, status=200)



# class FlagContentView(APIView):
#     permission_classes = [IsAuthenticated]  # Only authenticated users can flag content

#     def post(self, request, *args, **kwargs):
#         question_id = request.data.get('question_id')
#         answer_id = request.data.get('answer_id')
#         comment_id = request.data.get('comment_id')
        
#         # Ensure at least one content identifier is provided
#         if not question_id and not answer_id and not comment_id:
#             return JsonResponse({"error": "At least one of question_id, answer_id, or comment_id must be provided."}, status=status.HTTP_400_BAD_REQUEST)

#         flag_data = {
#             'user': request.user.id,
#             'reason': request.data.get('reason'),
#             'description': request.data.get('description', '')
#         }
        
#         # Associate the appropriate content with the flag
#         if question_id:
#             try:
#                 flag_data['question'] = Question.objects.get(id=question_id).id
#             except Question.DoesNotExist:
#                 return JsonResponse({"error": "Question not found."}, status=status.HTTP_404_NOT_FOUND)
        
#         if answer_id:
#             try:
#                 flag_data['answer'] = Answer.objects.get(id=answer_id).id
#             except Answer.DoesNotExist:
#                 return JsonResponse({"error": "Answer not found."}, status=status.HTTP_404_NOT_FOUND)
        
#         if comment_id:
#             try:
#                 flag_data['comment'] = Comment.objects.get(id=comment_id).id
#             except Comment.DoesNotExist:
#                 return JsonResponse({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)
        
#         # Serialize the flag data
#         serializer = FlagSerializer(data=flag_data)
        
#         if serializer.is_valid():
#             serializer.save()
#             return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
#         return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class FlagContentView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can flag content

    def post(self, request, *args, **kwargs):
        question_id = request.data.get('question_id')
        answer_id = request.data.get('answer_id')
        comment_id = request.data.get('comment_id')
        reason = request.data.get('reason')
        description = request.data.get('description', '')

        # Ensure at least one content identifier is provided
        if not question_id and not answer_id and not comment_id:
            return JsonResponse({"error": "At least one of question_id, answer_id, or comment_id must be provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize flag data
        flag_data = {
            'user': request.user.id,
            'reason': reason,
            'description': description
        }

        flagged_content = None
        flagged_user = None

        # Associate the appropriate content with the flag
        if question_id:
            try:
                existing_flag = Flag.objects.filter(user=request.user, question_id=question_id).exists()
                if existing_flag:
                    return JsonResponse({"error": "You have already flagged this question."}, status=status.HTTP_400_BAD_REQUEST)
                flagged_content = Question.objects.get(id=question_id)
                flag_data['question'] = flagged_content.id
                flagged_user = flagged_content.user
            except Question.DoesNotExist:
                return JsonResponse({"error": "Question not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if answer_id:
            try:
                existing_flag = Flag.objects.filter(user=request.user, answer_id=answer_id).exists()
                if existing_flag:
                    return JsonResponse({"error": "You have already flagged this answer."}, status=status.HTTP_400_BAD_REQUEST)
                flagged_content = Answer.objects.get(id=answer_id)
                flag_data['answer'] = flagged_content.id
                flagged_user = flagged_content.user
            except Answer.DoesNotExist:
                return JsonResponse({"error": "Answer not found."}, status=status.HTTP_404_NOT_FOUND)

        if comment_id:
            try:
                existing_flag = Flag.objects.filter(user=request.user, comment_id=comment_id).exists()
                if existing_flag:
                    return JsonResponse({"error": "You have already flagged this comment."}, status=status.HTTP_400_BAD_REQUEST)
                flagged_content = Comment.objects.get(id=comment_id)
                flag_data['comment'] = flagged_content.id
                flagged_user = flagged_content.user
            except Comment.DoesNotExist:
                return JsonResponse({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the flag data
        serializer = FlagSerializer(data=flag_data)
        
        if serializer.is_valid():
            serializer.save()

            # Track flags for the flagged user and apply reputation penalty
            flag_count = Flag.objects.filter(Q(question=flagged_content) | Q(answer=flagged_content) | Q(comment=flagged_content)).count()
            
            # Check if the flagged content has reached the penalty threshold
            if flag_count >= 6:  # Threshold for reputation penalty
                profile = get_object_or_404(Profile, user=flagged_user)
                profile.reputation -= 100  # Apply reputation penalty
                profile.reputation = max(1, profile.reputation)  # Ensure reputation doesn't drop below 1
                profile.save()
                # flagged_user.profile.reputation -= 100  # Apply reputation penalty
                # flagged_user.profile.reputation = max(1, flagged_user.profile.reputation)  # Ensure reputation doesn't drop below 1
                # flagged_user.profile.save()

            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)

        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ================================= NEW API's WITH REPUTATION ADDED ===================================================================



#======================= Answer BLOCK ===================================================================================================

@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(ratelimit(key='user', rate='15/h', method='POST', block=True), name='dispatch')
class AnswerQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    @reversion.create_revision()
    def post(self, request, pk, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User must be logged in to create a question'}, status=status.HTTP_401_UNAUTHORIZED)
        
        question = get_object_or_404(Question, pk=pk)
        data = json.loads(request.body)
        body = data.get('body')

        if not body:
            return JsonResponse({'error': 'Answer body is required'}, status=400)
        
        try:
            if body:
                validate_no_contact_info(body,user=request.user)
                validate_for_malicious_content(body)
        except Exception as e:
            return JsonResponse({'error': f'Error Occured During Validation: {e}'}, status=404)

        answer = Answer.objects.create(user=request.user, question=question, body=body)
        

        # Increase reputation for answering the question
        profile = get_object_or_404(Profile, user=request.user)
        profile.reputation += 10
        profile.save()


        return JsonResponse({'message': 'Answer created successfully', 'answer_id': answer.id}, status=201)


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

        # Increase reputation for accepted answer
        profile = get_object_or_404(Profile, user=answer.user)
        profile.reputation += 15
        profile.save()

        return JsonResponse({'message': 'Answer accepted successfully'}, status=200)


class UpvoteAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    @method_decorator(ratelimit(key='user', rate='30/h', method='POST', block=True))
    def post(self, request, pk, *args, **kwargs):
        user = request.user
        answer = get_object_or_404(Answer, pk=pk)

        if answer.user == user:
            return JsonResponse({'message': 'You cannot upvote your own answer'}, status=400)

        existing_vote = Vote.objects.filter(user=user, answer=answer).first()

        if existing_vote:
            if existing_vote.vote_type == 'UPVOTE':
                return JsonResponse({'message': 'Already upvoted'}, status=400)
            elif existing_vote.vote_type == 'DOWNVOTE':
                answer.downvotes -= 1
                answer.upvotes += 1
                existing_vote.vote_type = 'UPVOTE'
                existing_vote.save()
                answer.save()

                # # Adjust reputation
                # answer.user.reputation += 7
                # user.reputation += 1  # Small reward for the upvoter
                # answer.user.save()
                # user.save()


                # Adjust reputation
                profile_answer = get_object_or_404(Profile, user=answer.user)
                profile_answer.reputation += 5
                profile_answer.save()

                profile_user = get_object_or_404(Profile, user=user)
                profile_user.reputation += 1  # Small reward for the upvoter
                profile_user.save()

                return JsonResponse({'message': 'Vote updated successfully', 'upvotes': answer.upvotes, 'downvotes': answer.downvotes}, status=200)

        Vote.objects.create(user=user, answer=answer, vote_type='UPVOTE')
        answer.upvotes += 1
        answer.save()

        # # Adjust reputation for the first upvote
        # answer.user.reputation += 5
        # user.reputation += 1  # Small reward for the upvoter
        # answer.user.save()
        # user.save()


        # Adjust reputation for the first upvote
        profile_answer = get_object_or_404(Profile, user=answer.user)
        profile_answer.reputation += 5
        profile_answer.save()

        profile_user = get_object_or_404(Profile, user=user)
        profile_user.reputation += 1  # Small reward for the upvoter
        profile_user.save()

        return JsonResponse({'message': 'Answer upvoted successfully', 'upvotes': answer.upvotes}, status=200)


class DownvoteAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    @method_decorator(ratelimit(key='user', rate='30/h', method='POST', block=True))
    def post(self, request, pk, *args, **kwargs):
        user = request.user
        answer = get_object_or_404(Answer, pk=pk)

        if answer.user == user:
            return JsonResponse({'message': 'You cannot downvote your own answer'}, status=400)

        existing_vote = Vote.objects.filter(user=user, answer=answer).first()

        if existing_vote:
            if existing_vote.vote_type == 'DOWNVOTE':
                return JsonResponse({'message': 'Already downvoted'}, status=400)
            elif existing_vote.vote_type == 'UPVOTE':
                answer.upvotes -= 1
                answer.downvotes += 1
                existing_vote.vote_type = 'DOWNVOTE'
                existing_vote.save()
                answer.save()

                # # Adjust reputation
                # answer.user.reputation -= 5
                # user.reputation -= 1  # Penalty for downvoting
                # answer.user.save()
                # user.save()


                # Adjust reputation
                profile_answer = get_object_or_404(Profile, user=answer.user)
                profile_answer.reputation -= 5
                profile_answer.save()

                profile_user = get_object_or_404(Profile, user=user)
                profile_user.reputation -= 1  # Penalty for downvoting
                profile_user.save()

                return JsonResponse({'message': 'Vote updated successfully', 'upvotes': answer.upvotes, 'downvotes': answer.downvotes}, status=200)

        Vote.objects.create(user=user, answer=answer, vote_type='DOWNVOTE')
        answer.downvotes += 1
        answer.save()

        # # Adjust reputation for the first downvote
        # answer.user.reputation -= 2
        # user.reputation -= 1  # Penalty for downvoting
        # answer.user.save()
        # user.save()

        # Adjust reputation for the first downvote
        profile_answer = get_object_or_404(Profile, user=answer.user)
        profile_answer.reputation -= 2
        profile_answer.save()

        profile_user = get_object_or_404(Profile, user=user)
        profile_user.reputation -= 1  # Penalty for downvoting
        profile_user.save()

        return JsonResponse({'message': 'Answer downvoted successfully', 'downvotes': answer.downvotes}, status=200)

#======================= Answer BLOCK ===================================================================================================

@method_decorator(csrf_exempt, name='dispatch')
class DeleteQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User must be logged in to delete a question'}, status=403)

        question = get_object_or_404(Question, pk=pk)

        # Ensure that only the author or admin can delete the question
        if question.user != request.user:
            return JsonResponse({'error': 'You are not authorized to delete this question'}, status=403)

        question.delete()

        return JsonResponse({'message': 'Question deleted successfully'}, status=200)
    
@method_decorator(csrf_exempt, name='dispatch')
class DeleteAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User must be logged in to delete a answer'}, status=403)

        question = get_object_or_404(Answer, pk=pk)

        # Ensure that only the author or admin can delete the question
        if question.user != request.user:
            return JsonResponse({'error': 'You are not authorized to delete this answer'}, status=403)

        question.delete()

        return JsonResponse({'message': 'Answer deleted successfully'}, status=200)
    
@method_decorator(csrf_exempt, name='dispatch')
class DeleteCommentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User must be logged in to delete a comment'}, status=403)

        question = get_object_or_404(Comment, pk=pk)

        # Ensure that only the author or admin can delete the question
        if question.user != request.user:
            return JsonResponse({'error': 'You are not authorized to delete this comment'}, status=403)

        question.delete()

        return JsonResponse({'message': 'Comment deleted successfully'}, status=200)