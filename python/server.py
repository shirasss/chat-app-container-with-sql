from flask import Flask, render_template,request,redirect,url_for,session
import csv
import os,re
import base64
from enum import Enum
import datetime
from flask_session import Session
import mysql.connector

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'your_secret_key!!!!'
app.config['SESSION_COOKIE_NAME'] = 'my_session_cookie'
Session(app)

@app.route('/logout', methods=['GET','POST'])
# def logOut():
#     session.pop('user_name', 'user_password')
#     return redirect('login')
def logOut():
    try:
        connection = mysql.connector.connect(
            user='root',
            password='root',
            host='mysql-db',  # Use the service name defined in Docker Compose
            port=3306,         # Use the MySQL default port
            database='mydb'
        )
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()

        return f"Connected to MySQL. Users: {users}"

    except mysql.connector.Error as err:
        return f"Error: {err}"


def add_user_to_sql(user_name,password):
    try:
        connection = mysql.connector.connect(
            user='root',
            password='root',
            host='mysql-db',  # Use the service name defined in Docker Compose
            port=3306,         # Use the MySQL default port
            database='mydb'
        )
        cursor = connection.cursor()
        insert_query = "INSERT INTO users (username, password) VALUES (%s, %s)"
        user_data = (user_name,password)
        cursor.execute(insert_query, user_data)
        connection.commit()  # Commit the transaction

    except mysql.connector.Error as err:
        return f"Error: {err}"



# def logOut():
#     try:
#         connection = mysql.connector.connect(
#             user='root',
#             password='root',
#             host='mysql-db',  # Use the service name defined in Docker Compose
#             port=3306,         # Use the MySQL default port
#             database='mydb'
#         )
#         cursor = connection.cursor()
#         insert_query = "INSERT INTO users (username, password) VALUES (%s, %s)"
#         user_data = ('otheruser', '1234')
#         cursor.execute(insert_query, user_data)
#         connection.commit()  # Commit the transaction

#         cursor.execute("SELECT * FROM users")
#         users = cursor.fetchall()

#         return f"Connected to MySQL. Users: {users}"

#     except mysql.connector.Error as err:
#         return f"Error: {err}"


def get_filenames_without_extensions(directory):
  files = os.listdir(directory)
  filenames_without_extensions = []
  for file in files:
    filename, extension = os.path.splitext(file)
    filenames_without_extensions.append(filename)
  return filenames_without_extensions

class user_status(Enum):
    PASS_AND_NAME_MATCH = 1
    NAME_MATCH = 2
    NO_MATCH = 3
    ERROR = 4



@app.route('/',methods=['GET','POST'] )
def homePage():
    return redirect("/register") 
    

@app.route('/register',methods=['GET','POST'] )
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        status,msg = check_if_user_exists(username,password)
        if status == user_status.NO_MATCH.value:
           add_user_to_sql(username,encode_password(password))
           return redirect("/login")
        elif status == user_status.NAME_MATCH.value:
           return msg
        elif status == user_status.PASS_AND_NAME_MATCH.value:
            return redirect("/login") 
    else:
        return render_template('register.html')
    
def check_if_user_exists(username, password):
    filename = os.getenv('DATA_DIR')+"user.csv"
    with open(filename, 'r',newline="") as file:
        csv_reader = csv.reader(file) 
        for row in csv_reader:
            name, pws= row[0],row[1] 
            if name == username:
                if decode_password(pws) == password:
                   return 1,"user and password are correct"
                else:
                    return 2,"User name already exists"
    return 3,"new user"


@app.route('/login', methods=['POST','GET'])
def login():
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        status,msg=check_if_user_exists(username,password)
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
    return render_template('lobby.html', room_names=get_filenames_without_extensions(os.getenv('ROOMS_DIR')))

def create_a_room(room):
    if room not in get_filenames_without_extensions(os.getenv('ROOMS_DIR')):
            room_file = open(os.getenv('ROOMS_DIR')+room+".txt", 'w')
            room_file.write('Wellcom To {} room!'.format(room))
            room_file.close()
    else:
        print("The room name is already exist")
        

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
    filename = os.getenv('ROOMS_DIR')+room+".txt"
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




# from flask import Flask, render_template, request, redirect,  session
# import csv
# import os
# import re
# import base64
# from enum import Enum
# import datetime
# from flask_session import Session
# import mysql.connector

# app = Flask(__name__)
# app.config['SESSION_TYPE'] = 'filesystem'
# app.config['SECRET_KEY'] = 'your_secret_key!!!!'
# Session(app)

# @app.route('/')
# def hello_world():
#     try:
#         connection = mysql.connector.connect(
#             user='root',
#             password='root',
#             host='mysql-db',  # Use the service name defined in Docker Compose
#             port=3306,         # Use the MySQL default port
#             database='mydb'
#         )

#         cursor = connection.cursor()
#         insert_query = "INSERT INTO users (username, password) VALUES (%s, %s)"
#         user_data = ('otheruser', '1234')
#         cursor.execute(insert_query, user_data)
#         connection.commit()  # Commit the transaction

#         cursor.execute("SELECT * FROM users")
#         users = cursor.fetchall()

#         return f"Connected to MySQL. Users: {users}"

#     except mysql.connector.Error as err:
#         return f"Error: {err}"



# # @app.route('/logout')
# # def hello_world():
# #     try:
# #         connection = mysql.connector.connect(
# #             user='root',
# #             password='root',
# #             host='mysql-db',  # Use the service name defined in Docker Compose
# #             port=3306,         # Use the MySQL default port
# #             database='mydb'
# #         )

