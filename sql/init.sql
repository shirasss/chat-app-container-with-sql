CREATE DATABASE IF NOT EXISTS chat_app_db;
USE chat_app_db;


CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    room_name VARCHAR(255) NOT NULL
);

CREATE TABLE messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    user_id INT NOT NULL,
    message VARCHAR(255) NOT NULL,
    date VARCHAR(255) NOT NULL
    -- FOREIGN KEY (user_id) REFERENCES users(user_id),
    -- FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);
