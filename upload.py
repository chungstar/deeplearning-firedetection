import time
import pathlib
import os

import firebase_admin
from firebase_admin import credentials, storage, db, messaging

from watchdog.observers import Observer
import watchdog.events

cred = credentials.Certificate('yourfirebase.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'yourdatabaseURL',
    'storageBucket': 'yourstorageBucket.appspot.com'
})
bucket = storage.bucket()

def send_to_firebase_cloud_messaging():
    # This registration token comes from the client FCM SDKs.
    registration_token = 'your token'

    # See documentation on defining a message payload.
    message = messaging.Message(
    notification=messaging.Notification(
        title='타이틀 입니다',
        body='바디 입니다',
    ),
    token=registration_token,
    )

    response = messaging.send(message)
    # Response is a message ID string.
    print('Successfully sent message:', response)

class CustomHandler(watchdog.events.PatternMatchingEventHandler):
    
    """Custom handler for Watchdog"""
    def __init__(self, source_path):
        # setting parameters for 'PatternMatchingEventHandler'
        super(CustomHandler, self).__init__(patterns=["*.jpg"], ignore_patterns=["*~"], ignore_directories=True, case_sensitive=False)
        self.source_path = source_path
        self.print_info = None

    def on_created(self, event):
        # time
        timestr = time.strftime("%Y%m%d-%H%M%S")
        # paths
        path_on_cloud = "images/"+ timestr +".jpg"
        path_local = event.src_path
        # upload file
        blob = bucket.blob(path_on_cloud)
        blob.upload_from_filename(path_local)
        # get url of uploaded file
        blob.make_public()
        print(blob.public_url)

        # upload to real time database
        ref = db.reference('Users')
        # Generate a reference to a location 
        ref.push({
            'timeStamp': timestr,
            'uid': "admin",
            'url': blob.public_url
        })
        #retreiving data
        #print(ref.get())
        send_to_firebase_cloud_messaging()
        time.sleep(0.5)



if __name__ == '__main__':
    # get current path as absolute, linux-style path.
    working_path = pathlib.Path(".").absolute().as_posix()
    # create instance of observer and CustomHandler
    observer = Observer()
    handler = CustomHandler(source_path=working_path)

    # start observer, checks files recursively
    observer.schedule(handler, path=working_path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
