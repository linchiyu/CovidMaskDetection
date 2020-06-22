from time import sleep
import playsound
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
        while True:
            if not self.soundQ.empty():
                tipo = self.soundQ.get()
                if tipo == 'pass':
                    playsound.playsound(self.path+'pass.mp3')
                elif tipo == 'stop':
                    playsound.playsound(self.path+'stop.mp3')
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
    sleep(5)
