from config.celery import app
from config.helpers import send_sms_code, validate_sms_code
# from .models import Notification
from account.models import UserModel
from .send_notification import sendPush


@app.task
def send_notification_func(title, description, image_path, type, foreign_id):
    # notification = Notification.objects.get(id=pk)
    # title = notification.title
    # description = notification.description
    # image = notification.image
    # notification_name = notification.notification_name

    # # sending to firebase
    # try:
    #     image_path = image.path
    # except:
    #     image_path = None

    registration_tokens = []

    if foreign_id != "0":
        user = UserModel.objects.get(id=foreign_id)
        registration_tokens.append(user.notificationKey or "-1")
    else:
        keys = list(UserModel.objects.filter().values_list('notificationKey', flat=True))
        for key in keys:
            registration_tokens.append(key or "-1")

    sendPush(title=title, description=description, registration_tokens=registration_tokens,
                    image=image_path, notification_name=type, dataObject={'id': foreign_id})
