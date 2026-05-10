from django.db import models
from accounts.models import CandidateProfile


def resume_upload_path(instance, filename):
    return f'resumes/candidate_{instance.candidate.id}/{filename}'


class Resume(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(max_length=200, default='My Resume')
    file = models.FileField(upload_to=resume_upload_path)
    is_default = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} - {self.candidate.user.full_name}"

    def save(self, *args, **kwargs):
        # Ensure only one default resume per candidate
        if self.is_default:
            Resume.objects.filter(candidate=self.candidate, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
