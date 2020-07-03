#!/bin/sh
servico(){
	cd /home/pi/Documents/
	sleep 10

	cd CovidMaskDetection/
	echo "Iniciando detector..."
	/usr/bin/python3 main.py

}

echo Iniciando Servico

servico

echo Finalizando Servico


#x-terminal-emulator --title="Servico" --command="bash -c 'echo ldxpi; cd /home/$
#@/home/pi/Desktop/inicializador.sh &

#@lxterminal -e bash -c '/home/pi/Desktop/inicializador.sh; bash' &

#@/home/pi/inicializador.sh &
#inserir chamada desse arquivo em /home/pi/.config/lxsession/LXDE-pi/autostart

