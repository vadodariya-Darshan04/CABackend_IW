from django.contrib import admin
from .models import JobListing, JobCategory


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'employer', 'job_type', 'location', 'status', 'applications_count', 'created_at']
    list_filter = ['status', 'job_type', 'experience_level', 'is_remote']
    search_fields = ['title', 'employer__company_name', 'location']
    readonly_fields = ['views_count', 'applications_count', 'created_at', 'updated_at']
    ordering = ['-created_at']
