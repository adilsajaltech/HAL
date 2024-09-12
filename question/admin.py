from django.contrib import admin
from .models import *

@admin.register(Flag)
class FlagAdmin(admin.ModelAdmin):
    list_display = ('user', 'reason', 'resolved', 'created', 'updated')
    list_filter = ('resolved', 'reason')
    search_fields = ('user__email', 'description')


admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Tag)
admin.site.register(Comment)