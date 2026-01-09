import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate("config/doctor-ali-firebase-adminsdk-hujjz-7b33529111.json")
firebase_admin.initialize_app(cred)


def sendPush(title, description, registration_tokens, image=None, notification_name=None, dataObject=None):
    # See documentation on defining a message payload.
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=description,
            image=image,
        ),
        data=dataObject,
        tokens=registration_tokens,
    )

    # Send a message to the device corresponding to the provided
    # registration token.
    response = messaging.send_multicast(message)
    # Response is a message ID string.
    return response