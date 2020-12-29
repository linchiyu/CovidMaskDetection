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

        self.updateToken()

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
            response = requests.get(URL+"/api/pessoa/facelist", cookies=self.cookies)
            if response.status_code == 200:
                print("Obtendo lista de usuarios")
                data = json.loads(response.content)
                for d in data:
                    if d.get('ativo') and d.get('foto_valida'):
                        d['face_encoded'] = getFaceArray(d.get('face_encoded'))
                        pessoa_list.append(d)
                        face_list.append(d.get('face_encoded'))
        except:
            print("Erro na conexão com servidor")
        return pessoa_list, face_list

    def createAcesso(self, idPessoa=1, datahora=str(datetime.now()), tipo="entrada"):
        data = {"data": datahora, "tipoAcesso": tipo, "fkpessoa": idPessoa}
        erro = 0
        while erro < 5:
            try:
                self.updateToken()
                response = requests.post(URL+"/api/acesso/new", data=data, cookies=self.cookies)
                if response.status_code == 201:
                    data = json.loads(response.content)
                    break
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
    USUARIO = 'teste1'
    SENHA = 'testeteste'
    x = API()
    x.createAcesso(1)