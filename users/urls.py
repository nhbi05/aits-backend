from django.urls import path

from .views import( RegisterView,
                   LoginView,
                   SubmitIssueView,
                   AssignIssueView,
                   ResolveIssueView,
                   StudentIssueView,
                   ResolvedIssuesView,
                   IssueDetailView,
                   LecturerProfileView,
                   RegistrarProfileView,
                   StudentProfileView,
                   LogoutView,
                   RegistrarIssueView,
                   IssueCountView,
                   RegisterCountView,
                   LecturerSearchView,
                   LecturerAssignedIssuesView,
                   LecturerIssueDetailView,
                   LecturerPendingIssuesView,
                   DebugRequestView,
                   UsersView,
                   #LecturerResolvedIssueView
                   UsersView,
                   )


from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,)




urlpatterns = [

    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),

    #student
    path('student/profile/', StudentProfileView.as_view(), name='student_profile'),
    path('lecturer/profile/', LecturerProfileView.as_view(), name='lecturer_profile'),
    path('registrar/profile/', RegistrarProfileView.as_view(), name='registrar_profile'),
    path('submit-issue/', SubmitIssueView.as_view(), name='submit_issue'),
    
    path('my-issues/',StudentIssueView.as_view(),name='my-issues'),
    path('resolved-issues/',ResolvedIssuesView.as_view(),name='resolved-issues'),
    path('issue/<int:pk>/',IssueDetailView.as_view(),name='issue-detail'),
    path('issue-count/', IssueCountView.as_view(), name='issue-count'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    #registrar
    path('registrar/issues/', RegistrarIssueView.as_view(), name='registrar_issues'),
    path('Registrar_issue_counts/',RegisterCountView.as_view(),name='Registrar_issue_counts'),
    path('search-lecturers/', LecturerSearchView.as_view(), name='search-lecturers'),#lecturer in the database
    path('assign-issue/<int:issue_id>/', AssignIssueView.as_view(), name='assign_issue'),

    #lecturer 
    path('assigned-issues/', LecturerAssignedIssuesView.as_view(), name='lecturer_assigned_issues'),
    path('lecturer/issue/<int:pk>/',LecturerIssueDetailView.as_view(), name='lecturer_issue_detail'),
    path('lecturer/pending_issues/', LecturerPendingIssuesView.as_view(), name='lecturer_pending_issues'),
    path('resolve-issue/', ResolveIssueView.as_view(), name='resolve_issue'),
    #path('lecturer/resolved-issues/', LecturerResolvedIssuesView.as_view(), name='lecturer_resolved_issues'),
    
    path('api/debug-request/', DebugRequestView.as_view(), name='debug-request'),
    path('users/', UsersView.as_view(), name='users'),
]