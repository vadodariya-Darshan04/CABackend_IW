from django.urls import path
from . import views

urlpatterns = [
    # Categories
    path('categories/', views.JobCategoryListCreateView.as_view(), name='job_categories'),
    path('categories/<int:pk>/', views.JobCategoryDetailView.as_view(), name='job_category_detail'),

    # Job Listings
    path('', views.JobListingListCreateView.as_view(), name='job_list'),
    path('<int:pk>/', views.JobListingDetailView.as_view(), name='job_detail'),

    # Employer-specific
    path('my-jobs/', views.MyJobListingsView.as_view(), name='my_jobs'),
    path('<int:pk>/close/', views.CloseJobView.as_view(), name='close_job'),
    path('<int:pk>/reactivate/', views.ReactivateJobView.as_view(), name='reactivate_job'),
    path('<int:pk>/stats/', views.JobStatsView.as_view(), name='job_stats'),
]
