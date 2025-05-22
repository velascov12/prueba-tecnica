import sqlite3
import bcrypt

DB_NAME="users.db"

def create_table():
    conn=sqlite3.connect(DB_NAME)
    cursor=conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY UNIQUE NOT NULL,
        passwordhash TEXT NOT NULL)''')
    conn.commit()
    conn.close()
    
    
    
def insert_user(username,password):
    password_hash=bcrypt.hashpw(password.encode("utf-8"),bcrypt.gensalt())
    conn=sqlite3.connect(DB_NAME)
    cursor=conn.cursor()
    cursor.execute("INSERT INTO users (username,passwordhash) VALUES (?,?)",(username,password_hash))
    conn.commit()
    conn.close()

def get_user(username,password):
    conn=sqlite3.connect(DB_NAME)
    cursor=conn.cursor()
    cursor.execute("SELECT passwordhash FROM users WHERE username = ?",(username,))
    row=cursor.fetchone()
    conn.close()
    if row:
        return bcrypt.checkpw(password.encode('utf-8'), row[0])
    return False


