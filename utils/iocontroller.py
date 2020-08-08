import RPi.GPIO as GPIO
import time
from threading import Thread
from queue import Queue
from settings import *

class IoManager():
    """In Out Manager"""
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        #catraca - OUT
        #saída de sinal LOW libera a catraca
        self.catracaDireita = 23
        self.catracaEsquerda = 25
        GPIO.setup(self.catracaDireita, GPIO.OUT)
        GPIO.setup(self.catracaEsquerda, GPIO.OUT)
        #contagem catraca - IN
        #VERIFICAR REGRA DO SINAL
        self.contagemCatraca = 24
        GPIO.setup(self.temperatura, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        #GPIO.add_event_detect(self.contagemCatraca, GPIO.RISING, bouncetime=300)


        #temperatura - IN
        #entrada de sinal LOW significa ativacao do sensor de temperatura
        #1 LOW = temperatura normal
        #2 LOW seguidos = temperatura abaixo/acima
        self.temperatura = 26
        GPIO.setup(self.temperatura, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        #sensor de alcool gel
        #VERIFICAR REGRA DO SINAL
        self.sensorAlcool = 17
        self.alcoolVazio = 27
        GPIO.setup(self.sensorAlcool, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.alcoolVazio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        GPIO.output(self.controlPin, GPIO.HIGH)
        self.high = True #high = True == catraca travada
        #0 = sleep, 1 = temperatura, 2 = alcool
        self.mode = 1
        self.controlQ = Queue() #true para liberar catraca, false para desligar programa
        self.outputQ = Queue() #saída de informações de GPIO


    def setHigh(self, pin):
        #travar catraca
        GPIO.output(pin, GPIO.HIGH)

    def setLow(self, pin):
        #liberar catraca
        GPIO.output(pin, GPIO.LOW)

    def getPinValue(self, pin):
        return GPIO.input(pin)

    def avaliarTemperatura(self):
        while True:
            channel = GPIO.wait_for_edge(self.temperatura, GPIO.FALLING, timeout=TIME_TEMP * 1000)
            if channel == None:
                break
            channel = GPIO.wait_for_edge(self.temperatura, GPIO.FALLING, timeout=500)
            if channel == None:
                #temperatura emitiu 1 low, temperatura aceita
                self.outputQ.put('pass')
                self.mode = 0
                break
            else:
                #temperatura emitiu 2 low
                self.outputQ.put('stop')

    def avaliarAlcool(self):
        while True:
            channel = GPIO.wait_for_edge(self.temperatura, GPIO.FALLING, timeout=TIME_ALCOOL * 1000)
            if channel == None:
                break
            else:
                #sensor de alcool recebido
                self.outputQ.put('pass')
                self.mode = 0

    def liberarCatraca(self):
        ##############
        #adicionar logica de pessoa ja ter passado na catraca
        self.setLow(self.catracaDireita)
        self.setLow(self.catracaEsquerda)
        time.sleep(TIME_CATRACA)
        self.setHigh(self.catracaDireita)
        self.setHigh(self.catracaEsquerda)

    def loopGpio(self):
        while True:
            if self.mode == 1:
                self.avaliarTemperatura()
            elif self.mode == 2:
                self.avaliarAlcool()
            elif self.mode == 3:
                self.liberarCatraca()
            


            time.sleep(0.05)
        GPIO.cleanup()

    def run(self):
        Thread(target=self.loopCatraca, args=(), daemon=True).start()


