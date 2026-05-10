from rest_framework import generics, status, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from .models import JobApplication, ApplicationStatusHistory, Notification
from .serializers import (
    JobApplicationSerializer, ApplicationListSerializer,
    UpdateApplicationStatusSerializer, NotificationSerializer
)


class IsCandidate(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'candidate'


class IsEmployer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'employer'


def create_notification(recipient_email, notif_type, title, message, application_id=None):
    Notification.objects.create(
        recipient_email=recipient_email,
        notification_type=notif_type,
        title=title,
        message=message,
        related_application_id=application_id
    )


# ---------- Candidate: Apply for a job ----------

class ApplyForJobView(generics.CreateAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [IsCandidate]

    def perform_create(self, serializer):
        candidate = self.request.user.candidate_profile
        application = serializer.save(candidate=candidate, status='pending')

        # Update job application count
        job = application.job
        job.applications_count += 1
        job.save(update_fields=['applications_count'])

        # Create status history entry
        ApplicationStatusHistory.objects.create(
            application=application,
            old_status='',
            new_status='pending',
            changed_by=self.request.user.email,
            note='Application submitted.'
        )

        # Notify employer
        create_notification(
            recipient_email=job.employer.user.email,
            notif_type='new_application',
            title=f'New application for "{job.title}"',
            message=f'{candidate.user.full_name} has applied for your job posting "{job.title}".',
            application_id=application.id
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                'message': 'Application submitted successfully.',
                'application': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------- Candidate: View my applications ----------

class MyApplicationsView(generics.ListAPIView):
    serializer_class = ApplicationListSerializer
    permission_classes = [IsCandidate]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'job__job_type']
    ordering_fields = ['applied_at', 'updated_at']
    ordering = ['-applied_at']

    def get_queryset(self):
        return JobApplication.objects.filter(
            candidate=self.request.user.candidate_profile
        ).select_related('job', 'job__employer')


class MyApplicationDetailView(generics.RetrieveAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):
        return JobApplication.objects.filter(candidate=self.request.user.candidate_profile)


class WithdrawApplicationView(APIView):
    permission_classes = [IsCandidate]

    def post(self, request, pk):
        try:
            application = JobApplication.objects.get(pk=pk, candidate=request.user.candidate_profile)
            if application.status in ['offered', 'rejected', 'withdrawn']:
                return Response({'error': f'Cannot withdraw an application with status: {application.status}'}, status=400)

            old_status = application.status
            application.status = 'withdrawn'
            application.save()

            ApplicationStatusHistory.objects.create(
                application=application,
                old_status=old_status,
                new_status='withdrawn',
                changed_by=request.user.email,
                note='Candidate withdrew the application.'
            )

            # Notify employer
            create_notification(
                recipient_email=application.job.employer.user.email,
                notif_type='status_update',
                title=f'Application withdrawn for "{application.job.title}"',
                message=f'{request.user.full_name} has withdrawn their application for "{application.job.title}".',
                application_id=application.id
            )

            return Response({'message': 'Application withdrawn successfully.'})
        except JobApplication.DoesNotExist:
            return Response({'error': 'Application not found.'}, status=404)


# ---------- Employer: View applications for their jobs ----------

class JobApplicationsView(generics.ListAPIView):
    """Employer: list all applications for a specific job."""
    serializer_class = ApplicationListSerializer
    permission_classes = [IsEmployer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['candidate__user__first_name', 'candidate__user__last_name', 'candidate__user__email']
    ordering_fields = ['applied_at', 'updated_at']
    ordering = ['-applied_at']

    def get_queryset(self):
        job_id = self.kwargs['job_id']
        return JobApplication.objects.filter(
            job__id=job_id,
            job__employer=self.request.user.employer_profile
        ).select_related('candidate', 'candidate__user', 'job')


class AllMyJobApplicationsView(generics.ListAPIView):
    """Employer: all applications across all their jobs."""
    serializer_class = ApplicationListSerializer
    permission_classes = [IsEmployer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'job']
    search_fields = ['candidate__user__email', 'candidate__user__first_name', 'job__title']
    ordering_fields = ['applied_at', 'updated_at']
    ordering = ['-applied_at']

    def get_queryset(self):
        return JobApplication.objects.filter(
            job__employer=self.request.user.employer_profile
        ).select_related('candidate', 'candidate__user', 'job')


class ApplicationDetailForEmployerView(generics.RetrieveAPIView):
    """Employer: full detail of a specific application."""
    serializer_class = JobApplicationSerializer
    permission_classes = [IsEmployer]

    def get_queryset(self):
        return JobApplication.objects.filter(job__employer=self.request.user.employer_profile)


class UpdateApplicationStatusView(APIView):
    """Employer: update application status."""
    permission_classes = [IsEmployer]

    def post(self, request, pk):
        try:
            application = JobApplication.objects.get(
                pk=pk,
                job__employer=request.user.employer_profile
            )
        except JobApplication.DoesNotExist:
            return Response({'error': 'Application not found.'}, status=404)

        serializer = UpdateApplicationStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        old_status = application.status
        new_status = serializer.validated_data['status']
        note = serializer.validated_data.get('note', '')
        employer_notes = serializer.validated_data.get('employer_notes', '')

        application.status = new_status
        if employer_notes:
            application.employer_notes = employer_notes
        application.save()

        # Record history
        ApplicationStatusHistory.objects.create(
            application=application,
            old_status=old_status,
            new_status=new_status,
            changed_by=request.user.email,
            note=note
        )

        # Notify candidate
        status_messages = {
            'reviewing': 'Your application is being reviewed.',
            'shortlisted': 'Congratulations! You have been shortlisted.',
            'interview': 'You have been selected for an interview. Please check your email.',
            'offered': 'Congratulations! You have received a job offer.',
            'rejected': 'Thank you for applying. Unfortunately, you have not been selected.',
        }
        notif_types = {
            'reviewing': 'status_update',
            'shortlisted': 'status_update',
            'interview': 'interview',
            'offered': 'offer',
            'rejected': 'rejection',
        }

        create_notification(
            recipient_email=application.candidate.user.email,
            notif_type=notif_types.get(new_status, 'status_update'),
            title=f'Application update for "{application.job.title}"',
            message=status_messages.get(new_status, f'Your application status has been updated to: {new_status}'),
            application_id=application.id
        )

        return Response({
            'message': f'Application status updated to {new_status}.',
            'application_id': application.id,
            'old_status': old_status,
            'new_status': new_status
        })


# ---------- Notifications ----------

class MyNotificationsView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient_email=self.request.user.email)


class MarkNotificationReadView(APIView):
    def post(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk, recipient_email=request.user.email)
            notif.is_read = True
            notif.save()
            return Response({'message': 'Notification marked as read.'})
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found.'}, status=404)


class MarkAllNotificationsReadView(APIView):
    def post(self, request):
        count = Notification.objects.filter(recipient_email=request.user.email, is_read=False).update(is_read=True)
        return Response({'message': f'{count} notifications marked as read.'})


# ---------- Reporting & Stats ----------

class EmployerDashboardView(APIView):
    """Employer: overall stats dashboard."""
    permission_classes = [IsEmployer]

    def get(self, request):
        employer = request.user.employer_profile
        from jobs.models import JobListing
        jobs = JobListing.objects.filter(employer=employer)
        apps = JobApplication.objects.filter(job__employer=employer)

        data = {
            'total_jobs': jobs.count(),
            'active_jobs': jobs.filter(status='active').count(),
            'closed_jobs': jobs.filter(status='closed').count(),
            'total_applications': apps.count(),
            'applications_by_status': {
                'pending': apps.filter(status='pending').count(),
                'reviewing': apps.filter(status='reviewing').count(),
                'shortlisted': apps.filter(status='shortlisted').count(),
                'interview': apps.filter(status='interview').count(),
                'offered': apps.filter(status='offered').count(),
                'rejected': apps.filter(status='rejected').count(),
                'withdrawn': apps.filter(status='withdrawn').count(),
            },
            'top_jobs_by_applications': list(
                jobs.values('id', 'title').annotate(app_count=Count('applications')).order_by('-app_count')[:5]
            ),
            'unread_notifications': Notification.objects.filter(
                recipient_email=request.user.email, is_read=False
            ).count()
        }
        return Response(data)


class CandidateDashboardView(APIView):
    """Candidate: their application stats."""
    permission_classes = [IsCandidate]

    def get(self, request):
        apps = JobApplication.objects.filter(candidate=request.user.candidate_profile)
        data = {
            'total_applications': apps.count(),
            'by_status': {
                'pending': apps.filter(status='pending').count(),
                'reviewing': apps.filter(status='reviewing').count(),
                'shortlisted': apps.filter(status='shortlisted').count(),
                'interview': apps.filter(status='interview').count(),
                'offered': apps.filter(status='offered').count(),
                'rejected': apps.filter(status='rejected').count(),
                'withdrawn': apps.filter(status='withdrawn').count(),
            },
            'unread_notifications': Notification.objects.filter(
                recipient_email=request.user.email, is_read=False
            ).count()
        }
        return Response(data)


class AdminReportView(APIView):
    """Admin: platform-wide statistics."""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from accounts.models import User
        from jobs.models import JobListing
        data = {
            'total_users': User.objects.count(),
            'employers': User.objects.filter(role='employer').count(),
            'candidates': User.objects.filter(role='candidate').count(),
            'total_jobs': JobListing.objects.count(),
            'active_jobs': JobListing.objects.filter(status='active').count(),
            'total_applications': JobApplication.objects.count(),
            'applications_today': JobApplication.objects.filter(
                applied_at__date=__import__('datetime').date.today()
            ).count(),
        }
        return Response(data)
