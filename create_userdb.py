import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="ahmed",
  passwd=""
)

cur=mydb.cursor()

cur.execute("CREATE DATABASE sibi_forms")

cur.execute('''USE sibi_forms''')

cur.execute('''CREATE TABLE users(
                 username VARCHAR(200),
                 password VARCHAR(200))''')

