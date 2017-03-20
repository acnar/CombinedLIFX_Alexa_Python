import configparser
from copy import deepcopy
from lifxlan.lifxlan import *
from time import time
""""
 Class for managing LIFX devices.
"""
class LIFXManager:
    
    LIGHTS_DOWN = 0
    LIGHTS_RESTORED = 1
    LIGHTS_CHANGED = 2
    
    def __init__(self):
    
        config = configparser.ConfigParser()
        config.read("config")
        self.configs = config["LIFX_CONFIGS"]
        self.config = config["LIFX"]
            
        self.saved_groups = dict()
        self.lan = LifxLAN()
        
        # cached discovery
        self.ReadCache()
        
        # perform first new discovery
        self.lan.get_groups()
        self.ProcessConfigs()
        
        self.control_group = self.config["control_group"]
        
        self.active_config_num = self.config["active_config_num"]
        
        if int(self.active_config_num) >= len(self.configs):
            # override invalid config
            self.activeConfigNum = "0"
        
        if self.config["lights_on_at_start"] == "1":
            self.lights_start_on = True
            self.lan.set_group(self.control_group, (0,0,13107,3000), 65535, 0)
        else:
            self.lights_start_on = False
        
        #if len(self.lan.groups.keys()) == 0 or len(self.lan.groups[self.control_group]) == 0:
        #    # No configs found.  Store current state as saved state after first discovery.
        self.save_pending = True;
        #else:
        #    self.save_pending = False
        
        self.light_state = LIFXManager.LIGHTS_RESTORED
        self.previous_state = LIFXManager.LIGHTS_RESTORED
        
        self.last_print = ""
    
        if len(self.configs) == 0:
            print("Error, no configs found\n")
            exit(1)
    
    def ReadCache(self):
        groups = dict()
        group = []
        name = ""
        with open("cache") as cache:
            for line in cache:
                if "Group" in line:
                    if name != "" and len(group) > 0:
                        groups[name] = group
                    name = line.split(",")[1].strip()
                elif "Device" in line:
                    (device, mac_addr, label, hue, saturation, brightness, kelvin, power_level) = line.split(",")
                    light = Device(0,0,0,0,0)
                    light.label = name.strip()
                    light.color = (int(hue.strip()), int(saturation.strip()), int(brightness.strip()), int(kelvin.strip()))
                    light.power_level = int(power_level.strip())
                    light.mac_addr = mac_addr.strip()
                    light.discovered = False
                    light.discovery_time = time()
                    group.append(light)
            self.lan.groups = groups
            
    def WriteCache(self):
        cache = open("cache", "w")
        for group, lights in self.lan.groups.items():
            cache.write("Group, %s\n" % group)
            for light in lights:
                cache.write("Device, %s, %s, %i, %i, %i, %i, %i\n" % (light.mac_addr, light.label, light.color[0], light.color[1], light.color[2], light.color[3], light.power_level))
  
        cache.close()
        
    def ProcessConfigs(self):
        new_configs = dict()
        for key,value in self.configs.items():
            if "," in value:
                (name, hue, saturation, brightness, kelvin, power_level, fade_time, restore_time) = value.split(",")
                new_configs[key] = (name, (int(hue), int(saturation), int(brightness), int(kelvin)), int(power_level), int(fade_time), int(restore_time))
            else:
                new_configs[key] = value
        self.configs = new_configs
            
    def ListGroups(self):
    
        thisprint = ""
        for group in self.lan.groups:
            thisprint += "%s\n" % str(group)
       
        if thisprint != self.lastprint:
            print(thisprint)
            self.lastprint = thisprint
    
    def LightsRestore(self):
    
        saved_state = self.saved_groups[self.control_group]
        
        if self.active_config_num != 0:
            restore_time = self.configs[self.active_config_num][-1]
        else:
            restore_time = 0

        group = self.lan.groups[self.control_group]
        
        for device in group:
            (saved_color, saved_power) = saved_state[device.label]
            #print("restoring device %s to %s in %i ms" % (device.label, str(saved_color), restore_time))
            if saved_power != 0:
                # Turn on the power first
               device.set_power(saved_power, restore_time)
            device.set_hsbk(saved_color, restore_time)
            if saved_power != 0:
                # Turn off the power last
                device.set_power(saved_power, restore_time)
            
        self.light_state = LIFXManager.LIGHTS_RESTORED
    
    def LightsDown(self):
        
        success = True
        save = True
        (name, color, power_level, fade_time, restore_time) = self.configs[self.active_config_num]
                                
        if not self.lan.discovery_done(self.control_group):
            return False
        
        state = self.GetGroupState()
        saved_state = self.saved_groups[self.control_group]
        
        for device in self.lan.groups[self.control_group]:
            if self.light_state == LIFXManager.LIGHTS_CHANGED:
                if self.prev_light_state != LIGHTS_RESTORED:
                    compare_state = saved_state[device.label]
                    save = False
            else:
                compare_state = state[device.label]
                print(compare_state)
            
            if compare_state[1] != 0 or power_level != 0:
                if compare_state[1] >= power_level:
                    if compare_state[0][2] < color[2]:
                        color[2] = compare_state[0][2]
                    if power_level != 0:
                        # Turn on the power first
                        device.set_power(power_level, fade_time)
                    device.set_hsbk(color, fade_time)
                    if power_level == 0:
                        # Turn off power last
                        device.set_power(power_level, fade_time)
                    #if not device.set_hsbk(color, power_level, fade_time):
                    #    save = False
					
        if save:
            print("save")
            self.SaveGroup(fade_time, state)
            self.previous_state = self.light_state
            self.light_state = LIFXManager.LIGHTS_DOWN
        
    def GetGroupState(self):
    
        group = self.lan.groups[self.control_group]
        
        state = dict()
        
        for device in group:
            #print("color =")
            #print(device.color)
            name = deepcopy(device.label)
            color = deepcopy(device.color)
            power = deepcopy(device.power_level)
            state[name] = (color, power)
            
            #print(color)
            
        
        
        return state
        
            
    def SaveGroup(self, delay = 0, state = None):
        save = False
        if not state:
            state = self.GetGroupState()
        
        if self.control_group in self.saved_groups:
            saved_state = self.saved_groups[self.control_group]
            if "time" in saved_state:
                if saved_state["time"] < time():
                    state["time"] = time() + delay
                    save = True
        else:
            save = True
            
        if save:
            self.saved_groups[self.control_group] = state
        
        
    def Discover(self):
        #print("discovering\n")
        try:
            self.lan.get_groups()
        except Exception as e:
            pass
            #print ("Exception during discovery: %s\n", e)
            
        #print("done\n")
        if self.save_pending:
            if self.lan.discovery_done(self.control_group):
                self.SaveGroup()
                self.save_pending = False