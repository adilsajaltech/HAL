from django.contrib import admin
from .models import *
from reversion.admin import VersionAdmin

@admin.register(Flag)
class FlagAdmin(admin.ModelAdmin):
    list_display = ('user', 'reason', 'resolved', 'created', 'updated')
    list_filter = ('resolved', 'reason')
    search_fields = ('user__email', 'description')

@admin.register(Question)
class QuestionAdmin(VersionAdmin):
    pass

@admin.register(Answer)
class AnswerAdmin(VersionAdmin):
    pass

@admin.register(Comment)
class CommentAdmin(VersionAdmin):
    pass

# admin.site.register(Question)
# admin.site.register(Answer)
admin.site.register(Tag)
# admin.site.register(Comment)