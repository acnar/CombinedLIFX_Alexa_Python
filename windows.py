
from __future__ import print_function
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, ISimpleAudioVolume
from subprocess import check_output
import ctypes
import win32con

class WindowsController:
    
    def __init__(self):
        
        # init windows volume interface
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))
        
    def cmd(self, command):
        print(check_output(command, shell=True).decode())

    def setVolume(self, vol, absolute=True):
        if not absolute:
            newVol = float(self.volume.GetMasterVolumeLevelScalar()) + vol
        else:
            newVol = vol
        print("volume.GetMasterVolumeLevelScalar(): %s" % self.volume.GetMasterVolumeLevelScalar())
        self.volume.SetMasterVolumeLevelScalar(newVol, None)
        print("volume.GetMasterVolumeLevelScalar(): %s" % self.volume.GetMasterVolumeLevelScalar())
        
    def sleep(self):
        self.cmd("%windir%/System32/rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        
    def hibernate(self):
        self.cmd("%windir%/System32/rundll32.exe powrprof.dll,SetSuspendState Hibernate")
