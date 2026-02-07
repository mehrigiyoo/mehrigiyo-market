import datetime
from django.db import models
from specialist.models import Doctor
from shop.models import Medicine

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


class Stories(models.Model):
    title = models.TextField()
    title_uz = models.TextField(default="", blank=True)
    title_ru = models.TextField(default="", blank=True)
    title_en = models.TextField(default="", blank=True)
    icon = models.ImageField(upload_to="news/stories/icon", null=True)

    def __str__(self):
        return self.title


class StoriesImage(models.Model):
    story = models.ForeignKey(Stories, on_delete=models.CASCADE, related_name='images')
    image = models.FileField(upload_to=f'news/stories/{today.year}-{today.month}/')

    def __str__(self) -> str:
        return f"ID#{self.id}: {self.image}"



class Advertising(models.Model):
    image = models.ImageField(upload_to=f'medicine/advertising/', null=True, blank=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    text = models.TextField(blank=True, null=True)
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

