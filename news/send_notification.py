import os
import firebase_admin
from firebase_admin import credentials, messaging

firebase_secret_path = os.environ.get(
    'FIREBASE_CRED_PATH',
    './config/doctor-ali-firebase-adminsdk-hujjz-7b33529111.json'
)

# Container ichida faqat faylni o'qiydi, directory emas
if os.path.isdir(firebase_secret_path):
    # Secret noto'g'ri mount qilingan
    raise ValueError(f"Firebase secret path is a directory, expected a file: {firebase_secret_path}")

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_secret_path)
    firebase_admin.initialize_app(cred)

def sendPush(title, description, registration_tokens, image=None, dataObject=None):
    if not registration_tokens:
        return None
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=description, image=image),
        data=dataObject or {},
        tokens=registration_tokens,
    )
    response = messaging.send_multicast(message)
    return response





# import firebase_admin
# from firebase_admin import credentials, messaging
#
# cred = credentials.Certificate("config/doctor-ali-firebase-adminsdk-hujjz-7b33529111.json")
# firebase_admin.initialize_app(cred)
#
#
# def sendPush(title, description, registration_tokens, image=None, notification_name=None, dataObject=None):
#     # See documentation on defining a message payload.
#     message = messaging.MulticastMessage(
#         notification=messaging.Notification(
#             title=title,
#             body=description,
#             image=image,
#         ),
#         data=dataObject,
#         tokens=registration_tokens,
#     )
#
#     # Send a message to the device corresponding to the provided
#     # registration token.
#     response = messaging.send_multicast(message)
#     # Response is a message ID string.
#     return response