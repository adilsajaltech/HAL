

from django_elasticsearch_dsl import Document, fields, Index
from django_elasticsearch_dsl.registries import registry
from .models import Question, Answer, Comment, Tag


questions_index = Index('questions')
questions_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)

@registry.register_document
@questions_index.document
class QuestionDocument(Document):
    
    title = fields.TextField(
        fields={
            'raw': fields.KeywordField(),
        }
    )
    body = fields.TextField()
    tags = fields.ListField(fields.TextField())  
    user = fields.TextField(attr='user.username')
    views_count = fields.IntegerField()  
    upvotes = fields.IntegerField()  
    downvotes = fields.IntegerField()  
    created = fields.DateField()

    class Django:
        model = Question  
        

    def prepare_tags(self, instance):
        
        return [tag.name for tag in instance.tags.all()]
tags_index = Index('tags')
tags_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)

@registry.register_document
@tags_index.document
class TagDocument(Document):
    
    name = fields.TextField(
        fields={
            'raw': fields.KeywordField(),
        }
    )
    description = fields.TextField()

    class Django:
        model = Tag  
        

    def prepare_name(self, instance):
        
        return instance.name

    def prepare_description(self, instance):
        
        return instance.description if instance.description else ""


answers_index = Index('answers')
answers_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)

@registry.register_document
@answers_index.document
class AnswerDocument(Document):
    
    body = fields.TextField()
    user = fields.TextField(attr='user.username')
    question = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'title': fields.TextField(),
    })

    class Django:
        model = Answer
        

    def prepare_question(self, instance):
        return {
            'id': instance.question.id,
            'title': instance.question.title
        }


comments_index = Index('comments')
comments_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)

@registry.register_document
@comments_index.document
class CommentDocument(Document):
    
    content = fields.TextField()
    user = fields.TextField(attr='user.username')

    class Django:
        model = Comment
        
