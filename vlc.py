import configparser
import requests
from requests.auth import HTTPBasicAuth
import urllib
import xml.etree.ElementTree as ET
from subprocess import Popen, PIPE, STDOUT, DEVNULL, check_output
import os
import psutil

class VLC:
    class __VLC:
        def __init__(self):
            config = configparser.ConfigParser()
            config.read("config")
            self.config = config["VLC"]
            self.baseurl = "http://localhost:8080/requests/status.xml?"
        
        def send_command(self, command, val=None):
            """ Send commands to VLC http interface - seek, volume, pause/play etc .""" 
            print("sending vlc command %s" % command)
            if (val == None ):
                requests.get(self.baseurl + "command=" + command, auth=HTTPBasicAuth('', self.config["password"]))
            else:
                if command == "in_play" or command == "in_enqueue":
                    param = "&input="
                else:
                    param = "&val="
                requests.get(self.baseurl + "command=" + command + param + urllib.parse.quote_plus(str(val)), auth=HTTPBasicAuth('', self.config["password"]))

        def get_attributes(self):
            """ It parses the VLC status xml file and returns a dictionary of attributes. """
            attributes = {}
            try:
                page = requests.get(self.baseurl, auth=HTTPBasicAuth('', self.config["password"]))
                
                et = ET.fromstring(page.text)
                
                # It is advised to look at the structure of status.xml to understand this
                for ele in et:
                    # If element doesn't have sub elements.
                    if len(ele) == 0:
                        attributes[ ele.tag ] = ele.text
                    else:
                        attributes[ ele.tag ] = {}
                        for subele in ele:
                            if subele.tag == "category":
                                subattr = attributes[ ele.tag ][ subele.get("name") ] = {}
                                for _subele in subele:
                                    subattr[ _subele.get("name")] = _subele.text
                            else:
                                attributes[ ele.tag ][ subele.tag ] = subele.text
            except Exception:
                pass
                
            return attributes
            
        def get_state(self):
            attributes = self.get_attributes()
            if attributes:
                return (attributes["fullscreen"], attributes["state"])
            else:
                return ("", "")
                
        def set_volume(self, val):
            """ Sets the volume of VLC. The interface expects value between 0 and 512 while in the UI it is 0% to 200%. So a factor of 2.56 is used
            to convert 0% to 200% to a scale of 0 to 512."""

            self.send_command("volume", val)
            
        def volume_up(self, val):
            curvol = int(self.get_attributes()["volume"])
            self.send_command("volume", curvol+val)
        
        def volume_down(self, val):
            curvol = int(self.get_attributes()["volume"])
            self.send_command("volume", curvol-val)

        def random(self, on):
            rand = self.get_attributes()["random"]
            if ((rand == "true" and on == False) or 
            (rand == "false" and on == True)):
                self.send_command("pl_random")
        
        def play_file(self, infile):
            """ Send the input file to be played. The in_file must be a valid playable resource."""
            if( not( os.path.isfile(infile) ) ):
                raise Exception("FileNotFound: The file " + infile + " does not exist.")
            else:
                uri = 'file:' + urllib.request.pathname2url(os.path.abspath(path))
                self.send_command("in_play", uri)
                
        def queue_file(self, infile):
            """ Send the input file to be played. The in_file must be a valid playable resource."""
            if( not( os.path.isfile(infile) ) ):
                raise Exception("FileNotFound: The file " + infile + " does not exist.")
            else:
                uri = 'file:' + urllib.request.pathname2url(os.path.abspath(path))
                self.send_command("in_enqueue", uri)

        def clear_playlist(self):
            self.send_command("pl_empty")
            
        def play_pause(self):
            """Toggle between play and pause."""

            self.send_command("pl_pause")

        def stop(self):
            """Stops the player."""

            self.send_command("pl_stop")

        def fullscreen(self):
            """ Toggle fullscreen."""

            self.send_command("fullscreen")

        def next(self):
            """ Next media on the playlist. """

            self.send_command("pl_next")

        def previous(self):
            """ Previous media on the playlist. """

            self.send_command("pl_previous")
        
        def fastForward(self, seconds):
            timestr = "%2B" + str(seconds)
            self.send_command("seek", timestr)
                
        def rewind(self, seconds):
            timestr = "-" + str(seconds)
            self.send_command("seek", time)

        def open(self):
        
            # open VLC
            self.gui = Popen([self.config["path"], "-I", "qt", "--extraintf", "http", "--http-password", self.config["password"]], stdout=DEVNULL, stderr=STDOUT)
            
        def close(self):
            try:
                #Popen.kill(self.gui)
                for proc in psutil.process_iter():
                    if proc.name() == "vlc.exe":
                        p = psutil.Process(proc.pid)
                        p.kill()
                        
            except Exception as e:
                print(e)
            
    instance = None
    
    def __init__(self):
        if not VLC.instance:
            VLC.instance = VLC.__VLC()
        
    def __getattr__(self, name):
        return getattr(self.instance, name)
        
    def __setattr__(self, name):
        return setattr(self.instance, name)
            