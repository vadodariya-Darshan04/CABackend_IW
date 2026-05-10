from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, EmployerProfile, CandidateProfile
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    EmployerProfileSerializer, CandidateProfileSerializer,
    ChangePasswordSerializer
)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            return Response({
                'message': 'Registration successful.',
                'user': UserSerializer(user).data,
                'tokens': tokens
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = get_tokens_for_user(user)
            return Response({
                'message': 'Login successful.',
                'user': UserSerializer(user).data,
                'tokens': tokens
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully.'})
        except Exception:
            return Response({'message': 'Logged out successfully.'})


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({'old_password': 'Incorrect password.'}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------- Employer Profile ----------

class EmployerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = EmployerProfileSerializer

    def get_object(self):
        profile, _ = EmployerProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get(self, request, *args, **kwargs):
        if request.user.role != 'employer':
            return Response({'error': 'Only employers can access this.'}, status=403)
        return super().get(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        if request.user.role != 'employer':
            return Response({'error': 'Only employers can update this.'}, status=403)
        return super().put(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        if request.user.role != 'employer':
            return Response({'error': 'Only employers can update this.'}, status=403)
        return super().patch(request, *args, **kwargs)


class PublicEmployerProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmployerProfileSerializer
    queryset = EmployerProfile.objects.all()


# ---------- Candidate Profile ----------

class CandidateProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CandidateProfileSerializer

    def get_object(self):
        profile, _ = CandidateProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get(self, request, *args, **kwargs):
        if request.user.role != 'candidate':
            return Response({'error': 'Only candidates can access this.'}, status=403)
        return super().get(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        if request.user.role != 'candidate':
            return Response({'error': 'Only candidates can update this.'}, status=403)
        return super().put(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        if request.user.role != 'candidate':
            return Response({'error': 'Only candidates can update this.'}, status=403)
        return super().patch(request, *args, **kwargs)


class AllEmployersView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmployerProfileSerializer
    queryset = EmployerProfile.objects.select_related('user').all()