# #         cursor = connection.cursor()
# #         cursor.execute("SELECT * FROM users")
# #         users = cursor.fetchall()

# #         return f"Connected to MySQL. Users: {users}"

# #     except mysql.connector.Error as err:
# #         return f"Error: {err}"


# def get_filenames_without_extensions(directory):
#   files = os.listdir(directory)
#   filenames_without_extensions = []
#   for file in files:
#     filename, extension = os.path.splitext(file)
#     filenames_without_extensions.append(filename)
#   return filenames_without_extensions

# class user_status(Enum):
#     PASS_AND_NAME_MATCH = 1
#     NAME_MATCH = 2
#     NO_MATCH = 3
#     ERROR = 4



# # @app.route('/',methods=['GET','POST'] )
# # def homePage():
# #     return redirect("/register") 
    

# @app.route('/register',methods=['GET','POST'] )
# def register():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         status,msg = check_if_user_exists(username,password)
#         if status == user_status.NO_MATCH.value:
#            write_to_csv(username,encode_password(password))
#            return redirect("/login")
#         elif status == user_status.NAME_MATCH.value:
#            return msg
#         elif status == user_status.PASS_AND_NAME_MATCH.value:
#             return redirect("/login") 
#     else:
#         return render_template('register.html')
    
# def check_if_user_exists(username, password):
#     filename = os.getenv('DATA_DIR')+"user.csv"
#     with open(filename, 'r',newline="") as file:
#         csv_reader = csv.reader(file) 
#         for row in csv_reader:
#             name, pws= row[0],row[1] 
#             if name == username:
#                 if decode_password(pws) == password:
#                    return 1,"user and password are correct"
#                 else:
#                     return 2,"User name already exists"
#     return 3,"new user"


# def write_to_csv(username,password):
#     filename = os.getenv('DATA_DIR')+"user.csv"
#     with open(filename,"a") as file:
#         writer = csv.writer(file)
#         writer.writerow([username, password])

# @app.route('/login', methods=['POST','GET'])
# def login():
#     if request.method=='POST':
#         username = request.form['username']
#         password = request.form['password']
#         status,msg=check_if_user_exists(username,password)
#         if status == user_status.PASS_AND_NAME_MATCH.value:
#             session['user_name'] = username
#             session['user_password'] = password
#             return redirect("/lobby") 
#         else:
#             return render_template('login.html')
#     else:
#         return render_template('login.html')


# @app.route('/lobby', methods=['GET','POST'])
# def lobby():
#     if not session.get("user_name"):
#         return redirect("/")
#     if request.method == 'POST':
#         create_a_room(request.form['new_room'])
#     else:
#         enter_room(request.args.get('room'))
#     return render_template('lobby.html', room_names=get_filenames_without_extensions(os.getenv('ROOMS_DIR')))

# def create_a_room(room):
#     if room not in get_filenames_without_extensions(os.getenv('ROOMS_DIR')):
#             room_file = open(os.getenv('ROOMS_DIR')+room+".txt", 'w')
#             room_file.write('Wellcom To {} room!'.format(room))
#             room_file.close()
#     else:
#         print("The room name is already exist")
        

# def enter_room(room):
#     return render_template('chat.html',room=room)


# @app.route('/logout', methods=['GET','POST'])
# def logOut():
#     session.pop('user_name', 'user_password')
#     return redirect('login')

# @app.route('/chat/<room>', methods=['GET','POST'])
# def chat_room(room):
#     if not session.get("user_name"):
#         return redirect("/")
#     # Display the specified chat room with all messages sent
#     return render_template('chat.html',room=room)

# # @app.route('/api/clear/<room>', methods=['POST','GET'])
# # def clear_room_data(room):
# #     if not session.get("user_name"):
# #         return redirect("/")
# #     filename = os.getenv('ROOMS_DIR')+room+".txt"
# #     with open(filename, "wb") as file: 
# #         file.truncate(0)      
# #         file.close() 
# #     return "success" 

# @app.route('/api/clear/<room>', methods=['POST','GET'])
# def clear_room_data(room):
#     if not session.get("user_name"):
#         return redirect("/")
#     filename = os.getenv('ROOMS_DIR')+room+".txt"
#     with open(filename, "wb") as file: 
#         file.truncate(0)      
#         file.close() 
#     return "success" 

# @app.route('/api/chat/<room>', methods=['GET','POST'])
# def updateChat(room):
#     if not session.get("user_name"):
#         return redirect("/")
#     filename = os.getenv('ROOMS_DIR')+room+".txt"
#     if request.method == 'POST':
#         msg = request.form['msg']
#         if "user_name" in session:
#             # Get the current date and time
#             # current_datetime = datetime.datetime.now()
#             # Format the date and time as a string
#             formatted_datetime = datetime.datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
#             with open(filename,"a") as file:
#                 file.write("\n"+formatted_datetime+"   "+session.get('user_name')+": "+msg)
#     with open(filename,"r") as file:
#         room_data = file.read()
#         return room_data


# def encode_password(password):
#     pass_bytes = password.encode('ascii')
#     base64_bytes = base64.b64encode(pass_bytes)
#     base64_message = base64_bytes.decode('ascii')
#     return base64_message

# def decode_password(password):
#     base64_bytes = password.encode('ascii')
#     pass_bytes = base64.b64decode(base64_bytes)
#     password = pass_bytes.decode('ascii')
#     return password


# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)
