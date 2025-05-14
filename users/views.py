from email import message
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from .models import Issue,User
from .models import Issue,User, StudentProfile
from rest_framework.response import Response
from rest_framework import status,generics,filters
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, parser_classes

#from ACADEMIC_TRACKING_SYSTEM.backend.AITS_project.settings import DEFAULT_FROM_EMAIL
from .models import Issue,User,LecturerProfile
from .serializers import RegisterSerializer, LoginSerializer, IssueSerializer,StudentProfileSerializer,LecturerProfileSerializer,RegistrarProfileSerializer,UserSerializer
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

User = get_user_model()
class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        print(request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Construct email
            subject = 'Welcome to the Academic Issue Tracking System'
            if user.role == 'student':
                message = f"Hello {user.first_name},\n\nYou have successfully registered into the Academic Issue Tracking System as a student."
            elif user.role == 'lecturer':
                message = f"Hello {user.first_name},\n\nYou have successfully registered into the Academic Issue Tracking System as a lecturer."
            elif user.role == 'registrar':
                message = f"Hello {user.first_name},\n\nYou have successfully registered into the Academic Issue Tracking System as a registrar."
            # Send email
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            return Response(
                {"message": "User created successfully", "user": serializer.data}, 
                status=status.HTTP_201_CREATED
            )
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']  # Use username instead of email
            password = serializer.validated_data['password']
            login_type = serializer.validated_data.get('loginType')  # Use get() for optional field
            
            # Find user by username
            try:
                user = User.objects.get(username=username)  # Find user by username instead of email
                # Authenticate with username and password
                authenticated_user = authenticate(request, username=user.username, password=password)
                
                if authenticated_user is not None:
                    # Optional role check
                    if login_type and authenticated_user.role != login_type:
                        return Response({'error': 'Invalid role for this login type'}, 
                                       status=status.HTTP_403_FORBIDDEN)
                    
                    refresh = RefreshToken.for_user(authenticated_user)
                    return Response({
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                        'user': {
                
                            'id': authenticated_user.id,
                            'username': authenticated_user.username,
                            'email': authenticated_user.email,
                            'role': authenticated_user.role,
                            'first_name': authenticated_user.first_name,
                            'last_name': authenticated_user.last_name,
                                                }
                    })
                return Response({'error': 'Invalid password'}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class StudentProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
         return get_object_or_404(StudentProfile, user=self.request.user)

# View for retrieving the lecturer profile
class LecturerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = LecturerProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.lecturer_profile

# View for retrieving the registrar profile
class RegistrarProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = RegistrarProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.registrar_profile


class SubmitIssueView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        if request.user.role != 'student':
            return Response(
                {'error': 'Only students can submit issues'},
                status=status.HTTP_403_FORBIDDEN
            )
        # Automatically include student details in the request data
        request_data = request.data.copy()
        student_profile = request.user.student_profile
        request_data['first_name'] = request.user.first_name
        request_data['last_name'] = request.user.last_name
        request_data['registration_no'] = student_profile.registration_no # From student profile
        request_data['student_no'] = student_profile.student_no  # From student profile

        serializer = IssueSerializer(data=request.data, context={'request':request})
        if serializer.is_valid():
            serializer.save(submitted_by=request.user)
            #Get the registrar's email
            registrar= User.objects.filter(role='registrar').first()
            if registrar and registrar.email:
                #send email notification to registrar
                send_mail(
                    subject="New Issue Submitted",
                    message=f"A new issue has been submitted by {request.user.first_name}",
                    from_email= settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[registrar.email],
                    fail_silently=False,        

                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @api_view(['POST'])
    @parser_classes([MultiPartParser, FormParser])
    def submit_issue(request):
        serializer = IssueSerializer(data=request.data)
        if serializer.is_valid():
            # Add the current user as the submitter
            issue = serializer.save(submitted_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResolveIssueView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        # validated_data = IssueSerializer(data=request.data, partial=True).is_valid(raise_exception=True)
        if request.user.role != 'lecturer':
            return Response(
                {'error': 'Only lecturers can resolve issues'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            issue = Issue.objects.get(id=request.data["issueId"], assigned_to=request.user)
            if issue.status =='resolved':
                return Response({'error: Issue is already resolved'}, status=status.HTTP_400_BAD_REQUEST)

            issue.status = 'resolved'
            issue.resolved_by = request.user
            issue.resolved_at = timezone.now()
            issue.save()

            #send an email notification to the student who submitted the issue
            student_user= issue.submitted_by
            if student_user and student_user.email:
               send_mail(
                    subject= "Your Issue has been resolved",
                    message=(f"Hello {student_user.first_name},your issue has been successfully resolved "),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[student_user.email],
                    fail_silently=False,   
                    )

                
            return Response({'message': 'Issue resolved successfully'},status=status.HTTP_200_OK)
        except Issue.DoesNotExist:  # Fixed typo in DoesNotExist
            return Response(
                {'error': 'Issue not found or not assigned to you'},status=status.HTTP_404_NOT_FOUND)


# views.py (corrected)
class AssignIssueView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, issue_id):
        if request.user.role != 'registrar':
            return Response(
                {'error': 'Only Registrar can assign issues'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        
        # Validate user_id exists and is a number
        if not user_id:
            return Response(
                {'error': 'Lecturer User ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user_id = int(user_id)  # Convert to integer
        except (ValueError, TypeError):
            return Response(
                {'error': 'User ID must be a valid integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            issue = Issue.objects.get(id=issue_id)
            lecturer = User.objects.get(
                id=user_id, 
                role='lecturer',
                lecturer_profile__isnull=False
            )
                
            issue.assigned_to = lecturer
            issue.status = 'assigned'  # Set to assigned, not in_progress
            issue.save()
            
            return Response({
                'message': 'Issue assigned successfully',
                'assigned_to': {
                    'id': lecturer.id,
                    'name': f"{lecturer.first_name} {lecturer.last_name}",
                    'department': lecturer.lecturer_profile.department if hasattr(lecturer, 'lecturer_profile') else ''
                }
            }, status=status.HTTP_200_OK)
            
        except Issue.DoesNotExist:
            return Response(
                {'error': 'Issue not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'Lecturer not found or not properly registered'},
                status=status.HTTP_404_NOT_FOUND
            )

#functionality of the students dashboard

    
class LecturerSearchView(generics.ListAPIView):
    serializer_class = LecturerProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        query = self.request.GET.get('q', '')

        # Get all users who are lecturers and match the search query
        matching_lecturers = User.objects.filter(
            role='lecturer'
        ).filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        )

        # Return the related LecturerProfile objects
        return LecturerProfile.objects.filter(user__in=matching_lecturers)

class StudentIssueView(generics.ListAPIView):
    serializer_class=IssueSerializer
    permission_classes=[IsAuthenticated]

    def get_queryset(self):
        return Issue.objects.filter(submitted_by=self.request.user).order_by('created_at')



class ResolvedIssuesView(generics.ListAPIView):
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Issue.objects.filter(Q(assigned_to=self.request.user) | Q(submitted_by=self.request.user), status='resolved')

class UsersView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.all()

    def perform_create(self,serializer):
        #O11 serializer.save(student=self.request.use
        serializer.save()

class IssueDetailView(generics.RetrieveAPIView):
    queryset = Issue.objects.all()
    serializer_class=IssueSerializer
    permission_classes=[IsAuthenticated]


class IssueCountView(generics.ListAPIView):
    permission_classes=[IsAuthenticated]

    def list(self,request):
        total_issues = Issue.objects.count()
        resolved_issues = Issue.objects.filter(status="resolved").count()
        pending_issues = Issue.objects.filter(status="pending").count()
        return Response({
            "total_issues":total_issues,
            "resolved_issues":resolved_issues,
            "pending_issues":pending_issues
        })
        

class LogoutView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        try:
            refresh_token=request.data.get('refresh')
            if not RefreshToken:
                return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
            token=RefreshToken(refresh_token)
            token.blacklist() #Blacklist the refresh token
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



#functionality for Registrar dashboard
class RegistrarIssueView(generics.ListAPIView):
    # API endpoint for registrar to view all submitted issues and filter all submitted issues
    
    serializer_class= IssueSerializer
    permission_classes= [IsAuthenticated]
    #Retrieves all issues for the registar
    def get_queryset(self):
        return Issue.objects.all().order_by('created_at')
    #filtering capabalities
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'category']  # Add programme
    search_fields = ['first_name', 'last_name', 'registration_no']  # Add search fields

    # Method for registrars to assign issues to lecturers
    def assign_issue(self, issue, lecturer):
        # Only registrars can assign issues
        if self.role != 'registrar':
            raise PermissionError("Only Registrar can assign issues to lecturers")
        # Ensure the lecturer is of the correct role
        if lecturer.role != 'lecturer':
            raise ValueError("Issues can only be assigned to lecturers")
        # Assign the issue to the lecturer and update its status
        issue.assigned_to = lecturer
        issue.status = 'assigned'
        issue.save()

     #viewing Issue statistics 
class RegisterCountView(generics.ListAPIView):
    permission_classes=[IsAuthenticated]

    def list(self,request):
        if request.user.role == "registrar":
            total_issues = Issue.objects.count()
            resolved_issues = Issue.objects.filter(status="resolved").count()
            pending_issues = Issue.objects.filter(status="pending").count()
            return Response({
            "total_issues":total_issues,
            "resolved_issues":resolved_issues,
            "pending_issues":pending_issues
        })



        
#Functionality of lecture dashboard
class LecturerAssignedIssuesView(generics.ListAPIView):
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Issue.objects.filter(assigned_to=self.request.user).order_by('created_at')
class LecturerIssueDetailView(generics.RetrieveAPIView):
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Issue.objects.filter(assigned_to=self.request.user)
    
class LecturerPendingIssuesView(generics.ListAPIView):
        serializer_class = IssueSerializer
        permission_classes = [IsAuthenticated]
        
        def get_queryset(self):
            return Issue.objects.filter(assigned_to=self.request.user).order_by('-created_at')
    
class LecturerResolvedIssuesView(generics.ListAPIView):
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Issue.objects.filter(assigned_to=self.request.user, status='resolved').order_by('resolved_at')       
    def notify_lecturer(issue):
        lecturer = issue.assigned_to
        if lecturer and lecturer.email:
            send_mail(
                subject="New Issue Assigned",
                message=f"Dear {lecturer.first_name}, a new issue titled '{issue.title}' has been assigned to you.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[lecturer.email],
                fail_silently=False,
            )

class UsersView(generics.ListAPIView):
     serializer_class = UserSerializer
     permission_classes = [IsAuthenticated]
 
     def get_queryset(self):
         return User.objects.all()
     
class DebugRequestView(APIView):
    """
    A simple view that echoes back request data for debugging purposes.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        return Response({
            'headers': dict(request.headers),
            'method': request.method,
            'path': request.path,
            'data': request.data,
            'query_params': request.query_params,
            'user': request.user.username
        }, status=status.HTTP_200_OK)

