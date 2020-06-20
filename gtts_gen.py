from gtts import gTTS
import os
 
#em text, informe o texto a ser dito. Evite usar acentuacao.
AudioDoTexto = gTTS(text='Obrigado por utilizar mascara!', lang='pt')  #pt eh o codigo de idioma correspondente ao Portugues. 
                                                                   #Aqui pode ser utilizado qualquer um dos codigos de idioma citados anteriormente neste post.
AudioDoTexto.save("audio.mp3")