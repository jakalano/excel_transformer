from django.contrib import admin
from .models import Action, Template

class ActionAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'uploaded_file', 'timestamp', 'user', 'undone')
    list_filter = ('action_type', 'timestamp', 'user', 'undone')
    search_fields = ('action_type', 'uploaded_file__file', 'user__username', 'session_id')

class TemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    list_filter = ('user',)
    search_fields = ('name', 'user__username')

admin.site.register(Action, ActionAdmin)
admin.site.register(Template, TemplateAdmin)
