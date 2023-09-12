
CREATE DATABASE IF NOT EXISTS mydb;
USE mydb;



CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_name VARCHAR(255) NOT NULL
);

CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    roomID INT NOT NULL,
    username VARCHAR(255) NOT NULL,
    message VARCHAR(255) NOT NULL,
    date DATE

);
INSERT INTO users (username, password) VALUES ('shira', '1234');





-- CREATE DATABASE IF NOT EXISTS mydb;
-- USE mydb;

-- CREATE TABLE users (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     username VARCHAR(255) NOT NULL,
--     password VARCHAR(255) NOT NULL
-- );

-- INSERT INTO users (username, password) VALUES
--     ('user1', 'password1'),
--     ('user2', 'password2');
