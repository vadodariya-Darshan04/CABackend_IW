from rest_framework import serializers
from .models import JobApplication, ApplicationStatusHistory, Notification
from accounts.serializers import CandidateProfileSerializer
from jobs.serializers import JobListingListSerializer
from resumes.serializers import ResumeSerializer


class ApplicationStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationStatusHistory
        fields = ['id', 'old_status', 'new_status', 'changed_by', 'note', 'changed_at']


class JobApplicationSerializer(serializers.ModelSerializer):
    candidate_details = CandidateProfileSerializer(source='candidate', read_only=True)
    job_details = JobListingListSerializer(source='job', read_only=True)
    resume_details = ResumeSerializer(source='resume', read_only=True)
    status_history = ApplicationStatusHistorySerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = JobApplication
        fields = [
            'id', 'candidate', 'candidate_details',
            'job', 'job_details',
            'resume', 'resume_details',
            'cover_letter', 'expected_salary', 'availability_date',
            'status', 'status_display', 'employer_notes',
            'status_history', 'applied_at', 'updated_at'
        ]
        read_only_fields = ['candidate', 'status', 'employer_notes', 'applied_at', 'updated_at']

    def validate_job(self, job):
        if job.status != 'active':
            raise serializers.ValidationError('This job is no longer accepting applications.')
        return job

    def validate(self, data):
        request = self.context.get('request')
        if request and hasattr(request.user, 'candidate_profile'):
            candidate = request.user.candidate_profile
            job = data.get('job')
            if job and JobApplication.objects.filter(candidate=candidate, job=job).exists():
                raise serializers.ValidationError({'job': 'You have already applied to this job.'})
        return data


class ApplicationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for lists."""
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.employer.company_name', read_only=True)
    candidate_name = serializers.CharField(source='candidate.user.full_name', read_only=True)
    candidate_email = serializers.CharField(source='candidate.user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = JobApplication
        fields = [
            'id', 'job_title', 'company_name', 'candidate_name', 'candidate_email',
            'status', 'status_display', 'expected_salary', 'applied_at', 'updated_at'
        ]

class UpdateApplicationStatusSerializer(serializers.Serializer):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewing', 'Reviewing'),
        ('shortlisted', 'Shortlisted'),
        ('interview', 'Interview Scheduled'),
        ('offered', 'Offered'),
        ('rejected', 'Rejected'),
    ]
    status = serializers.ChoiceField(choices=STATUS_CHOICES)
    note = serializers.CharField(required=False, allow_blank=True)
    employer_notes = serializers.CharField(required=False, allow_blank=True)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
