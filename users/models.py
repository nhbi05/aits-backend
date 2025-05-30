# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth import get_user_model


class User(AbstractUser):
    #role choices
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
        ('registrar', 'Registrar'),
    ]
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    # Method for students to submit issues
    def submit_issue(self, category, description, course_unit, semester, year_of_study):
        # Only students are allowed to submit issues
        if self.role != 'student':
            raise PermissionError("Only students can submit issues")
        # Create and return a new Issue object
        return Issue.objects.create(
            category=category,
            status='pending',
            description=description,
            course_unit=course_unit,
            semester=semester,
            year_of_study=year_of_study,
            submitted_by=self  # Set the user who submitted the issue
        )

    # Method for lecturers to resolve assigned issues
    def resolve_issue(self, issue):
        if self.role != 'lecturer':
            raise PermissionError("Only lecturers can resolve issues")
        if issue.assigned_to != self:
            raise PermissionError("You can only resolve issues assigned to you")
        issue.status = 'resolved'
        issue.resolved_at = timezone.now()
        issue.save()


# Profile model for students, linked to the User model
class StudentProfile(models.Model):
    PROGRAMME_CHOICES = [
        ('BSCS', 'Bachelor of Science in Computer Science'),
        ('BSSE', 'Bachelor of Science in Software Engineering'),
        ('BIT', 'Bachelor of Information Systems & Technology'),
        ('BLIS', 'Bachelor of Library & Information Systems'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    registration_no = models.CharField(max_length=50, unique=True)  # Unique student identifier
    student_no = models.CharField(max_length=50, unique=True)
    programme = models.CharField(max_length=100, choices=PROGRAMME_CHOICES)


# Profile model for lecturers, linked to the User model
class LecturerProfile(models.Model):
    DEPARTMENT_CHOICES = [
        ('CS', 'Department of Computer Science'),
        ('IS', 'Department of Information Systems'),
        ('DIT', 'Department of Information Technology'),
        ('NET', 'Department of Networks'),
        ('RAM', 'Department of Records and Archives Management'),
        ('LIS', 'Department of Library & Information Science'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lecturer_profile')
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES)  # Changed from ForeignKey to CharField



class RegistrarProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='registrar_profile')
    college = models.CharField(max_length=100)  # College name


class Issue(models.Model):
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]
    issue_id = models.CharField(max_length=20, unique=True, editable=False)
    # the choices for the issue category
    CATEGORY_CHOICES = [
        ('missing_marks', 'Missing Marks'),
        ('appeal', 'Appeal'),
        ('correction', 'Correction'),
        ('others', 'Others'),
    ]
    # New choices for year of study 
    YEAR_OF_STUDY = [
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
    ]
    # New choices for semester
    SEMESTER_OF_STUDY = [
        ('Semester 1', 'Semester 1'),
        ('Semester 2', 'Semester 2'),
    ]
    student_no = models.CharField(max_length=20)
    registration_no = models.CharField(max_length=20)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField()
    course_unit = models.CharField(max_length=100)
    year_of_study = models.IntegerField(choices=YEAR_OF_STUDY)
    semester = models.CharField(max_length=20, choices=SEMESTER_OF_STUDY)
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submitted_issues")
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_issues")
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    lecturer_name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    attachments = models.FileField(upload_to="issue_attachments/", blank=True, null=True)

    def _str_(self):
        return f"Issue {self.id} - {self.category} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.issue_id:
            # Generate a unique issue ID (e.g., 'ISSUE-0001')
            last_issue = Issue.objects.order_by('-id').first()
            if last_issue and last_issue.issue_id:
                last_num = int(last_issue.issue_id.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.issue_id = f'ISSUE-{new_num:04d}'
        super().save(*args, **kwargs)
