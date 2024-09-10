from django.shortcuts import render

# Create your views here.
from .models import *
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from serializers import QuestionSerializer, AnswerSerializer, CommentSerializer


class QuestionCreateView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = QuestionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AnswerCreateView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AnswerSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user, question_id=kwargs['question_id'])
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CommentCreateView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            if 'question_id' in kwargs:
                serializer.save(user=request.user, question_id=kwargs['question_id'])
            elif 'answer_id' in kwargs:
                serializer.save(user=request.user, answer_id=kwargs['answer_id'])
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
