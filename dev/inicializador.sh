#!/bin/sh
servico(){
	cd /home/pi/Documents/CovidMaskDetection/
	/usr/bin/python3 first_run.py
	cd /home/pi/Documents/CovidMaskDetection-v2/
	/usr/bin/python3 first_run.py
	
	sleep 10
	cd /home/pi/Documents/
	echo "Iniciando detector..."
	cd CovidMaskDetection/
	/usr/bin/python3 main.py

}

echo Iniciando Servico
export LD_PRELOAD="/usr/lib/libtcmalloc_minimal.so.4"

servico

echo Finalizando Servico


#x-terminal-emulator --title="Servico" --command="bash -c 'echo ldxpi; cd /home/$
#@/home/pi/Desktop/inicializador.sh &

#@lxterminal -e bash -c '/home/pi/Desktop/inicializador.sh; bash' &

#@/home/pi/inicializador.sh &
#inserir chamada desse arquivo em /home/pi/.config/lxsession/LXDE-pi/autostart

