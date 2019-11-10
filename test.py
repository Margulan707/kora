import face_recognition
import picamera
import numpy as np
import cv2

camera = picamera.PiCamera()
camera.resolution = (1600, 1200)
frame = np.empty((1200,1600,3),dtype=np.uint8)
while True:
    camera.capture(frame, format="bgr", use_video_port=True)
    small_frame = cv2.resize(frame, (400, 300))
    small_faces = face_recognition.face_locations(small_frame)
    faces = face_recognition.face_locations(frame)
    if faces and small_faces:
        i=0
        for i in range(len(faces)):
            print(i)
            print(faces[i][0] / small_faces[i][0])
            print(faces[i][1] / small_faces[i][1])
            print(faces[i][2] / small_faces[i][2])
            print(faces[i][3] / small_faces[i][3])
            i += 1