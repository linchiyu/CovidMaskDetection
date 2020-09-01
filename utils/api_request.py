import numpy as np
import json, requests
from datetime import datetime
#from settings import URL, USUARIO, SENHA
from threading import Thread
URL = 'http://localhost:8000'
USUARIO = 'teste'
SENHA = 'testeteste'


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

	def registrarUsuario(self):
		dados = {"username": self.user, "password1": self.password, "password2": self.password}
		response = requests.post(URL+"/auth/registration/", data=dados)

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
				print("Servidor não conectado")
				return False
		except:
			print("Servidor não conectado")
		return False

	def getFaceList(self):
		idPessoa = []
		nome = []
		codigo = []
		face_points = []
		try:
			response = requests.get(URL+"/api/pessoa/facelist", cookies=self.cookies)
			if response.status_code == 200:
				print("Obtendo lista de usuarios")
				data = json.loads(response.content)
				for d in data:
					try:
						d['face_encoded'] = getFaceArray(d['face_encoded'])
						if len(d['face_encoded']) > 10:
							idPessoa.append(d['id'])
							nome.append(d['nome'])
							codigo.append(d['codigo'])
							face_points.append(d['face_encoded'])
					except:
						None
				#print(idPessoa, nome, face_points)
		except:
			print("Erro na conexão com servidor")
			pass
		return idPessoa, nome, codigo, face_points

	def createAcesso(self, idPessoa=1, datahora=str(datetime.now()), tipo="entrada"):
		success = False
		data = {"data": datahora, "tipoAcesso": tipo, "fkpessoa": idPessoa}
		while not success:
			try:
				response = requests.post(URL+"/api/acesso/new", data=data, cookies=self.cookies)
				if response.status_code == 201:
					data = json.loads(response.content)
					success = True
				else:
					success = False
			except:
				print("Erro na conexão com servidor")
				pass

	def loopCreateAcesso(self, idPessoa=1, datahora=str(datetime.now()), tipo="entrada"):
		Thread(target=self.createAcesso,args=(idPessoa, datahora, tipo,),daemon=True).start()

if __name__ == '__main__':
	x = API()
	print(x.getFaceList())
	