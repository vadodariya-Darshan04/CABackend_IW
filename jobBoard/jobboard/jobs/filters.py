import django_filters
from .models import JobListing


class JobFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    location = django_filters.CharFilter(lookup_expr='icontains')
    skills = django_filters.CharFilter(field_name='skills_required', lookup_expr='icontains')
    salary_min = django_filters.NumberFilter(field_name='salary_min', lookup_expr='gte')
    salary_max = django_filters.NumberFilter(field_name='salary_max', lookup_expr='lte')
    is_remote = django_filters.BooleanFilter()
    job_type = django_filters.ChoiceFilter(choices=JobListing.JOB_TYPE_CHOICES)
    experience_level = django_filters.ChoiceFilter(choices=JobListing.EXPERIENCE_LEVEL_CHOICES)
    category = django_filters.NumberFilter(field_name='category__id')
    employer = django_filters.NumberFilter(field_name='employer__id')
    deadline_after = django_filters.DateFilter(field_name='deadline', lookup_expr='gte')

    class Meta:
        model = JobListing
        fields = [
            'title', 'location', 'skills', 'salary_min', 'salary_max',
            'is_remote', 'job_type', 'experience_level', 'category', 'employer',
            'status', 'deadline_after'
        ]
