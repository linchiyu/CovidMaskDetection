#downloaded from https://ttsmp3.com/
from time import sleep
from threading import Thread
from queue import Queue
#from multiprocessing import Process, Queue

class SoundManager():
    """docstring for SoundManager"""
    def __init__(self, path='data/sound/'):
        self.path = path
        self.soundQ = Queue()

    def run(self):
        Thread(target=self.playSound, args=(), daemon=True).start()
        
    def playSound(self):
        import pygame
        pygame.mixer.init()
        while True:
            if pygame.mixer.music.get_busy() == True:
                continue
            if not self.soundQ.empty():
                tipo = self.soundQ.get()
                if tipo == 'pass':
                    pygame.mixer.music.load(self.path+'pass.mp3')
                    pygame.mixer.music.play()
                elif tipo == 'stop':
                    pygame.mixer.music.load(self.path+'stop.mp3')
                    pygame.mixer.music.play()
                elif tipo == 'temperatura':
                    pygame.mixer.music.load(self.path+'temperatura.mp3')
                    pygame.mixer.music.play()
                elif tipo == 'mascara':
                    pygame.mixer.music.load(self.path+'mascara.mp3')
                    pygame.mixer.music.play()
                elif tipo == 'alcool':
                    pygame.mixer.music.load(self.path+'alcool.mp3')
                    pygame.mixer.music.play()
                elif tipo == 'cartao':
                    pygame.mixer.music.load(self.path+'cartao.mp3')
                    pygame.mixer.music.play()
                elif tipo == 'catraca':
                    pygame.mixer.music.load(self.path+'catraca.mp3')
                    pygame.mixer.music.play()
                elif tipo == 'bemvindo':
                    pygame.mixer.music.load(self.path+'bemvindo.mp3')
                    pygame.mixer.music.play()
                elif tipo == 'block':
                    pygame.mixer.music.load(self.path+'block.mp3')
                    pygame.mixer.music.play()
                elif tipo == 'wait':
                    None
                else:
                    break
            sleep(0.05)

    def stop(self):
        self.soundQ.put('False')

if __name__ == '__main__':
    s = SoundManager(path='./../data/sound/')
    s.run()
    s.soundQ.put('pass')
    s.soundQ.put('stop')
    s.soundQ.put('stop')
    s.soundQ.put('stop')
    sleep(15)
