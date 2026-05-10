from django.contrib import admin
from .models import JobApplication, ApplicationStatusHistory, Notification


class StatusHistoryInline(admin.TabularInline):
    model = ApplicationStatusHistory
    extra = 0
    readonly_fields = ['old_status', 'new_status', 'changed_by', 'note', 'changed_at']


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['id', 'candidate', 'job', 'status', 'applied_at']
    list_filter = ['status']
    search_fields = ['candidate__user__email', 'job__title']
    readonly_fields = ['applied_at', 'updated_at']
    inlines = [StatusHistoryInline]
    ordering = ['-applied_at']


@admin.register(ApplicationStatusHistory)
class ApplicationStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['application', 'old_status', 'new_status', 'changed_by', 'changed_at']
    readonly_fields = ['changed_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient_email', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
    search_fields = ['recipient_email', 'title']
