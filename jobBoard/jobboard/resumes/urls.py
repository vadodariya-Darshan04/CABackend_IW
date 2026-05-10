from django.urls import path
from . import views

urlpatterns = [
    path('', views.ResumeListCreateView.as_view(), name='resume_list'),
    path('<int:pk>/', views.ResumeDetailView.as_view(), name='resume_detail'),
    path('<int:pk>/set-default/', views.SetDefaultResumeView.as_view(), name='set_default_resume'),
]
