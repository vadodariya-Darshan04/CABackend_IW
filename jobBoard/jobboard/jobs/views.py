from rest_framework import generics, status, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from .models import JobListing, JobCategory
from .serializers import JobListingSerializer, JobListingListSerializer, JobCategorySerializer
from .filters import JobFilter


class IsEmployer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'employer'


class IsEmployerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'employer'


# ---------- Job Categories ----------

class JobCategoryListCreateView(generics.ListCreateAPIView):
    queryset = JobCategory.objects.all()
    serializer_class = JobCategorySerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class JobCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = JobCategory.objects.all()
    serializer_class = JobCategorySerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


# ---------- Job Listings ----------

class JobListingListCreateView(generics.ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = JobFilter
    search_fields = ['title', 'description', 'skills_required', 'location']
    ordering_fields = ['created_at', 'salary_min', 'salary_max', 'views_count', 'applications_count']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [IsEmployer()]

    def get_queryset(self):
        qs = JobListing.objects.select_related('employer', 'category').all()
        # Public: only active jobs
        if not self.request.user.is_authenticated or self.request.user.role != 'employer':
            return qs.filter(status='active')
        # Employer: their own jobs (all statuses)
        if self.request.user.role == 'employer':
            return qs.filter(employer=self.request.user.employer_profile)
        return qs.filter(status='active')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return JobListingListSerializer
        return JobListingSerializer

    def perform_create(self, serializer):
        serializer.save(employer=self.request.user.employer_profile)


class JobListingDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JobListingSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [IsEmployer()]

    def get_queryset(self):
        return JobListing.objects.select_related('employer', 'category').all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.employer.user != request.user:
            return Response({'error': 'You can only edit your own job listings.'}, status=403)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.employer.user != request.user:
            return Response({'error': 'You can only delete your own job listings.'}, status=403)
        return super().destroy(request, *args, **kwargs)


class MyJobListingsView(generics.ListAPIView):
    """Employer: view all their own job listings."""
    serializer_class = JobListingListSerializer
    permission_classes = [IsEmployer]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = JobFilter
    ordering_fields = ['created_at', 'applications_count']
    ordering = ['-created_at']

    def get_queryset(self):
        return JobListing.objects.filter(employer=self.request.user.employer_profile)


class CloseJobView(APIView):
    """Employer: close a job listing."""
    permission_classes = [IsEmployer]

    def post(self, request, pk):
        try:
            job = JobListing.objects.get(pk=pk, employer=request.user.employer_profile)
            job.status = 'closed'
            job.save()
            return Response({'message': 'Job closed successfully.', 'status': job.status})
        except JobListing.DoesNotExist:
            return Response({'error': 'Job not found.'}, status=404)


class ReactivateJobView(APIView):
    """Employer: reactivate a closed job."""
    permission_classes = [IsEmployer]

    def post(self, request, pk):
        try:
            job = JobListing.objects.get(pk=pk, employer=request.user.employer_profile)
            job.status = 'active'
            job.save()
            return Response({'message': 'Job reactivated.', 'status': job.status})
        except JobListing.DoesNotExist:
            return Response({'error': 'Job not found.'}, status=404)


class JobStatsView(APIView):
    """Employer: stats for a specific job."""
    permission_classes = [IsEmployer]

    def get(self, request, pk):
        try:
            job = JobListing.objects.get(pk=pk, employer=request.user.employer_profile)
            from applications.models import JobApplication
            apps = JobApplication.objects.filter(job=job)
            stats = {
                'job_id': job.id,
                'title': job.title,
                'status': job.status,
                'views': job.views_count,
                'total_applications': apps.count(),
                'by_status': {
                    'pending': apps.filter(status='pending').count(),
                    'reviewing': apps.filter(status='reviewing').count(),
                    'shortlisted': apps.filter(status='shortlisted').count(),
                    'interview': apps.filter(status='interview').count(),
                    'offered': apps.filter(status='offered').count(),
                    'rejected': apps.filter(status='rejected').count(),
                    'withdrawn': apps.filter(status='withdrawn').count(),
                }
            }
            return Response(stats)
        except JobListing.DoesNotExist:
            return Response({'error': 'Job not found.'}, status=404)
