import cv2
import sqlite3
import numpy as np
import face_recognition
from datetime import datetime
# Connecting database
conn = sqlite3.connect('attendance.db')
db = conn.cursor()
cond = False

# Receiving input for teacher ID
teacher = int(input("Enter Your Teacher ID: "))

# Loop to start camera begins
while True:

    # Capturing Frame and releasing camera
    cap = cv2.VideoCapture(0)
    m, frame = cap.read()
    cap.release()
    cv2.imshow('frame', frame)
    rgb_img2 = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Clearing any old encodings(from 2nd iteration onward only)
    if cond:
        img2_encoding.clear()

    # Generating Face encodings for the fram
    img2_encoding = face_recognition.face_encodings(rgb_img2)
    face_detected = True
    
    # Checking if faces present in image
    if len(img2_encoding) == 0:
        face_detected = False
    else:
        img2_encoding = [img2_encoding[0]]


    if not face_detected:
        print("No Face Detected")
        
    if cv2.waitKey(1) == ord('q'):
        cap.release()
        cv2.destroyAllWindows()
        break


    if face_detected:
        print("Face Detected")

        # Retrieving all images from database in the selected class
        db.execute("SELECT id,image FROM images WHERE id in (SELECT student_id FROM students WHERE class_id in (SELECT class_id FROM classes WHERE teacher in (SELECT teacher_id FROM teachers WHERE teacher_id=?)))",[teacher])
        encodings = []
        faces = db.fetchall()

        # Converting images to cv2 readable format and generating face encodings
        for i in faces:

            download = np.frombuffer(i[1], dtype = "uint8")
            img = cv2.imdecode(download,cv2.IMREAD_COLOR)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img1_encoding = face_recognition.face_encodings(rgb_img)[0]
            encodings.append(img1_encoding)

        # Comparing all the faces in the database with the detected face
        results = face_recognition.compare_faces(encodings,img2_encoding[0],tolerance=0.6)
        index = 0

        # Iterating through results and recording attendance into the database
        for j in results:
            if j:
                id = faces[index][0]
                dateandtime = datetime.now()
                current_date = dateandtime.strftime("%d-%m-%y")
                current_time = dateandtime.strftime("%X")
                db.execute("INSERT INTO attendance VALUES (?,?,?)",[current_date,current_time,id])
                conn.commit()
                name = db.execute("SELECT name FROM students WHERE student_id=?",[id])
                for i in name:
                    name = i[0]
                print(name," is present")
                break
            else:
                print("No Match")
            index+=1
        cond = True
        
        # Wait for 5 seconds
        cv2.waitKey(5000)