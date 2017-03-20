  
import windows
from findInLibrary import MediaLibrary
from apiclient.discovery import build
import random
import configparser
import webbrowser
from vlc import VLC
from windows import WindowsController
import inspect

class MediaController:

    def __init__(self):

        # parse config
        self.config = configparser.ConfigParser()
        self.config.read("config")
        
        # init vlc controller
        self.vlc = VLC()
        
        # init windows controller
        self.windows = WindowsController()
        
        # init library
        self.library = MediaLibrary()
        
        # init google apis
        self.youtube_api = build("youtube", "v3", developerKey = self.config["GOOGLE"]["developer_key"])
        #self.customSearch = build("customsearch", "v1", developerKey = config["GOOGLE"]["developer_key"])
        
    def youtube(self, args):
        print("play youtube vid %s\n" % args[inspect.currentframe().f_code.co_name][0])
        self.playFromYoutube(args[inspect.currentframe().f_code.co_name][0])
        
    def youtubePlaylist(self, args):
        self.playFromYoutube(args[inspect.currentframe().f_code.co_name][0], queryType = "playlist")
    
    def stop(self, args):
        self.vlc.pl_pause()
        
    def resume(self, args):
        self.vlc.pl_pause()
        
    def fullscreen(self, args):
        self.vlc.fullscreen()
        
    def next(self, args):
        self.vlc.next()
        
    def prev(self, args):
        self.vlc.previous()
        
    def volume(self, args):
        self.vlc.volume(args[inspect.currentframe().f_code.co_name][0])
        
    def plex(self, plex, args):
        showName = args[inspect.currentframe().f_code.co_name][0]
        seasonNum = args["seasonNum"][0]
        episodeNum = args["episodeNum"][0]
        self.playFromLibrary(showName, seasonNum, episodeNum)
        
    def plexShuffle(self, args):
        showName = args[inspect.currentframe().f_code.co_name][0]
        self.shuffleFromLibrary(showName)
        
    def plexLates(self, args):
        self.playLatest(args[inspect.currentframe().f_code.co_name][0])
        
    def movie(self, args):
        self.playMovie(args[inspect.currentframe().f_code.co_name][0])
        
    def forwardSecs(self, args):
        self.vlc.fastForward(int(args[inspect.currentframe().f_code.co_name][0]))
        
    def rewindSecs(self, args):
        self.vlc.rewind(int(args[inspect.currentframe().f_code.co_name][0]))
        
    def volumeUp(self, args):
        self.vlc.volume_up(int(args[inspect.currentframe().f_code.co_name][0]))
        
    def volumeDown(self, args):
        self.vlc.volume_down(int(args[inspect.currentframe().f_code.co_name][0]))
        
    def open(self, args):
        self.vlc.open()
        
    def close(self, args):
        self.vlc.close()
        
    def windowsVolume(self, args):
        self.windows.setVolume(float(args[inspect.currentframe().f_code.co_name][0]))
        
    def windowsVolumeUp(self, args):
        self.windows.setVolume(float(args[inspect.currentframe().f_code.co_name][0]), False)
        
    def windowsVolumeDown(self, args):
        self.windows.setVolume(-1 * float(args[inspect.currentframe().f_code.co_name][0]), False)
        
    def sleep(self, args):
        self.windows.sleep()
        
    def hibernate(self, args):
        self.windows.hibernate()
        
    def search(self, args):
        query =  args[inspect.currentframe().f_code.co_name][0]
        print("googling %s\n" % query)
        #googleSearch(query) # this is to get a string of results from google api
        webbrowser.open('https://www.google.com/search?q=%s' % query) # this opens google search in default browser
        
    def imageSearch(self, args):
        query =  args[inspect.currentframe().f_code.co_name][0]
        print("searching google images for %s\n" % query)
        webbrowser.open('https://www.google.com/images?q=%s' % query) # this opens google search in default browser
        
        
        
        
            
    def playLatest(self, showName):
        show = library.find_show(showName)
        episodeList = library.list_episode_paths(show)
        if not len(episodeList) == 0:
            vlc.clear_playlist()
            vlc.random(False)
            for mediaPath in episodeList:
                 vlc.play_file(mediaPath)

    def playMovie(self, movieQuery):
        """
        Play a movie from the local library
        :param movieQuery:
        :return: None
        """
        movie = self.library.find_movie_path(movieQuery)
        if movie is not None:
            self.vlc.clear_playlist()
            self.vlc.random(False)
            self.vlc.play_file(movie)
        

    def googleSearch(self, query):
        res = self.customSearch.cse().list(
          q=query,
          cx=self.config["GOOGLE"]["search_engine_id"],
          num=1,
          safe='off',
        ).execute()
        print(res)
        
    def shuffleFromLibrary(self, showName):
        show = self.library.find_show(showName)
        episodeList = self.library.list_episode_paths(show)
        print(episodeList)
        if not len(episodeList) == 0:
            self.vlc.clear_playlist()
            self.vlc.random(True)
            random.shuffle(episodeList, random.random)
            for mediaPath in episodeList:
                 self.vlc.play_file(mediaPath)
            

    def playFromLibrary(self, showName, seasonNum, episodeNum):
        show = self.library.find_show(showName)
        index, episodeList = self, self.library.index_search(show, int(seasonNum), int(episodeNum))
        print(index, episodeList)
        if not len(episodeList) == 0:
            self.vlc.clear_playlist()
            self.vlc.random(False)
            self.vlc.play_file(episodeList[index])
            truncatedList = episodeList[index + 1:]
            for mediaPath in truncatedList:
                self.vlc.queue_file(mediaPath)

    def playFromYoutube(self, query, queryType = "video"):
        print(query, queryType)
        response = self.youtube_api.search().list(q=urllib.parse.unquote(query), part="id,snippet", maxResults=5, type=queryType).execute()
        results = response.get("items", [])
        if queryType == "video" and not len(results) == 0:
            self.playYoutubeVideos([results[0]["id"]["videoId"]])
        elif queryType == "playlist" and not len(results) == 0:
            self.playYoutubePlaylist(results[0]["id"]["playlistId"])

    def playYoutubeVideos(self, videoIds):
        self.vlc.clear_playlist()
        self.vlc.random(False)

        if not len(videoIds) == 0:
            videoUrl = "http://youtube.com/watch?v=%s" % videoIds[0]
            self.vlc.send("add %s \n" % videoUrl)

        for videoId in videoIds[1:]:
            videoUrl = "http://youtube.com/watch?v=%s" % videoId
            self.vlc.queue_file(videoUrl)

    def playYoutubePlaylist(self, playlistId):
        response = self.youtube_api.playlistItems().list(part="id,snippet", playlistId=playlistId, maxResults = 50).execute()

        results = response.get("items", [])

        videoIds = map(lambda result: result["snippet"]["resourceId"]["videoId"], results)

        self.playYoutubeVideos(videoIds)
        
    