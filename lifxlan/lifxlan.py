# lifxlan.py

from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST, timeout
from .message import BROADCAST_MAC, BROADCAST_SOURCE_ID
from .device import Device, UDP_BROADCAST_IP, UDP_BROADCAST_PORT, DEFAULT_TIMEOUT, DEFAULT_ATTEMPTS
from .light import *
from .multizonelight import *
from .msgtypes import *
from .unpack import unpack_lifx_message
from random import randint
from time import time, sleep
from .errors import WorkflowException, InvalidParameterException

class LifxLAN:
    def __init__(self, num_lights=None, verbose=False):
        self.source_id = randint(0, (2**32)-1)
        self.num_devices = num_lights
        self.num_lights = num_lights
        self.devices = None
        self.lights = None
        self.verbose = verbose
        self.groups = dict()

    ############################################################################
    #                                                                          #
    #                         LAN (Broadcast) API Methods                      #
    #                                                                          #
    ############################################################################

    # This is shuttered until it becomes clear how to distinguish between Lights and non-Light Devices
    # def get_devices(self):
    #   if self.num_devices == None:
    #       responses = self.discover()
    #   else:
    #       responses = self.broadcast_with_resp(GetService, StateService)
    #   for r in responses:
    #       mac = r.target_addr
    #       service = r.service
    #       port = r.port
    #       self.devices.append(Device(mac, service, port, self.source_id, self.verbose))
    #   self.num_devices = len(self.devices)
    #   return self.devices

    def get_lights(self):
        if self.lights == None:
            self.lights = []
            self.devices = []
            if self.num_lights == None:
                responses = self.discover()
            else:
                try:
                    responses = self.broadcast_with_resp(GetService, StateService)
                except WorkflowException as e:
                    raise
                    #return None
            for r in responses:
                device = Device(r.target_addr, r.ip_addr, r.service, r.port, self.source_id, self.verbose)
                if device.supports_multizone():
                    device = MultiZoneLight(r.target_addr, r.ip_addr, r.service, r.port, self.source_id, self.verbose)
                else:
                    device = Light(r.target_addr, r.ip_addr, r.service, r.port, self.source_id, self.verbose)
                self.lights.append(device)
                self.devices.append(device)
            self.num_lights = len(self.lights)
            self.num_devices = len(self.lights)
        return self.lights

    def get_multizone_lights(self):
        multizone_lights = []
        all_lights = self.get_lights()
        for l in all_lights:
            if l.supports_multizone():
                multizone_lights.append(l)
        return multizone_lights

    def get_infrared_lights(self):
        infrared_lights = []
        all_lights = self.get_lights()
        for l in all_lights:
            if l.supports_infrared():
                infrared_lights.append(l)
        return infrared_lights

    def get_color_lights(self):
        color_lights = []
        all_lights = self.get_lights()
        for l in all_lights:
            if l.supports_color():
                color_lights.append(l)
        return color_lights

    # returns dict of Light: power_level pairs
    def get_power_all_lights(self):
        responses = self.broadcast_with_resp(LightGetPower, LightStatePower)
        power_states = []
        for light in self.lights:
            for response in responses:
                if light.mac_addr == response.target_addr:
                    power_states.append((light, response.power_level))
        return power_states

    def set_power_all_lights(self, power_level, duration=0, rapid=False):
        on = [True, 1, "on", 65535]
        off = [False, 0, "off"]
        try:
            if power_level in on and not rapid:
                self.broadcast_with_ack(LightSetPower, {"power_level": 65535, "duration": duration})
            elif power_level in on and rapid:
                self.broadcast_fire_and_forget(LightSetPower, {"power_level": 65535, "duration": duration}, num_repeats=5)
            elif power_level in off and not rapid:
                self.broadcast_with_ack(LightSetPower, {"power_level": 0, "duration": duration})
            elif power_level in off and rapid:
                self.broadcast_fire_and_forget(LightSetPower, {"power_level": 0, "duration": duration}, num_repeats=5)
            else:
                raise InvalidParameterException("{} is not a valid power level.".format(power_level))
        except WorkflowException as e:
            raise

    def get_color_all_lights(self):
        responses = self.broadcast_with_resp(LightGet, LightState)
        colors = []
        for light in self.lights:
            for response in responses:
                if light.mac_addr == response.target_addr:
                    colors.append((light, response.color))
        return colors

    def set_group(self, group, color, power_level=65535, duration=0, rapid=False):
        lights = self.groups[group]
        for light in lights:
            
            if power_level != 0:
                # Turn on the power first
                light.set_power(power_level, duration, rapid)
                
            light.set_hsbk(color, duration, rapid)
            
            if power_level == 0:
                # Turn off the power last
                light.set_power(power_level, duration, rapid)
                
        return True
        
    def set_hsbk_all_lights(self, hue, saturation, brightness, kelvin, duration=0, rapid=False):
        color = (hue, saturation, brightness, kelvin)
        try:
            if rapid:
                self.broadcast_fire_and_forget(LightSetColor, {"color": color, "duration": duration}, num_repeats=5)
            else:
                self.broadcast_with_ack(LightSetColor, {"color": color, "duration": duration})
        except WorkflowException as e:
            raise
                
    def set_color_all_lights(self, color, duration=0, rapid=False):
        if len(color) == 4:
            try:
                if rapid:
                    self.broadcast_fire_and_forget(LightSetColor, {"color": color, "duration": duration}, num_repeats=5)
                else:
                    self.broadcast_with_ack(LightSetColor, {"color": color, "duration": duration})
            except WorkflowException as e:
                raise
        else:
            raise InvalidParameterException("{} is not a valid color.".format(color))

    def set_waveform_all_lights(self, is_transient, color, period, cycles, duty_cycle, waveform, rapid=False):
        if len(color) == 4:
            try:
                if rapid:
                    self.broadcast_fire_and_forget(LightSetWaveform, {"transient": is_transient, "color": color, "period": period, "cycles": cycles, "duty_cycle": duty_cycle, "waveform": waveform}, num_repeats=5)
                else:
                    self.broadcast_with_ack(LightSetWaveform, {"transient": is_transient, "color": color, "period": period, "cycles": cycles, "duty_cycle": duty_cycle, "waveform": waveform})
            except WorkflowException as e:
                raise
        else:
            raise InvalidParameterException("{} is not a valid color.".format(color))

    ############################################################################
    #                                                                          #
    #                            Workflow Methods                              #
    #                                                                          #
    ############################################################################

    
    def purge(self):
        pass
        
    def discovery_done(self, group):
    
        for device in self.groups[group]:
            if not device.discovered:
                return False
        return True
    
    def get_groups(self):
        
        try:
            responses = self.broadcast_with_resp(GetService, StateService)
        except WorkflowException as e:
            raise
            #return None
        discovery_time = time()
        for r in responses:
            device = Device(r.target_addr, r.ip_addr, r.service, r.port, self.source_id, self.verbose)
            if device.supports_multizone():
                device = MultiZoneLight(r.target_addr, r.ip_addr, r.service, r.port, self.source_id, self.verbose)
            else:
                device = Light(r.target_addr, r.ip_addr, r.service, r.port, self.source_id, self.verbose)
            device.get_group()
            device.get_color()
            device.discovered = True
            device.discovery_time = discovery_time
            
            if device.group not in self.groups:
                self.groups[device.group] = [device]
            else:
                in_group = False
                g= self.groups[device.group]
                for light in g:
                    if light.mac_addr == device.mac_addr:
                        g.remove(light)
                        break
                    
                self.groups[device.group].append(device)
                
            # make sure this device didn't just get removed from another group
            for name, lights in self.groups.items():
                if name == device.group:
                    continue
                # if any other group has an item with the same mac address, remove it
                self.groups[name] = [item for item in lights if item.mac_addr != device.mac_addr]
            
        # Purge old devices (haven't been discovered recently)
        for key,val in self.groups.items():
            if len(val) == 0:
                del self.groups[key]
            else:
                for device in val:
                    if (device.discovery_time + 120000) < time():
                        self.groups[key].remove(device)
        return self.groups
            
    def discover(self, timeout_secs=0.3, num_repeats=3):
        self.initialize_socket(timeout_secs)
        msg = GetService(BROADCAST_MAC, self.source_id, seq_num=0, payload={}, ack_requested=False, response_requested=True)
        responses = []
        addr_seen = []
        num_devices_seen = 0
        attempts = 0
        while attempts < num_repeats:
            sent = False
            start_time = time()
            timedout = False
            while not timedout:
                if not sent:
                    self.sock.sendto(msg.packed_message, (UDP_BROADCAST_IP, UDP_BROADCAST_PORT))
                    sent = True
                    if self.verbose:
                        print("SEND: " + str(msg))
                try:
                    data, (ip_addr, port) = self.sock.recvfrom(1024)
                    response = unpack_lifx_message(data)
                    response.ip_addr = ip_addr
                    if self.verbose:
                        print("RECV: " + str(response))
                    if type(response) == StateService and response.origin == 1 and response.source_id == self.source_id:
                        if response.target_addr not in addr_seen and response.target_addr != BROADCAST_MAC:
                            addr_seen.append(response.target_addr)
                            num_devices_seen += 1
                            responses.append(response)
                except timeout:
                    pass
                elapsed_time = time() - start_time
                timedout = True if elapsed_time > timeout_secs else False
            attempts += 1
        self.close_socket()
        return responses

    def broadcast_fire_and_forget(self, msg_type, payload={}, timeout_secs=DEFAULT_TIMEOUT, num_repeats=DEFAULT_ATTEMPTS):
        self.initialize_socket(timeout_secs)
        msg = msg_type(BROADCAST_MAC, self.source_id, seq_num=0, payload=payload, ack_requested=False, response_requested=False)
        sent_msg_count = 0
        sleep_interval = 0.05 if num_repeats > 20 else 0
        while(sent_msg_count < num_repeats):
            self.sock.sendto(msg.packed_message, (UDP_BROADCAST_IP, UDP_BROADCAST_PORT))
            if self.verbose:
                print("SEND: " + str(msg))
            sent_msg_count += 1
            sleep(sleep_interval) # Max num of messages device can handle is 20 per second.
        self.close_socket()

    def broadcast_with_resp(self, msg_type, response_type, payload={}, timeout_secs=DEFAULT_TIMEOUT, max_attempts=DEFAULT_ATTEMPTS):
        if self.lights == None:
            self.get_lights()
        success = False
        self.initialize_socket(timeout_secs)
        if response_type == Acknowledgement:
            msg = msg_type(BROADCAST_MAC, self.source_id, seq_num=0, payload=payload, ack_requested=True, response_requested=False)
        else:
            msg = msg_type(BROADCAST_MAC, self.source_id, seq_num=0, payload=payload, ack_requested=False, response_requested=True)
        responses = []
        addr_seen = []
        num_devices_seen = 0
        attempts = 0
        while num_devices_seen < self.num_devices and attempts < max_attempts:
            sent = False
            start_time = time()
            timedout = False
            while num_devices_seen < self.num_devices and not timedout:
                if not sent:
                    self.sock.sendto(msg.packed_message, (UDP_BROADCAST_IP, UDP_BROADCAST_PORT))
                    sent = True
                    if self.verbose:
                        print("SEND: " + str(msg))
                try:
                    data, (ip_addr, port) = self.sock.recvfrom(1024)
                    response = unpack_lifx_message(data)
                    response.ip_addr = ip_addr
                    if self.verbose:
                        print("RECV: " + str(response))
                    if type(response) == response_type and response.origin == 1 and response.source_id == self.source_id:
                        if response.target_addr not in addr_seen and response.target_addr != BROADCAST_MAC:
                            addr_seen.append(response.target_addr)
                            num_devices_seen += 1
                            responses.append(response)
                            if num_devices_seen >= self.num_devices:
                                success = True
                except timeout:
                    pass
                elapsed_time = time() - start_time
                timedout = True if elapsed_time > timeout_secs else False
            attempts += 1
        if success == False:
            self.close_socket()
            raise WorkflowException("Did not receive {} in response to {}".format(str(response_type), str(msg_type)))
        else:
            self.close_socket()
        return responses

    def broadcast_with_ack(self, msg_type, payload={}, timeout_secs=DEFAULT_TIMEOUT+0.5, max_attempts=DEFAULT_ATTEMPTS):
        self.broadcast_with_resp(msg_type, Acknowledgement, payload, timeout_secs, max_attempts)

    # Not currently implemented, although the LIFX LAN protocol supports this kind of workflow natively
    def broadcast_with_ack_resp(self, msg_type, response_type, payload={}, timeout_secs=DEFAULT_TIMEOUT+0.5, max_attempts=DEFAULT_ATTEMPTS):
        pass

    ############################################################################
    #                                                                          #
    #                              Socket Methods                              #
    #                                                                          #
    ############################################################################

    def initialize_socket(self, timeout):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.sock.settimeout(timeout)
        port = UDP_BROADCAST_PORT
        self.sock.bind(("", port))

    def close_socket(self):
        self.sock.close()

def test():
    pass

if __name__=="__main__":
    test()
