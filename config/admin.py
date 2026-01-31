
from utils.fcm import send_fcm
from account.models import UserModel


def send_promotion_to_all():
    """Send promotional notification to all users"""
    users = UserModel.objects.filter(is_active=True)

    count = 0
    for user in users:
        success = send_fcm(
            user=user,
            type='promotion',
            title="🎉 50% Chegirma!",
            body="Bugun barcha konsultatsiyalarga 50% chegirma. Shoshiling!",
            promo_id='summer2026',
            discount='50',
            valid_until='2026-02-28',
            action_url='/promotions/summer2026',
        )
        if success:
            count += 1

    return f"Sent to {count} users"


def send_news_notification(news):
    """Send news notification to all users"""
    users = UserModel.objects.filter(is_active=True)

    for user in users:
        send_fcm(
            user=user,
            type='news',
            title=news.title,
            body=news.summary[:100],
            news_id=news.id,
            category=news.category,
            image_url=news.image.url if news.image else '',
            published_at=news.published_at.isoformat(),
        )