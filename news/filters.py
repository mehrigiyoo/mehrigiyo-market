from .models import NewsModel
import django_filters


class NewsFilter(django_filters.FilterSet):

    class Meta:
        model = NewsModel
        fields = ['id', 'name', 'hashtag', 'created_at']
