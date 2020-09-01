USUARIO = [{
  "numero": 6042777,
  "nome": "Nome",
  "empresa": "Portal"
},
{
  "numero": 1762425,
  "nome": "Nome",
  "empresa": "Sissi"
},
{
  "numero": 8004586,
  "nome": "Marcelo",
  "empresa": "Lave Bem"
},
{
  "numero": 8834861,
  "nome": "Amanda",
  "empresa": "leads"
},
{
  "numero": 8834856,
  "nome": "Amanda",
  "empresa": "leads"
},
{
  "numero": 6117435,
  "nome": "Jociane",
  "empresa": "Master Shopping"
}]

def verificarUsuario(numero, listaRfid):
	try:
		numero = int(numero)
	except:
		return -1
	for idx, codigoRfid in enumerate(listaRfid):
		if int(codigoRfid) == numero:
			print('usr', idx, codigoRfid)
			return idx
	return -1

