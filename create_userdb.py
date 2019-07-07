import mysql.connector


mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  passwd=""
)

cur=mydb.cursor()

cur.execute("CREATE DATABASE sibi_forms")

cur.execute('''USE sibi_forms''')

cur.execute('''CREATE TABLE users(
                 username VARCHAR(200),
                 password VARCHAR(200))''')

cur.execute('''CREATE TABLE forms(
                  title VARCHAR(200),
                  description VARCHAR(200),
                  formno INT,
                  question VARCHAR(200),
                  answertype VARCHAR(200),
                  options VARCHAR(200),
                  status VARCHAR(200),
                  quesno INT,
                  deadline DATE,
                  maxsub INT,
                  username VARCHAR(200))''')

cur.execute('''CREATE TABLE responses(
                  resno INT,
                  formno INT,
                  quesno INT,
                  question VARCHAR(200),
                  answertype VARCHAR(200),
                  answer VARCHAR(200),
                  username VARCHAR(200))''')


