import mysql.connector
import datetime
import csv
import os
import threading

HOST = 'localhost'
USER = 'root'
PASSWORD = ''
DATABASE = 'uppcare01'

def criarBanco():
    mydb = mysql.connector.connect(
      host=HOST,
      user=USER,
      password=PASSWORD
    )
    mycursor = mydb.cursor()
    mycursor.execute("CREATE DATABASE uppcare01")

def criarTabela():
    mydb = mysql.connector.connect(
      host=HOST,
      user=USER,
      password=PASSWORD,
      database=DATABASE
    )
    mycursor = mydb.cursor()
    mycursor.execute("CREATE TABLE registro (id INT AUTO_INCREMENT PRIMARY KEY, datahora DATETIME NOT NULL, temperatura VARCHAR(30) NOT NULL, mascara VARCHAR(30) NOT NULL)")

class DBManager():
    def __init__(self):
        self.mydb = mysql.connector.connect(
          host=HOST,
          user=USER,
          password=PASSWORD,
          database=DATABASE
        )
        self.path = "/home/pi/temp/"
        try:
            os.system("sudo mkdir " + path)
        except:
            None

    def inserirRegistro(self, data=datetime.datetime.now(), temperatura="normal", mascara="sim"):
        mycursor = self.mydb.cursor()
        sql = "INSERT INTO registro (datahora, temperatura, mascara) VALUES (%s, %s, %s)"
        val = (str(data), str(temperatura), str(mascara))
        mycursor.execute(sql, val)
        self.mydb.commit()

    def receberRegistros(self):
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


if __name__ == '__main__':
    b = DBManager()
    b.inserirRegistro(datetime.datetime(year=2021, month=3, day=5))
    #x = b.receberRegistros()
    #registros2Csv(x)
    print(b.receberRegistros())