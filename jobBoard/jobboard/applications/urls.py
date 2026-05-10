from django.urls import path
from . import views

urlpatterns = [
    # Candidate
    path('apply/', views.ApplyForJobView.as_view(), name='apply'),
    path('my-applications/', views.MyApplicationsView.as_view(), name='my_applications'),
    path('my-applications/<int:pk>/', views.MyApplicationDetailView.as_view(), name='my_application_detail'),
    path('my-applications/<int:pk>/withdraw/', views.WithdrawApplicationView.as_view(), name='withdraw_application'),
    path('candidate/dashboard/', views.CandidateDashboardView.as_view(), name='candidate_dashboard'),

    # Employer
    path('job/<int:job_id>/applications/', views.JobApplicationsView.as_view(), name='job_applications'),
    path('employer/all/', views.AllMyJobApplicationsView.as_view(), name='all_employer_applications'),
    path('employer/<int:pk>/', views.ApplicationDetailForEmployerView.as_view(), name='employer_application_detail'),
    path('<int:pk>/update-status/', views.UpdateApplicationStatusView.as_view(), name='update_status'),
    path('employer/dashboard/', views.EmployerDashboardView.as_view(), name='employer_dashboard'),

    # Notifications
    path('notifications/', views.MyNotificationsView.as_view(), name='notifications'),
    path('notifications/<int:pk>/read/', views.MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('notifications/read-all/', views.MarkAllNotificationsReadView.as_view(), name='mark_all_read'),

    # Admin
    path('admin/report/', views.AdminReportView.as_view(), name='admin_report'),
]
