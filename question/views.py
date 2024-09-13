from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404, get_list_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Question, Answer, Comment, Tag, Flag, Vote
import json
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework import status
import reversion
from reversion.models import Version
from .content_management.serializer import FlagSerializer, QuestionSerializer, AnswerSerializer, CommentSerializer
from .content_management.validators import validate_no_contact_info, validate_for_malicious_content
from django_ratelimit.decorators import ratelimit

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
        return JsonResponse({'message': 'Answer created successfully', 'answer_id': answer.id}, status=201)

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

# @method_decorator(csrf_exempt, name="dispatch")
# @method_decorator(ratelimit(key='user', rate='30/h', method='POST', block=True), name='dispatch')
# class UpvoteAnswerView(APIView):
#     permission_classes = [IsAuthenticated]
#     def post(self, request, pk, *args, **kwargs):
#         user = request.user
#         answer = get_object_or_404(Answer, pk=pk)
#         answer_user = answer.user

#         if answer.user == user:
#             return JsonResponse({'message': 'You cannot upvote your own Answer'}, status=400)


#         answer.upvotes += 1
#         answer.save()

#         return JsonResponse({'message': 'Answer upvoted successfully', 'upvotes': answer.upvotes}, status=200)

# @method_decorator(csrf_exempt, name="dispatch")
# @method_decorator(ratelimit(key='user', rate='30/h', method='POST', block=True), name='dispatch')
# class DownvoteAnswerView(APIView):
#     permission_classes = [IsAuthenticated]
#     def post(self, request, pk, *args, **kwargs):
#         user = request.user
#         answer = get_object_or_404(Answer, pk=pk)
#         answer_user = answer.user

#         if answer.user == user:
#             return JsonResponse({'message': 'You cannot downvoted your own Answer'}, status=400)
        
#         answer.downvotes += 1
#         answer.save()

#         return JsonResponse({'message': 'Answer downvoted successfully', 'downvotes': answer.downvotes}, status=200)
    
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
                return JsonResponse({'message': 'Vote updated successfully', 'upvotes': answer.upvotes, 'downvotes': answer.downvotes}, status=200)
        
        Vote.objects.create(user=user, answer=answer, vote_type='UPVOTE')
        answer.upvotes += 1
        answer.save()

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
                return JsonResponse({'message': 'Vote updated successfully', 'upvotes': answer.upvotes, 'downvotes': answer.downvotes}, status=200)
        
        Vote.objects.create(user=user, answer=answer, vote_type='DOWNVOTE')
        answer.downvotes += 1
        answer.save()

        return JsonResponse({'message': 'Answer downvoted successfully', 'downvotes': answer.downvotes}, status=200)
    

class UpvoteQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    @method_decorator(ratelimit(key='user', rate='30/h', method='POST', block=True))
    def post(self, request, pk, *args, **kwargs):
        user = request.user
        question = get_object_or_404(Question, pk=pk)

        if question.user == user:
            return JsonResponse({'message': 'You cannot upvote your own question'}, status=400)

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
                return JsonResponse({'message': 'Vote updated successfully', 'upvotes': question.upvotes, 'downvotes': question.downvotes}, status=200)
        
        Vote.objects.create(user=user, question=question, vote_type='UPVOTE')
        question.upvotes += 1
        question.save()

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
                return JsonResponse({'message': 'Vote updated successfully', 'upvotes': question.upvotes, 'downvotes': question.downvotes}, status=200)
        
        Vote.objects.create(user=user, question=question, vote_type='DOWNVOTE')
        question.downvotes += 1
        question.save()

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
                return JsonResponse({'message': 'Vote updated successfully', 'upvotes': comment.upvotes, 'downvotes': comment.downvotes}, status=200)
        
        Vote.objects.create(user=user, comment=comment, vote_type='UPVOTE')
        comment.upvotes += 1
        comment.save()

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
                return JsonResponse({'message': 'Vote updated successfully', 'upvotes': comment.upvotes, 'downvotes': comment.downvotes}, status=200)
        
        Vote.objects.create(user=user, comment=comment, vote_type='DOWNVOTE')
        comment.downvotes += 1
        comment.save()

        return JsonResponse({'message': 'Comment downvoted successfully', 'downvotes': comment.downvotes}, status=200)



class FlagContentView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can flag content

    def post(self, request, *args, **kwargs):
        question_id = request.data.get('question_id')
        answer_id = request.data.get('answer_id')
        comment_id = request.data.get('comment_id')
        
        # Ensure at least one content identifier is provided
        if not question_id and not answer_id and not comment_id:
            return JsonResponse({"error": "At least one of question_id, answer_id, or comment_id must be provided."}, status=status.HTTP_400_BAD_REQUEST)

        flag_data = {
            'user': request.user.id,
            'reason': request.data.get('reason'),
            'description': request.data.get('description', '')
        }
        
        # Associate the appropriate content with the flag
        if question_id:
            try:
                flag_data['question'] = Question.objects.get(id=question_id).id
            except Question.DoesNotExist:
                return JsonResponse({"error": "Question not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if answer_id:
            try:
                flag_data['answer'] = Answer.objects.get(id=answer_id).id
            except Answer.DoesNotExist:
                return JsonResponse({"error": "Answer not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if comment_id:
            try:
                flag_data['comment'] = Comment.objects.get(id=comment_id).id
            except Comment.DoesNotExist:
                return JsonResponse({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Serialize the flag data
        serializer = FlagSerializer(data=flag_data)
        
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
