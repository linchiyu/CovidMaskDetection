from time import sleep
import pygame
from multiprocessing import Process, Queue

class SoundManager():
    """docstring for SoundManager"""
    def __init__(self, path='data/sound/'):
        self.path = path
        self.soundQ = Queue()
        self.p = None

    def run(self):
        self.p = Process(target=self.playSound, args=(), daemon=True).start()
        
    def playSound(self):
        pygame.mixer.init()
        while True:
            if not self.soundQ.empty():
                tipo = self.soundQ.get()
                if tipo == 'pass':
                    pygame.mixer.music.load(self.path+'pass.mp3')
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy() == True:
                        continue
                elif tipo == 'stop':
                    pygame.mixer.music.load(self.path+'stop.mp3')
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy() == True:
                        continue
                else:
                    break
            sleep(0.05)

if __name__ == '__main__':
    s = SoundManager(path='./../data/sound/')
    s.run()
    s.soundQ.put('pass')
    s.soundQ.put('stop')
    s.soundQ.put('stop')
    s.soundQ.put('stop')
    sleep(15)
