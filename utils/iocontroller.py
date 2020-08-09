import os
if 'nt' in os.name:
    pass
else:
    import RPi.GPIO as GPIO
import time
from threading import Thread
from queue import Queue
#from settings import *

class IoManager():
    """In Out Manager"""
    def __init__(self):
        #catraca - OUT
        #saída de sinal LOW libera a catraca
        self.catracaDireita = 23
        self.catracaEsquerda = 25
        #contagem catraca - IN
        #VERIFICAR REGRA DO SINAL
        self.contagemCatraca = 24
        #temperatura - IN
        #entrada de sinal LOW significa ativacao do sensor de temperatura
        #1 LOW = temperatura normal
        #2 LOW seguidos = temperatura abaixo/acima
        self.temperatura = 26
        #sensor de alcool gel
        #VERIFICAR REGRA DO SINAL
        self.sensorAlcool = 17
        self.alcoolVazio = 27

        if 'nt' in os.name: #windows
            self.has_GPIO = False
        else:
            self.has_GPIO = True
            GPIO.setstep(GPIO.BCM)
            
            GPIO.setup(self.catracaDireita, GPIO.OUT)
            GPIO.setup(self.catracaEsquerda, GPIO.OUT)
            
            GPIO.setup(self.contagemCatraca, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            #GPIO.add_event_detect(self.contagemCatraca, GPIO.RISING, bouncetime=300)

            GPIO.setup(self.temperatura, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            GPIO.setup(self.sensorAlcool, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.alcoolVazio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            GPIO.output(self.controlPin, GPIO.HIGH)
        #0 = sleep, 1 = temperatura, 3 = alcool, 5 = catraca
        self.step = 0
        self.stop = False
        #self.controlQ = Queue() #true para liberar catraca, false para desligar programa
        self.outputQ = Queue() #saída de informações de GPIO


    def setHigh(self, pin):
        #travar catraca
        if self.has_GPIO:
            GPIO.output(pin, GPIO.HIGH)
        else:
            print(pin, 'high')

    def setLow(self, pin):
        #liberar catraca
        if self.has_GPIO:
            GPIO.output(pin, GPIO.LOW)
        else:
            print(pin, 'low')

    def getPinValue(self, pin):
        if self.has_GPIO:
            return GPIO.input(pin)
        else:
            return 1

    def avaliarTemperatura(self):
        if self.has_GPIO:
            while True:
                channel = GPIO.wait_for_edge(self.temperatura, GPIO.FALLING, timeout=TIME_TEMP * 1000)
                if channel == None:
                    break
                channel = GPIO.wait_for_edge(self.temperatura, GPIO.FALLING, timeout=500)
                if channel == None:
                    #temperatura emitiu 1 low, temperatura aceita
                    self.outputQ.put('pass')
                    self.step = 0
                    break
                else:
                    #temperatura emitiu 2 low
                    self.outputQ.put('stop')
        else:
            print('avaliando temperatura GPIO')
            self.outputQ.put('pass')
            self.step = 0

    def avaliarAlcool(self):
        if self.has_GPIO:
            while True:
                channel = GPIO.wait_for_edge(self.sensorAlcool, GPIO.FALLING, timeout=TIME_ALCOOL * 1000)
                if channel == None:
                    break
                else:
                    #sensor de alcool recebido
                    self.outputQ.put('pass')
                    self.step = 0
        else:
            print('avaliando sensor alcool GPIO')
            self.outputQ.put('pass')
            self.step = 0

    def liberarCatraca(self):
        ##############
        #adicionar logica de pessoa ja ter passado na catraca
        self.setLow(self.catracaDireita)
        self.setLow(self.catracaEsquerda)
        time.sleep(0.3)
        self.setHigh(self.catracaDireita)
        self.setHigh(self.catracaEsquerda)
        self.step = 0
        if not self.has_GPIO:
            print('catraca liberada')

    def loopGpio(self):
        while True:
            if self.step == 1:
                self.avaliarTemperatura()
            elif self.step == 3:
                self.avaliarAlcool()
            elif self.step == 5:
                self.liberarCatraca()
            if self.stop:
                break
            time.sleep(0.1)
        if self.has_GPIO:
            GPIO.cleanup()

    def run(self):
        Thread(target=self.loopGpio, args=(), daemon=True).start()


if __name__ == '__main__':
    x = IoManager()
    x.run()
    x.step = 1
    time.sleep(5)
    x.step = 3
    time.sleep(5)
    x.step = 5
    time.sleep(5)