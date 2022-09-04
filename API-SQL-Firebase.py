from queue import Empty
from turtle import update
from unittest import result
from flask import Flask ,request, jsonify
import numpy as np
from datetime import datetime
from PIL import Image
import sqlite3
import cv2
from keras.models import Model
import firebase_admin
from firebase_admin import credentials , db
from keras.models import load_model
import pandas as pd
import urllib.request
import socket
import csv
import os
import threading


cred = credentials.Certificate("./databases/final-project-afeef-firebase-adminsdk-8xgm1-11703938a1.json")
firebase_admin.initialize_app(cred,{'databaseURL':'https://final-project-afeef-default-rtdb.firebaseio.com/',
'httpTimeout':30})


conn = sqlite3.connect('./databases/UNI_Project_db.db',check_same_thread=False)
curr=conn.cursor()

query='''CREATE TABLE IF NOT EXISTS UNI_Project_db  (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
	date TEXT,
	result INTEGER,
    flag INTEGER
);'''

#curr.execute(query)
def read_image(img):
        img = Image.open(img)
        img2 = np.asarray(img)
        cv2.imwrite('output.jpg', img2)
        return img2
     


app = Flask(__name__)
@app.route('/add')
def insert_data():
        conn
        curr
        image=str(request.args.get('image'))
        sql = """ INSERT INTO UNI_Project_db
                (date,result,flag) VALUES (?, ?, ?)"""
        try:
            img=read_image(image)
            now = datetime.now()
            curr_date = now.strftime("%d/%m/%Y")
            
           
            model = load_model("trained_model4.h5")
            img = cv2.resize(img,(64,64))
            img = np.reshape(img,[1,64,64,3])

            result=1


            if check_connection():
                flag=1
            else: 
                flag=0
            
            data_tuple = (str(curr_date),result,flag)
            curr.execute(sql, data_tuple)
            ID = curr.lastrowid
            pred = model.predict(img)
            update_result(ID,int(pred[0][0]))
          
            conn.commit()
            insertIntoFirebase(ID,curr_date,int(pred[0][0]))

            return jsonify(int(pred[0][0]))
        except sqlite3.Error as error:
            return "Failed to insert data ", error
        finally:
            if conn:
                conn.commit()

def insertIntoFirebase(id,date,result):
    ref='/' + str(id)
    root=db.reference(ref)
    try:
        data={
            'id':id,
            'data':date,
            'result':result
            
        }
        root.set(data)
        
        return True
    except Exception as e:
        
        return False

def update_result(id,pred):
    conn
    sql = """ UPDATE UNI_Project_db SET result=? where id==?"""
    curr.execute(sql,(pred,id))
    conn.commit()
    return pred


@app.route('/select')
def select_data():
        conn
        start=str(request.args.get("start"))
        end=str(request.args.get("end"))
        sql= """ SELECT * FROM  UNI_Project_db WHERE date BETWEEN ? AND ? """
        curr.execute(sql,(start,end))
        data=curr.fetchall()
        conn.commit()
        d=pd.DataFrame(data)
        d.columns = ['id', 'date','result','flag']
        d.to_csv('select.csv')
        return jsonify(str(data))

def check_flag():
        conn
        sql= """ SELECT * FROM  UNI_Project_db WHERE flag=0 """
        curr.execute(sql)
        dataf=curr.fetchall()
        conn.commit()
        f=pd.DataFrame(dataf)
     
        f.columns = ['id', 'date','result','flag']
        f.to_csv('flag.csv')
        return 'flag.csv'    

def check_connection():
    IPaddress=socket.gethostbyname(socket.gethostname())
    if IPaddress=="127.0.0.1":
      return False
    else:
      return True



def update_flag(id) :
    conn
    sql= """ UPDATE UNI_Project_db SET flag=1 where id==?"""
    curr.execute(sql,(id,))
    conn.commit()
   

def upload_data():
    data=check_flag()
    with open (data,mode='r'):
      csvFile = csv.reader
    table=pd.read_csv('flag.csv')  
  
    
    if len(table)!=0 and check_connection():
        Row_list =[]           
        for index,rows  in table.iterrows():
           my_list=[rows.id,rows.date,rows.result]
           Row_list.append(my_list)
        
        for i in Row_list:
            update_flag(int(i[0]))
            insertIntoFirebase(int(i[0]),i[1],int(i[2]))
    os.remove('flag.csv')   


if __name__ == "__main__":
    app.run(debug=True)
    
# creating thread
    t1 = threading.Thread(target=insert_data)
    t2 = threading.Thread(target=upload_data)

    # starting thread 1
    t1.start()
    # starting thread 2
    t2.start()
 
    # wait until thread 1 is completely executed
    t1.join()
    # wait until thread 2 is completely executed
    t2.join()
 
    # both threads completely executed
    print("Done!")

