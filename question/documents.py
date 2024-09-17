# your_app/documents.py

from django_elasticsearch_dsl import Document, fields, Index
from django_elasticsearch_dsl.registries import registry
from .models import Question, Answer, Comment, Tag

# Define the Elasticsearch index for questions
questions_index = Index('questions')
questions_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)

@registry.register_document
@questions_index.document
class QuestionDocument(Document):
    # Define only custom fields to be indexed in Elasticsearch
    title = fields.TextField(
        fields={
            'raw': fields.KeywordField(),
        }
    )
    body = fields.TextField()
    tags = fields.ListField(fields.TextField())  # Define custom field logic
    user = fields.TextField(attr='user.username')
    views_count = fields.IntegerField()  # Make sure to define views_count here
    upvotes = fields.IntegerField()  # Make sure to define upvotes here
    downvotes = fields.IntegerField()  # Make sure to define downvotes here

    class Django:
        model = Question  # The model associated with this Document
        # Don't include fields here that already exist in the model

    def prepare_tags(self, instance):
        # Custom logic to index tags as a list of strings
        return [tag.name for tag in instance.tags.all()]
tags_index = Index('tags')
tags_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)

@registry.register_document
@tags_index.document
class TagDocument(Document):
    # Define custom fields to be indexed in Elasticsearch
    name = fields.TextField(
        fields={
            'raw': fields.KeywordField(),
        }
    )
    description = fields.TextField()

    class Django:
        model = Tag  # The model associated with this Document
        # Fields that are indexed are defined as custom fields above

    def prepare_name(self, instance):
        # Custom logic to index name
        return instance.name

    def prepare_description(self, instance):
        # Custom logic to index description
        return instance.description if instance.description else ""

# Define the Elasticsearch index for answers
answers_index = Index('answers')
answers_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)

@registry.register_document
@answers_index.document
class AnswerDocument(Document):
    # Define only custom fields to be indexed in Elasticsearch
    body = fields.TextField()
    user = fields.TextField(attr='user.username')
    question = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'title': fields.TextField(),
    })

    class Django:
        model = Answer
        # Don't include fields here that already exist in the model

    def prepare_question(self, instance):
        return {
            'id': instance.question.id,
            'title': instance.question.title
        }

# Define the Elasticsearch index for comments
comments_index = Index('comments')
comments_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)

@registry.register_document
@comments_index.document
class CommentDocument(Document):
    # Define only custom fields to be indexed in Elasticsearch
    content = fields.TextField()
    user = fields.TextField(attr='user.username')

    class Django:
        model = Comment
        # Don't include fields here that already exist in the model
