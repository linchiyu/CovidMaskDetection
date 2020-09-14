def verificarUsuario(numero, listaRfid):
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
	return -2

