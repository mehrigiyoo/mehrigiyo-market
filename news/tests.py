from django.test import TestCase

from django.test import TestCase
from django.utils import timezone
from .models import Notification

class NotificationModelTest(TestCase):
    def test_create_notification(self):
        notification = Notification.objects.create(
            title='Test Title',
            description='Test Description',
            push_time=timezone.now()
        )
        self.assertEqual(notification.title, 'Test Title')
        self.assertTrue(Notification.objects.filter(title='Test Title').exists())