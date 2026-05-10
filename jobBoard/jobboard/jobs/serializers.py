from rest_framework import serializers
from .models import JobListing, JobCategory
from accounts.serializers import EmployerProfileSerializer


class JobCategorySerializer(serializers.ModelSerializer):
    job_count = serializers.SerializerMethodField()

    class Meta:
        model = JobCategory
        fields = ['id', 'name', 'description', 'job_count', 'created_at']

    def get_job_count(self, obj):
        return obj.jobs.filter(status='active').count()


class JobListingSerializer(serializers.ModelSerializer):
    employer_details = EmployerProfileSerializer(source='employer', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = JobListing
        fields = [
            'id', 'employer', 'employer_details', 'category', 'category_name',
            'title', 'description', 'requirements', 'responsibilities', 'benefits',
            'job_type', 'experience_level', 'location', 'is_remote',
            'salary_min', 'salary_max', 'salary_currency',
            'skills_required', 'openings', 'status', 'deadline',
            'views_count', 'applications_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['employer', 'views_count', 'applications_count', 'created_at', 'updated_at']

    def validate(self, data):
        if data.get('salary_min') and data.get('salary_max'):
            if data['salary_min'] > data['salary_max']:
                raise serializers.ValidationError({'salary_min': 'Minimum salary cannot exceed maximum salary.'})
        return data


class JobListingListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    employer_name = serializers.CharField(source='employer.company_name', read_only=True)
    employer_location = serializers.CharField(source='employer.location', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = JobListing
        fields = [
            'id', 'employer_name', 'employer_location', 'category_name',
            'title', 'job_type', 'experience_level', 'location', 'is_remote',
            'salary_min', 'salary_max', 'salary_currency', 'skills_required',
            'openings', 'status', 'deadline', 'views_count', 'applications_count',
            'created_at'
        ]
