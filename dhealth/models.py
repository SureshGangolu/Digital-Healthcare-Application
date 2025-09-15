from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_doc = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    spec = models.CharField(max_length=100, blank=True)
    license = models.FileField(upload_to='docs/', blank=True)
    address = models.TextField(blank=True)


class Slot(models.Model):
    doc = models.ForeignKey(Profile, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.doc.user.username} - {self.date} {self.time}"

    def get_time_range(self):
        mapping = {
            '09:00': '09:00 AM - 10:00 AM',
            '10:00': '10:00 AM - 11:00 AM',
            '11:00': '11:00 AM - 12:00 PM',
            '12:00': '12:00 PM - 01:00 PM',
            '13:00': '01:00 PM - 02:00 PM',
            '14:00': '02:00 PM - 03:00 PM',
            '15:00': '03:00 PM - 04:00 PM',
            '16:00': '04:00 PM - 05:00 PM',
            '17:00': '05:00 PM - 06:00 PM',
        }
        return mapping.get(self.time.strftime("%H:%M"), self.time.strftime("%H:%M"))


class Booking(models.Model):
    doc = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='d')
    pat = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='p')
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='confirmed')
    FEEDBACK_CHOICES = [(i, str(i)) for i in range(1, 6)]
    feedback_rating = models.PositiveSmallIntegerField(choices=FEEDBACK_CHOICES, null=True, blank=True)
    feedback_comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.pat.user.username} with {self.doc.user.username} on {self.slot.date} {self.slot.time}"

class ChatMessage(models.Model):
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE)
    sender = models.ForeignKey('Profile', on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='', null=True, blank=True)

    file_label = models.CharField(max_length=50, blank=True)       
    file_downloads = models.PositiveIntegerField(default=0)
    
