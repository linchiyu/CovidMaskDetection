import os
import threading
import time
import shutil
import settings
if not BANCO_ATIVO:
    from utils import banco
if 'nt' in os.name:
    pass
else:
    import pyudev

#https://vivekanandxyz.wordpress.com/2018/01/03/detecting-usb-insertion-removal-using-python/

def copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

            
class USBDetector():
    ''' Monitor udev for detection of usb '''
 
    def __init__(self):
        ''' Initiate the object '''
        self.path = "/home/pi/mountusbdevice"
        self.propagandaspath = os.getcwd()+"/propaganda"

        if 'nt' in os.name:
            print('iniciando usb detector')
        else:
            thread = threading.Thread(target=self._work)
            thread.daemon = True
            thread.start()
            try:
                os.system("mkdir " + self.path)
            except:
                None
        self.lastUpdated = 0


        if not BANCO_ATIVO:
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

        if not BANCO_ATIVO:
            self.dbm.registros2Csv(self.dbm.receberRegistros())

        tempfolder = os.getcwd()+"/propaganda_new"

        try:
            os.makedirs(path)
        except:
            None

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

                if not BANCO_ATIVO:
                    os.system("sudo cp "+ self.dbm.path + "registros.csv " + path + "/registros.csv")

                if os.path.exists(path+"/propaganda"):
                    try:
                        shutil.rmtree(tempfolder)
                    except:
                        None

                    copytree(path+"/propaganda", tempfolder)

                    try:
                        shutil.rmtree(self.propagandaspath)
                    except:
                        None

                    os.rename(tempfolder, self.propagandaspath)
                    #commit

                #commit

                #unmount device
                time.sleep(5)
                os.system("sudo umount -l " + path)
                print('done copying')
                time.sleep(5)
                os.system("sudo eject " + p)
                self.lastUpdated = time.time()
            os.system("sudo eject " + str(device.device_node))
            time.sleep(1)
            #os.system("sudo udisksctl power-off -b " + str(device.device_node))
        pass

    def on_removal(self):
        self.lastUpdated = 0


if __name__ == '__main__':
    usb = USBDetector()
    time.sleep(60)
    pass
