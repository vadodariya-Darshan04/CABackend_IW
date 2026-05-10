from django.contrib import admin
from .models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['title', 'candidate', 'is_default', 'uploaded_at']
    list_filter = ['is_default']
    search_fields = ['candidate__user__email', 'title']
