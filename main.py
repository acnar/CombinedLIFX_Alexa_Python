#import lifx
import threading
import signal
import ctypes
import win32con
import socketserver
import configparser
from alexa_listener import AlexaListener
from media_controller import MediaController
from lifxlan.lifxlan import *
from vlc import VLC
import sys
from lifx_manager import LIFXManager
from windows import WindowsController
import time
from pyHook import HookManager
from pyHook.HookManager import HookConstants, GetKeyState
import pythoncom


def sigterm_handler(signal, frame):
    global manager
    global manager_mutex
    
    print("Quitting...\n")
    manager_mutex.acquire()
    manager.WriteCache()
    manager_mutex.release()
    
    done = True
    sys.exit(0)

def vlc_listener():
    global manager
    global manager_mutex
    
    vlc = VLC()
    
    try:
        while not done:
            manager_mutex.acquire()
            manager.Discover()
            if manager.active_config_num != 0:
                fullscreen, playstate = vlc.get_state();
                if playstate != "" and fullscreen != "":
                    if (playstate == "playing" and fullscreen == "true") and (manager.light_state != LIFXManager.LIGHTS_DOWN):
                        print("lightsdown\n")
                        manager.LightsDown()
                    elif (playstate != "playing" or fullscreen != "true") and (manager.light_state == LIFXManager.LIGHTS_DOWN):
                        manager.LightsRestore()
                        print("lightsrestore\n")
                
            elif (manager.light_state != Manager.LIGHTS_RESTORED):
                manager.LightsRestore()
                print("lightsrestore\n")
        
            manager_mutex.release()

            time.sleep(5)

        vlc.close()
    except Exception as e:
        print("exception")
        manager_mutex.release()
        print(e)

    print("vlc listener exit\n")
    print("done = ")
    print(done)
    
def OnKeyboardEvent(event):
    #print(HookConstants.VKeyToID('VK_LCONTROL') >> 15)
    #ctrl_pressed = GetAsyncKeyState(win32con.VK_LCONTROL)
    #for i in range(0,256):
    #    print("%i = %i\n" % (i, GetKeyState(i)))
    #print(ctrl_pressed)
    ctrl_pressed = GetKeyState(HookConstants.VKeyToID('VK_LCONTROL') >> 15)
    #if ctrl_pressed:
    #    print("ctrl pressed")
    #print(event.KeyID)
    #print(event.Key)
    #print(HookConstants.IDToName(event.Ascii))

    return 0
        
def hotkey_listener():
    global manager
    global manager_mutex
    
    register_hotkeys()
    try:
        while not done:
            msg = ctypes.wintypes.MSG()
            if ctypes.windll.user32.GetMessageA(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == win32con.WM_HOTKEY:
                    if msg.wParam < len(manager.configs):
                        manager_mutex.acquire()
                        manager.activeConfigNum = msg.wParam
                        print("Setting config \"%s\"\n" % manager.configs[str(msg.wParam)][0])
                        manager.light_state = LIFXManager.LIGHTS_CHANGED;
                        manager_mutex.release()
                    else:
                        print("Config %i not defined\n" % msg.wParam)
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageA(ctypes.byref(msg))
            time.sleep(0.001)
    except Exception as e:
        print(e)
    
def register_hotkeys():
    # register CTRL + 0 - CTRL + 9
    failure = False

    for i in range(0x30, 0x40):
        if ctypes.windll.user32.RegisterHotKey(None, i-0x30, 2, i) == 0:
            print("Error registering hotkey CTRL + " + i + "\n")
            falure = True

    return failure

# main

global done
global manager
global manager_mutex

done = False

manager_mutex = threading.Lock()
manager = LIFXManager()
    
signal.signal(signal.SIGINT, sigterm_handler)

t2 = threading.Thread(target=vlc_listener)
t3 = threading.Thread(target=hotkey_listener)

t2.daemon = True
t3.daemon = True

t2.start()
t3.start()

# init server - run in main thread
config = configparser.ConfigParser()
config.read("config")
httpd = socketserver.TCPServer(("", int(config["SERVER"]["port"])), AlexaListener)
httpd.serve_forever()

# Lans' test interface (comment out init server lines)
"""
mc = MediaController()

while 1:
    try:
        cmd = input(">")
        arglist = cmd.split(" ")
        args = dict()
        if arglist[0] == "quit":
            break
        args[arglist[0]] = [arglist[1]]
        for key in args.keys():
            print(key)
            handler = getattr(mc, key)
            if callable(handler):
                print("callable")
                print(handler)
                handler(args)
                break
    except Exception:
        pass
"""

t2.join()
t3.join()

