import numpy as np
import json, requests
from datetime import datetime
from settings import URL, USUARIO, SENHA
from threading import Thread

def getFaceArray(encodedNumpyData):
    #converte o json em array numpy
    # Deserialization
    #print("Decode JSON serialized NumPy array")
    decodedArrays = json.loads(encodedNumpyData)

    finalNumpyArray = np.asarray(decodedArrays["face"])
    #print("NumPy Array")
    #print(finalNumpyArray)
    return finalNumpyArray

class API():
    """API conexão com servidor"""
    def __init__(self):
        self.user = USUARIO
        self.password = SENHA

        self.token = None

        self.cookies = {'auth': self.token}

        #self.updateToken()

    def registrarUsuario(self, usuario, senha):
        try:
            dados = {"username": usuario, "password1": senha, "password2": senha}
            response = requests.post(URL+"/auth/registration/", data=dados)
        except:
            None

    def updateToken(self):
        try:
            dados = {"username": self.user, "password": self.password}
            response = requests.post(URL+"/auth/login/", data=dados)
            if response.status_code == 200:
                self.token = json.loads(response.content)['access_token']
                self.cookies = {'auth': self.token}
                print("Token gerado com sucesso")
                return True
            else:
                print("Dados de acesso incorretos")
                return False
        except:
            print("Servidor não conectado")
        return False

    def getFaceList(self):
        pessoa_list = []
        face_list = []
        try:
            self.updateToken()
            response = requests.get(URL+"/api/pessoa/facelist?limit=100000", cookies=self.cookies)
            if response.status_code == 200:
                print("Obtendo lista de usuarios")
                data = json.loads(response.content)
                for d in data.get('results',[]):
                    d['face_encoded'] = getFaceArray(d.get('face_encoded'))
                    face_list.append(d.get('face_encoded', []))
                pessoa_list = data.get('results',[])
        except:
            print("Erro na conexão com servidor")
        return pessoa_list, face_list

    def getProcessList(self):
        pessoa_list = []
        try:
            self.updateToken()
            response = requests.get(URL+"/api/pessoa/process?limit=100000", cookies=self.cookies)
            if response.status_code == 200:
                print("Obtendo lista de usuarios")
                data = json.loads(response.content)
                pessoa_list = data.get('results',[])
        except:
            print("Erro na conexão com servidor")
        return pessoa_list

    def updateProcessedFace(self, idp, encoded, foto_valida):
        data = {"face_encoded": str(encoded), "foto_valida": foto_valida}
        try:
            self.updateToken()
            response = requests.put(URL+"/api/pessoa/process/"+str(idp), data=data, cookies=self.cookies)
            if response.status_code == 200:
                print('sucesso atualizada face '+str(idp))
            else:
                print('erro atualização face')
        except:
            print("Erro na conexão com servidor")

    def createAcesso(self, idPessoa=1, datahora=str(datetime.now()), tipo="entrada"):
        data = {"data": datahora, "tipoAcesso": tipo, "fkPessoa": idPessoa}
        erro = 0
        while erro < 5:
            try:
                self.updateToken()
                response = requests.post(URL+"/api/acesso/new", data=data, cookies=self.cookies)
                if response.status_code == 201:
                    data = json.loads(response.content)
                    break
                else:
                    #print('erro')
                    pass
                erro += 1
            except:
                print("Erro na conexão com servidor")
                erro += 1

    def threadCreateAcesso(self, idPessoa=-1, datahora=str(datetime.now()), tipo="entrada"):
        Thread(target=self.createAcesso,args=(idPessoa, datahora, tipo,),daemon=True).start()

if __name__ == '__main__':
    import time
    global URL, USUARIO, SENHA
    URL = 'http://localhost'
    URL = 'http://localhost:8000'

    USUARIO = 'api_client'
    SENHA = 'api_client_secret_key2020'
    USUARIO = 'chiyu'
    SENHA = 'p87419702'
    x = API()
    print(x.getProcessList())