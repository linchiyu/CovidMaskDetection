raspberry = False
if raspberry == True:
    import RPi.GPIO as gpio
else:
    None
import time
from threading import Thread
from queue import Queue
from settings import *

class CatracaManager():
    """docstring for SoundManager"""
    def __init__(self):
        self.controlPin = 23
        self.signalPin = 24
        gpio.setmode(gpio.BCM)
        gpio.setup(self.controlPin, gpio.OUT)
        gpio.setup(self.signalPin, gpio.IN, pull_up_down=gpio.PUD_UP)
        
        gpio.output(controlPin, gpio.HIGH)
        self.high = True #high = True == catraca travada
        self.controlQ = Queue() #true para liberar catraca, false para desligar programa

    def loopCatraca(self):
        while True:
            if gpio.input(self.signalPin): # button is released
                #recebe sinal da catraca, resetar controle para high
                self.setHigh()
            if self.high and not self.controlQ.empty():
                #se catraca travada e houver novo comando
                liberar = self.controlQ.get()
                if liberar:
                    self.setLow()
                    start = time.time()
                else:
                    gpio.cleanup()
                    break
            elif not self.high:
                if (time.time() - start) > CATRACA_TIME:
                    self.setHigh()

            time.sleep(0.1)

    def run(self):
        Thread(target=self.loopCatraca, args=(), daemon=True).start()

    def setHigh(self):
        #travar catraca
        gpio.output(self.controlPin, gpio.HIGH)
        self.high = True

    def setLow(self):
        #liberar catraca
        gpio.output(self.controlPin, gpio.LOW)
        self.high = False
