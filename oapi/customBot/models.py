from django.db import models

# Create your models here.


class UserProfile(models.Model):
    username = models.CharField(max_length=150)
    assitantId = models.CharField(max_length=200)
    threadID = models.CharField(max_length=200)

    # email = models.EmailField()
    # password = models.CharField(max_length=100)
    # user_type = models.CharField(max_length=20, choices=[('admin', 'Admin'),('employee', 'Employee'),('student', 'Student'), ('hostelOwner', 'Hostel Owner')])
    