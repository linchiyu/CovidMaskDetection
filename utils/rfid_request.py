'''def verificarUsuario(numero, listaRfid):
	try:
		numero = int(numero)
	except:
		return -1
	for idx, codigoRfid in enumerate(listaRfid):
		try:
			if int(codigoRfid) == numero:
				print('usr', idx, codigoRfid)
				return idx
		except:
			None
	return -2'''

def verificarUsuario(numero, listaP):
	try:
		numero = int(numero)
	except:
		return {}
	for pessoa in listaP:
		try:
			if numero == int(pessoa.get('codigo', 0)):
				#print('usr', pessoa)
				return pessoa
		except:
			return {}
	return {}

