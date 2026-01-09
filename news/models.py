from django.db import models
import datetime

from account.models import UserModel
from specialist.models import Doctor
from shop.models import Medicine
from .tasks import send_notification_func
from django.utils import timezone

# from django.utils.translation import gettext as _

today = datetime.date.today()


class NewsModel(models.Model):
    image = models.ImageField(upload_to=f'news/{today.year}-{today.month}-{today.month}/',
                              null=True, blank=True)
    name = models.CharField(max_length=255)
    hashtag = models.ForeignKey('TagsModel', on_delete=models.RESTRICT)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class TagsModel(models.Model):
    tag_name = models.CharField(max_length=50)

    def __str__(self):
        return self.tag_name

    # def get_news(self):
    #     return NewsModel.objects.filter(hashtag__tag_name=self.tag_name)


class StoriesContent(models.Model):
    content = models.FileField(upload_to='news/stories/')

    content_uz = models.FileField(upload_to='news/stories/', blank=True)
    content_ru = models.FileField(upload_to='news/stories/', blank=True)
    content_en = models.FileField(upload_to='news/stories/', blank=True)

    type = models.CharField(max_length=75, choices=(
        ('photo', 'Photo'),
        ('video', 'Video')
    ))

    def __str__(self) -> str:
        return f"ID#{self.id}: {self.content}"


class Stories(models.Model):
    title = models.TextField()

    title_uz = models.TextField(default="", blank=True)
    title_ru = models.TextField(default="", blank=True)
    title_en = models.TextField(default="", blank=True)

    icon = models.ImageField(upload_to="news/stories/icon", null=True)
    contents = models.ManyToManyField(StoriesContent)

    def __str__(self):
        return self.title


class Advertising(models.Model):
    image = models.ImageField(upload_to=f'medicine/advertising/', null=True, blank=True)
    title = models.CharField(max_length=255)
    text = models.TextField()
    medicine = models.ForeignKey(Medicine, on_delete=models.RESTRICT, null=True, blank=True,
                                 related_name='special_news_med')
    doctor = models.ForeignKey(Doctor, on_delete=models.RESTRICT, null=True, blank=True,
                               related_name='special_news_doc')
    type = models.SmallIntegerField(choices=(
        (1, 'medicines'),
        (2, 'doctors'),
        (3, 'banner')
    ), default=1, db_index=True)


class Notification(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to=f'notification/', null=True, blank=True)
    foreign_id = models.CharField(max_length=255, blank=True, null=True)
    push_time = models.DateTimeField(default=datetime.datetime.now())
    type = models.SmallIntegerField(choices=(
        (1, 'medicines'),
        (2, 'doctors')
    ), default=1, db_index=True)

    # def save(self, *args, **kwargs):
    #     # Obyektni saqlash
    #     super(Notification, self).save(*args, **kwargs)

    #     # Bildirishnoma yuborish vazifasini qo'shish
    #     image_path = None
    #     if self.image:
    #         image_path = self.image.path
    #     send_notification_func.s(
    #         self.title,
    #         self.description,
    #         image_path,
    #         self.type,
    #         self.foreign_id
    #     ).apply_async(eta=self.push_time + datetime.timedelta(seconds=30))

    #     print("LLLLLLLLLLLLLLLLLLLLLLLLLLLLAAAAAAAAA")

    # def save(self, *args, **kwargs):
    #
    #     image_path = None
    #     if self.image:
    #         image_path = self.image.path
    #     send_notification_func.s(self.title, self.description, image_path, self.type, self.foreign_id).apply_async(
    #         eta=self.push_time + datetime.timedelta(seconds=30))
    #     print("LLLLLLLLLLLLLLLLLLLLLLLLLLLLAAAAAAAAA")
    #     super(Notification, self).save(*args, **kwargs)


