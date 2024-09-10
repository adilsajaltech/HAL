from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

# Create your models here.
class TimeStampModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        
class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        """ 
        Create a normal user instead of super user with his/ her personal details.
        """
        if not email:
            raise ValueError('User must have an email address')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Superuser must have an email address')

        email = self.normalize_email(email)
        #user = self.model(email=email, username=email, is_staff=True, is_superuser=True, **extra_fields)
        user = self.model(email=email, is_staff=True, is_superuser=True, **extra_fields)
        #user = self.model(email=email, is_admin = True, is_staff=True, is_superuser=True, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class CustomUser(AbstractUser,TimeStampModel):
    """ 
    This models is create to store and edit the New registered User's Data and edit Django defualt User authentication 
    """

    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(unique=True) 
    # REQUIRED_FIELDS = ["email"]
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return self.is_staff

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True 
    

class Question(TimeStampModel):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='questions')
    title = models.CharField(max_length=255)
    body = models.TextField()
    tags = models.ManyToManyField('Tag', related_name='questions')
    views_count = models.IntegerField(default=0)
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

class Answer(TimeStampModel):
    id = models.BigAutoField(primary_key=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='answers')
    body = models.TextField()
    is_accepted = models.BooleanField(default=False)
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'Answer to {self.question.title}'

class Comment(TimeStampModel):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')

    def __str__(self):
        return f'Comment by {self.user.email}'

class Tag(TimeStampModel):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
    


class Flag(TimeStampModel):
    FLAG_TYPES = [
        ('SPAM', 'Spam'),
        ('INAPPROPRIATE', 'Inappropriate'),
        ('OFF_TOPIC', 'Off-Topic'),
        ('OTHER', 'Other'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='flags')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True, related_name='flags')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True, related_name='flags')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='flags')
    reason = models.CharField(choices=FLAG_TYPES, max_length=20)
    description = models.TextField(null=True, blank=True)  # Additional information about the flag
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f'Flag by {self.user.email} on {self.reason}'