
class Group:

    def __init__(self, n = ""):
        if n == "":
            self.name = "Unnamed Group"
        else:
            self.name = n
            
        self.devices = dict()
        
    def addDevice(self, address):
        devName = self.getDevice(address)
        
        if devName == "":
            self.devices[str(address)] = LIFXDevice(address)
    
    def getDevice(self, addr):
        devName = ""
        for dev in self.devices:
            if dev.address() == addr:
                devname = device.name
                break
    
        return devname

    def containsDevice(self, addr):
        deviceKey = str(addr)
        
        return deviceKey in self.devices
    
    def setDeviceAttributes(self, target, label, hue, saturation ,brightness, kelvin, power, last_discovered, discovered):
        d = self.devices[str(target)]
        d.setAttributes(label, hue, saturation, brightness, kelvin, power, last_discovered, discovered)
    
    """ todo - figure out how to delet from iterator
    void PurgeOldDevices(unsigned currentTime)
    {
        std::map<std::string, LIFXDevice*>::iterator itr = devices.begin();
        while (itr != devices.end()) {
            if (itr->second->Expired(currentTime)) {
               itr = devices.erase(itr);
            } else {
               ++itr;
            }
        }
    }
    
    void RemoveDevice(const MacAddress& address)
    {
        std::map<std::string, LIFXDevice*>::iterator itr = devices.begin();
        while (itr != devices.end()) {
            if (itr->second->Address() == address) {
               itr = devices.erase(itr);
            } else {
               ++itr;
            }
        }
    }
    """
    
    def refreshTimestamps(self, time):
        for dev in self.devices():
            dev.timestamp = time;

    def addDevice(self, device):
        label = str(device.addr)
        
        if label in self.devices:
            self.devices[label] = device
    
    def discoveryDone(self):
        done = True
        if not self.devices:
            for dev in self.devices:
                if dev.discovered == False:
                    done = False
                    break
        else:
            done = False
        
        return done
    
    def hasGlobalSetting(state):
        has = True
        for dev in self.devices:
            if dev.state != state:
                has = False
                break
        return has
        
    """ todo - figure out override for <<
    def __str__(self):
        str = ""
    std::string ToString() const {
        std::stringstream ret;
        ret << "\nGroup: " << name << "\n";
        ret << "===============================\n";
        for(const auto& it : devices)
        {
            ret << "Device: " << it.second->ToString() << "\n\n";
        }
        return ret.str();
    }"""