import mysql.connector
import datetime
import csv
import os
import threading
from settings import *

HOST = 'localhost'
USER = 'root'
PASSWORD = 'articfox'
DATABASE = 'uppcare01'


def criarBanco():
    mydb = mysql.connector.connect(
      host=HOST,
      user=USER,
      password=PASSWORD
    )
    mycursor = mydb.cursor()
    mycursor.execute("CREATE DATABASE uppcare01")
    mydb.close()

def criarTabela():
    mydb = mysql.connector.connect(
      host=HOST,
      user=USER,
      password=PASSWORD,
      database=DATABASE
    )
    mycursor = mydb.cursor()
    mycursor.execute("CREATE TABLE registro (id INT AUTO_INCREMENT PRIMARY KEY, datahora DATETIME NOT NULL, temperatura VARCHAR(30) NOT NULL, mascara VARCHAR(30) NOT NULL)")
    mydb.close()
    
def resetarTabela():
    mydb = mysql.connector.connect(
      host=HOST,
      user=USER,
      password=PASSWORD,
      database=DATABASE
    )
    mycursor = mydb.cursor()
    mycursor.execute("DROP TABLE registro")
    mydb.close()
    criarTabela()

class DBManager():
    def __init__(self):
        if not BANCO_ATIVO:
            return
        self.mydb = mysql.connector.connect(
          host=HOST,
          user=USER,
          password=PASSWORD,
          database=DATABASE
        )
        self.path = "/home/pi/temp/"
        try:
            os.system("mkdir " + self.path)
        except:
            None

    def inserirRegistro(self, data=datetime.datetime.now(), temperatura="normal", mascara="sim"):
        if not BANCO_ATIVO:
            return
        mycursor = self.mydb.cursor()
        sql = "INSERT INTO registro (datahora, temperatura, mascara) VALUES (%s, %s, %s)"
        val = (str(data), str(temperatura), str(mascara))
        mycursor.execute(sql, val)
        self.mydb.commit()

    def receberRegistros(self):
        if not BANCO_ATIVO:
            return []
        mycursor = self.mydb.cursor()

        start_date = datetime.datetime.now() - datetime.timedelta(32)

        sql = "SELECT * FROM registro WHERE datahora >= %s"
        val = (str(start_date),)

        mycursor.execute(sql, val)

        myresult = mycursor.fetchall()
        return myresult

    def registros2Csv(self, registros):
        with open(self.path+"registros.csv", 'w', newline='') as myfile:
            header = ('id', 'data', 'temperatura', 'mascara')
            wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
            wr.writerow(header)
            wr.writerows(registros)

    def threadInserir(self, data=datetime.datetime.now(), temperatura="normal", mascara="sim"):
        t = threading.Thread(target=self.inserirRegistro, args=(data, temperatura, mascara,))
        t.daemon = True
        t.start()
        
    def stop(self):
        if not BANCO_ATIVO:
            return
        self.mydb.close()


if __name__ == '__main__':
    #b = DBManager()
    #b.inserirRegistro(datetime.datetime(year=2021, month=3, day=5))
    #x = b.receberRegistros()
    #registros2Csv(x)
    #print(b.receberRegistros())
    #criarBanco()
    #criarTabela()
    resetarTabela()
    #b.stop()
    
    
    '''Log in to MySQL: sudo mysql --user=root

Delete the root user: DROP USER 'root'@'localhost'; Create a new user: CREATE USER 'root'@'localhost' IDENTIFIED BY 'password'; Give the user all permissions: GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost' WITH GRANT OPTION;


DROP USER 'root'@'localhost';
CREATE USER 'root'@'localhost' IDENTIFIED BY 'articfox';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost' WITH GRANT OPTION;

'''