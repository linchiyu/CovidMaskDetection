import os
import threading
import time
from utils import banco
if 'nt' in os.name:
    pass
else:
    import pyudev

class USBDetector():
    ''' Monitor udev for detection of usb '''
 
    def __init__(self):
        ''' Initiate the object '''
        self.path = "/home/pi/mountusbdevice"
        if 'nt' in os.name:
            print('iniciando usb detector')
        else:
            thread = threading.Thread(target=self._work)
            thread.daemon = True
            thread.start()
            try:
                os.system("sudo mkdir " + path)
            except:
                None
        self.lastUpdated = 0
        self.dbm = banco.DBManager()
 
    def _work(self):
        ''' Runs the actual loop to detect the events '''
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='usb')
        # this is module level logger, can be ignored
        #LOGGER.info("Starting to monitor for usb")
        self.monitor.start()
        for device in iter(self.monitor.poll, None):
            #LOGGER.info("Got USB event: %s", device.action)
            if device.action == 'add':
                # some function to run on insertion of usb
                self.on_insertion()
            else:
                # some function to run on removal of usb
                self.on_removal()

    def on_insertion(self):
        if time.time() - self.lastUpdated < 10:
            return
        #print('insertion') 
        path = self.path
        #generate csv data
        self.dbm.registros2Csv(self.dbm.receberRegistros())

        #find device(s)
        time.sleep(5)
        removable = [device for device in self.context.list_devices(subsystem='block', DEVTYPE='disk') if device.attributes.asstring('removable') == "1"]
        for device in removable:
            partitions = [device.device_node for device in self.context.list_devices(subsystem='block', DEVTYPE='partition', parent=device)]
            #print("All removable partitions: {}".format(", ".join(partitions)))
            for p in partitions:
                #mount the device
                #print('mount '+p)
                os.system("sudo mount " + p + " " + path) 
                #save csv on device

                #os.system("sudo cp /home/pi/inicializador.sh "+path+"/inic.sh")
                os.system("sudo cp "+ self.dbm.path + "registros.csv " + path + "/registros.csv")

                #commit

                #unmount device
                time.sleep(5)
                os.system("sudo umount -l " + path)
                print('done copying')
                time.sleep(5)
                self.lastUpdated = time.time()
        pass

    def on_removal(self):
        self.lastUpdated = 0


if __name__ == '__main__':
    usb = USBDetector()
    time.sleep(60)
    pass