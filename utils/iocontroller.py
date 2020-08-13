import os
if 'nt' in os.name:
    pass
else:
    import RPi.GPIO as GPIO
import time
from threading import Thread
from queue import Queue
from settings import *

class IoManager():
    """In Out Manager"""
    def __init__(self):
        #catraca - OUT
        #saída de sinal LOW libera a catraca
        self.catracaDireita = 18
        self.catracaEsquerda = 25
        #contagem catraca - IN
        #VERIFICAR REGRA DO SINAL
        #self.contagemCatraca = 24
        self.sensorEsqCat = 5
        self.sensorDirCat = 6

        self.sensorEsqCat2 = 23
        self.sensorDirCat2 = 24

        #numero de pessoas dentro da loja
        self.contagem = 0

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
            GPIO.setmode(GPIO.BCM)
            
            GPIO.setup(self.catracaDireita, GPIO.OUT)
            GPIO.setup(self.catracaEsquerda, GPIO.OUT)

            GPIO.setup(self.sensorEsqCat, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.sensorDirCat, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            #GPIO.setup(self.contagemCatraca, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.sensorEsqCat2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.sensorDirCat2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            #GPIO.add_event_detect(self.contagemCatraca, GPIO.RISING, bouncetime=300)

            GPIO.setup(self.temperatura, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            #GPIO.add_event_detect(self.temperatura, GPIO.RISING, callback=self.tempSignal)

            GPIO.setup(self.sensorAlcool, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.alcoolVazio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(self.sensorAlcool, GPIO.FALLING, callback=self.alcoolSignal)
            
            GPIO.output(self.catracaDireita, GPIO.HIGH)
            GPIO.output(self.catracaEsquerda, GPIO.HIGH)
        #0 = sleep, 1 = temperatura, 3 = alcool, 5 = catraca
        self.step = 0
        self.tempTimer = []
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
            x = GPIO.wait_for_edge(self.temperatura, GPIO.RISING, timeout=TIME_TEMP*1000)
            if x == None:
                pass
            else:
                x = GPIO.wait_for_edge(self.temperatura, GPIO.FALLING, timeout=300)
                if x == None:
                    self.outputQ.put('pass')
                    print('pass')
                    self.step = 0
                else:
                    GPIO.wait_for_edge(self.temperatura, GPIO.RISING, timeout=500)
                    self.outputQ.put('stop')
                    print('stop')
        else:
            print('avaliando temperatura GPIO')
            self.outputQ.put('pass')
            self.step = 0

    def alcoolSignal(self, channel):
        if self.step == 3:
            self.outputQ.put('pass')
            self.step = 0
        
    def avaliarAlcool(self):
        if self.has_GPIO:
            pass
        else:
            print('avaliando sensor alcool GPIO')
            self.outputQ.put('pass')
            self.step = 0

    def liberarCatraca(self):
        ##############
        if self.contagem >= CAPACIDADE_PESSOAS:
            #capacidade máxima de pessoas atingida
            self.outputQ.put('stop')
            print('stop')
        #adicionar logica de pessoa ja ter passado na catraca
        if self.has_GPIO:
            time.sleep(1)
            self.setLow(self.catracaDireita)
            self.setLow(self.catracaEsquerda)
            time.sleep(1)
            self.setHigh(self.catracaDireita)
            self.setHigh(self.catracaEsquerda)
            x = GPIO.wait_for_edge(self.sensorEsqCat, GPIO.FALLING, timeout=5000)
            if x == None:
                pass
            else:
                x = GPIO.wait_for_edge(self.sensorDirCat, GPIO.FALLING, timeout=1000)
                if x == None:
                    pass
                else:
                    self.contagem = self.contagem + 1
                    print('passagem registrada' + self.contagem)
            self.step = 0
        else:
            print('catraca liberada')

    def passagemCatraca(self):
        ##############
        #adicionar logica de pessoa ja ter passado na catraca
        if self.has_GPIO:
            time.sleep(1)
            self.setLow(self.catracaDireita)
            self.setLow(self.catracaEsquerda)
            time.sleep(1)
            self.setHigh(self.catracaDireita)
            self.setHigh(self.catracaEsquerda)
            self.step = 0
        else:
            print('catraca liberada')

    def loopGpio(self):
        while True:
            if self.step == 1:
                self.avaliarTemperatura()
                '''elif self.step == 3:
                self.avaliarAlcool()
                pass'''
                '''elif self.step == 5:
                self.liberarCatraca()'''
            else:
                time.sleep(0.1)
            if self.stop:
                break
        if self.has_GPIO:
            GPIO.cleanup()

    def run(self):
        Thread(target=self.loopGpio, args=(), daemon=True).start()
        
    def liberar(self):
        Thread(target=self.liberarCatraca, args=(), daemon=True).start()


if __name__ == '__main__':
    x = IoManager()
    x.run()
    x.step = 1
    time.sleep(10)
    x.stop = True
