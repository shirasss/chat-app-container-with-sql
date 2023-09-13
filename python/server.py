from flask import Flask, render_template,request,redirect,url_for,session
import csv
import os,re
import base64
from enum import Enum
import datetime
from flask_session import Session
import mysql.connector

# todo: , 

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'your_secret_key!!!!'
app.config['SESSION_COOKIE_NAME'] = 'my_session_cookie'
Session(app)

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            user='root',
            password='root',
            host='mysql-db',
            port=3306,
            database='chat_app_db'
        )
        return connection
    except mysql.connector.Error as err:
        return None


@app.route('/',methods=['GET','POST'] )
def homePage():
    return redirect("/register") 


@app.route('/logout', methods=['GET','POST'])
# def logOut():
#     session.pop('user_name', 'user_password')
#     return redirect('login')
def logOut():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM rooms")
        users = cursor.fetchall()   
        cursor.execute("SELECT * FROM messages")
        messages = cursor.fetchall()

        return f"Connected to MySQL. rooms: {users} ,  messages:{messages}"

    except mysql.connector.Error as err:
        return f"Error: {err}"


def add_user_to_sql(user_name,password):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        insert_query = "INSERT INTO users (user_name, password) VALUES (%s, %s)"
        user_data = (user_name,encode_password(password))
        cursor.execute(insert_query, user_data)
        connection.commit()  # Commit the transaction

    except mysql.connector.Error as err:
        return f"Error: {err}"


def get_rooms_names():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT room_name FROM rooms")
    rooms = cursor.fetchall() 
    rooms_list=[]
    for tup in rooms:
       rooms_list.append(tup[0]) 
    return rooms_list

class user_status(Enum):
    PASS_AND_NAME_MATCH = 1
    NAME_MATCH = 2
    NO_MATCH = 3
    ERROR = 4
    

@app.route('/register',methods=['GET','POST'] )
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        status,msg = check_if_user_exists(username,password)
        if status == user_status.NO_MATCH.value:
           add_user_to_sql(username,(password))
           return redirect("/login")
        elif status == user_status.NAME_MATCH.value:
           return msg
        elif status == user_status.PASS_AND_NAME_MATCH.value:
            return redirect("/login") 
    else:
        return render_template('register.html')
    
def check_if_user_exists(username, password):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "SELECT user_name, password FROM users WHERE user_name = %s"
        cursor.execute(query, (username,))
        user=cursor.fetchone()
        if user is not None:
            stored_password =decode_password(user[1])
            if stored_password == password:
               return 1,"user and password are correct"
            else:
                return 2,"User name already exists"
        else:
             return 3,"new user"
    except mysql.connector.Error as err:
        return f"Error: {err}","error"
  

@app.route('/login', methods=['POST','GET'])
def login():
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        status,msg = check_if_user_exists(username,password)
        if status == user_status.PASS_AND_NAME_MATCH.value:
            session['user_name'] = username
            session['user_password'] = password
            return redirect("/lobby") 
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')


@app.route('/lobby', methods=['GET','POST'])
def lobby():
    if not session.get("user_name"):
        return redirect("/")
    if request.method == 'POST':
        create_a_room(request.form['new_room'])
    else:
        enter_room(request.args.get('room'))
    return render_template('lobby.html', room_names=get_rooms_names())

def create_a_room(room):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "SELECT count(*) FROM rooms WHERE room_name = %s"
        cursor.execute(query, (room,))
        count = cursor.fetchone()[0]
        if count == 0:
           #creating new room
           insert_query = "INSERT INTO rooms (room_name) VALUES (%s)"
           user_data = (room,)
           cursor.execute(insert_query, user_data)
           connection.commit()  # Commit the transaction
           #extract the new room_id and user_id
           query = "SELECT room_id FROM rooms WHERE room_name = %s"
           cursor.execute(query, (room,))
           room_id=cursor.fetchone()[0]
           user_id = 0
           #inserting the first message of the new room to messages table
           insert_message_query = "INSERT INTO messages (room_id,user_id,message,date) VALUES (%s,%s,%s,%s)"
           date = datetime.datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
           welcome_message = "Welcome To {} room".format(room)
           data_values = ( room_id ,user_id,welcome_message, date)
           cursor.execute(insert_message_query, data_values)
           connection.commit()  # Commit the transaction
        else:
            print("The room name already exists")
    except mysql.connector.Error as err:
        return f"Error: {err}","error"
  
    # if room not in get_filenames_without_extensions(os.getenv('ROOMS_DIR')):
    #         room_file = open(os.getenv('ROOMS_DIR')+room+".txt", 'w')
    #         room_file.write('Wellcom To {} room!'.format(room))
    #         room_file.close()
    # else:
    #     print("The room name is already exist")
        

def enter_room(room):
    return render_template('chat.html',room=room)



@app.route('/chat/<room>', methods=['GET','POST'])
def chat_room(room):
    if not session.get("user_name"):
        return redirect("/")
    # Display the specified chat room with all messages sent
    return render_template('chat.html',room=room)


@app.route('/api/clear/<room>', methods=['POST','GET'])
def clear_room_user_data(room):
    if not session.get("user_name"):
        return redirect("/")
    filename = os.getenv('ROOMS_DIR')+room+".txt"
    name_to_remove= session['user_name']
    with open(filename, 'r') as f:
        lines = f.readlines()
    patt = r"^\[.+\]   {}: (.+)$".format(name_to_remove)
    with open(filename, 'w') as f:
        for line in lines:
            if not re.match(patt, line):
                f.write(line)
    return "success"

@app.route('/api/chat/<room>', methods=['GET','POST'])
def updateChat(room):
    if not session.get("user_name"):
        return redirect("/")
    # filename = os.getenv('ROOMS_DIR')+room+".txt"
    if request.method == 'POST':
        msg = request.form['msg']
        if "user_name" in session:
            # Get the current date and time
            # current_datetime = datetime.datetime.now()
            # Format the date and time as a string
            formatted_datetime = datetime.datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
            
            with open(filename,"a") as file:
                file.write("\n"+formatted_datetime+"   "+session.get('user_name')+": "+msg)
    with open(filename,"r") as file:
        room_data = file.read()
        return room_data


def encode_password(password):
    pass_bytes = password.encode('ascii')
    base64_bytes = base64.b64encode(pass_bytes)
    base64_message = base64_bytes.decode('ascii')
    return base64_message

def decode_password(password):
    base64_bytes = password.encode('ascii')
    pass_bytes = base64.b64decode(base64_bytes)
    password = pass_bytes.decode('ascii')
    return password


if __name__ == '__main__':
   app.run(host="0.0.0.0")


 