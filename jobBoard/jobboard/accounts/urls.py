from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # User
    path('me/', views.MeView.as_view(), name='me'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),

    # Profiles
    path('employer/profile/', views.EmployerProfileView.as_view(), name='employer_profile'),
    path('employer/profile/<int:pk>/', views.PublicEmployerProfileView.as_view(), name='public_employer_profile'),
    path('employers/', views.AllEmployersView.as_view(), name='all_employers'),
    path('candidate/profile/', views.CandidateProfileView.as_view(), name='candidate_profile'),
]
