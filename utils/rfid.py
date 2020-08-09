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

def verificarUsuario(numero):
	try:
		numero = int(numero)
	except:
		return None
	for usr in USUARIO:
		if usr['numero'] == numero:
			#print(usr)
			return usr
	return None

