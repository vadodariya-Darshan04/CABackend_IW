from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Resume
from .serializers import ResumeSerializer


class IsCandidate(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'candidate'


class ResumeListCreateView(generics.ListCreateAPIView):
    serializer_class = ResumeSerializer
    permission_classes = [IsCandidate]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return Resume.objects.filter(candidate=self.request.user.candidate_profile)

    def perform_create(self, serializer):
        candidate = self.request.user.candidate_profile
        # First resume is default
        is_default = not Resume.objects.filter(candidate=candidate).exists()
        serializer.save(candidate=candidate, is_default=is_default)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                'message': 'Resume uploaded successfully.',
                'resume': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResumeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ResumeSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):
        return Resume.objects.filter(candidate=self.request.user.candidate_profile)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_default and Resume.objects.filter(candidate=request.user.candidate_profile).count() > 1:
            # Assign default to next resume
            next_resume = Resume.objects.filter(
                candidate=request.user.candidate_profile
            ).exclude(id=instance.id).first()
            if next_resume:
                next_resume.is_default = True
                next_resume.save()
        instance.delete()
        return Response({'message': 'Resume deleted successfully.'}, status=status.HTTP_200_OK)


class SetDefaultResumeView(APIView):
    permission_classes = [IsCandidate]

    def post(self, request, pk):
        try:
            resume = Resume.objects.get(pk=pk, candidate=request.user.candidate_profile)
            # Unset existing default
            Resume.objects.filter(candidate=request.user.candidate_profile, is_default=True).update(is_default=False)
            resume.is_default = True
            resume.save(update_fields=['is_default'])
            return Response({'message': 'Default resume updated.', 'resume_id': resume.id})
        except Resume.DoesNotExist:
            return Response({'error': 'Resume not found.'}, status=404)
