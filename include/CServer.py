# -*- coding: utf-8 -*-
#!/usr/bin/env python
#########################
# Sys requirements check
#########################
#from config import *

import sys
import json
from threading import Thread, RLock # New threading module. Compatible python 2 and 3. Object oriented. Replace the deprecated _thread module

import socket
from include import CNetGames
import select
import time
import signal
from copy import deepcopy
import hmac
import random # Randomize player names

class CServer():
    def __init__(self, config, logs):
        self.room_lock = RLock()
        self.pin_attempts = {}
        self.Games = [] # Init Local Games array
        self.MsgQueue = [] # Queue of Message Dict
        self.colorlist = [color for color in range(31,39)] # First color will be red, and then green, yellow, blue, rose, cyan, grey, and back to first color.
        self.Config = config
        self.logs=logs
        self.delim='|'
        self.send_timeout = 10 # Time after what a client is considered as disconnected

    def Listen(self,NetIp,NetPort):
        self.TCP_IP = NetIp
        self.TCP_PORT = NetPort
        self.BUFFER_SIZE = 256  # Usually 1024, but we want fast response - unit is char in this case
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.TCP_IP, self.TCP_PORT))
        self.s.listen(20) # Max number of clients
        #self.s.setblocking(1)


#
# Main loop (listen for client and create a thread for each client)
#
    def __main__(self):
        i=0 # Black shell color
        self.color = {}

        while True:
            conn, addr = self.s.accept()
            userid="{}-{}".format(addr[0],addr[1])
            self.logs.warning("{} client joined server on port {}.".format(addr[0],addr[1]))
            self.color[userid] = self.colorlist[i]
            #print self.color
            #-_thread version_-thread.start_new_thread(self.client_thread,(conn,addr)) #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
            T={}
            T[i] = Thread(target=self.client_thread, args=(conn,addr))
            T[i].daemon = True # Permit CTRL-C
            T[i].start() # Start Thread
            i+=1
            if i==8:
                i=0

#
# Client thread (one per client) - started from main
#
    def client_thread(self, conn, addr):
        userid="{}-{}".format(addr[0],addr[1])
        i=0
        gamename=""
        #infinite loop so that function do not terminate and thread do not end.
        while True:
            """
            data=""
            ready = select.select([conn], [], [], 0)
            if ready:
               try:
                  #conn.settimeout(timeout) # Set timeout
                  #time.sleep(0.2) # To avoid getting all the cpu. Tried 0.1, now passed to 0.2 to slow down again
                  #data = conn.recv(self.BUFFER_SIZE) # Buffer_size stands for bytes of data to be received
                  #data=str(data.decode('UTF-8'))
                  conn.settimeout(None) # Reset timeout
               except:
                  self.logs.fatal("Bad data received or timeout ({}) has been reached for connection with {}. Aborting.".format(timeout,userid))
                  sys.exit(2)
               if data=="":
                  self.logs.debug("Closing connection or bad data received with {}. Aborting.".format(userid))
                  sys.exit(3)
            """
            # Receive data
            data=self.rcv(conn,userid)
            # Print data for debug
            self.logs.debug("Incoming network message")
            # Interpretation of the client message
            self.CheckMessage2(conn,data,addr)

#
# Receive Data and be sure that end of message has been reached
#
    def rcv(self,conn,userid,delim='|'):
        buf = ''
        data=""
        timeout = 3600
        ready = select.select([conn], [], [], 0)
        if ready:
            try:
                while True:
                    time.sleep(0.2) # Avoid consuming all cpu. Was 0.1, now I prefer 0.2 to reduce cpu again
                    data = conn.recv(self.BUFFER_SIZE)
                    buf += data.decode('utf-8') # Convert received bytes to unicode
                    found = buf.find(delim)
                    if found != -1:
                        msg = buf.split(delim, 1)
                        #print("Returning {} because we found {} in buffer ({}) : {}".format(data,delim,found,buf))
                        return str(msg[0])
            except Exception as e:
                self.logs.debug("Incoming network message")
                self.logs.fatal("Bad data received or timeout ({}) has been reached for connection with {}. Aborting.".format(timeout,userid))
                sys.exit(2)
            if data=="":
                self.logs.debug("Closing connection or bad data received with {}. Aborting.".format(userid))
                sys.exit(3)
        #return data

#
# NEW JSON CheckMessage implementation
#
    def CheckMessage2(self,conn,data,addr):
        try:
            d=json.loads(data)
        except:
            self.logs.debug("Incoming network message")
            return False
        if d:
            gamename=d['GAMENAME']
            req=d['REQUEST']
            # Send first a ACK to notify of good reception
            ack={'REQUEST':'ACK'}
            self.SendMessage2(conn,gamename,addr,ack)
            if req not in ('JOIN', 'GETVERSION'):
                with self.room_lock:
                    game = next((g for g in self.Games if g.GameName == gamename), None)
                    if game is not None and getattr(game, 'RoomPin', None) is not None and '{}-{}'.format(*addr[:2]) not in game.MembersId:
                        self.SendMessage2(conn,gamename,addr,{'REQUEST':'ROOMREFUSED','GAMENAME':gamename})
                        return False
            # Case Management
            if req=='GETVERSION':
                self.SendVersion(conn,gamename,addr)
            if req=='JOIN':
                with self.room_lock:
                    self.JoinGame2(conn,gamename,addr,d)
            if req=="CLIENTWAIT4GAMEREADY":
                while not self.CheckGameReady(gamename):
                    time.sleep(0.2) # To avoid getting all the cpu
                    pass
                d={'GAMENAME':gamename,'REQUEST':'GAMEISREADY'}
                self.SendMessage2(conn,gamename,addr,d)
            if req=="HEREISCHOOSEDGAME":
                self.SetChoosedGame(gamename,d['CHOOSEDGAME'])
            if req=="GETCHOOSEDGAME":
                self.SendGame(conn,gamename,addr)
            if req=="HEREAREPLAYERNAMES":
                self.AddPlayerNames2(gamename,d['PLAYERNAMES'])
                self.SetGameReady(gamename) # Game is ready when no more data to receive from Master
            if req=="HEREAREGAMEOPTS":
                self.AddOpts(gamename,d['GAMEOPTS'],d.get('NBDARTS', d.get('nb_darts')),d.get('NBSETS',1))
            if req=="GAMEOPTS":
                self.SendOpts(conn,gamename,addr)
            if req=="PLAYERNAMES":
                self.SendPlayers(conn,gamename,addr)
            if req=="READY" and 'NBLOCALPLAYERS' in d:
                self.SetReady(gamename,d['NBLOCALPLAYERS'])
            if req=="READY" and 'PLAYERSNAMES' in d:
                self.SetReady2(conn,gamename,addr,d['PLAYERSNAMES'],d.get('MAXPLAYERS'))
            if req=="LAUNCH":
                with self.room_lock:
                    self.Launch(gamename)
            if req=="SHUFFLE":
                self.Shuffle(gamename)
            if req=="LEAVE" and 'PLAYERSNAMES' in d:
                with self.room_lock:
                    self.SomeoneLeaving(addr,gamename,d['PLAYERSNAMES'],d['NETSTATUS'])
            if req=="ISEVERYBODYREADY":
                self.SendStatus(conn,gamename,addr)
            if req=="HEREARERANDOMVALUES":
                self.StoreRamdom(gamename,d['RANDOMVALUES'],d.get('ACTUALROUND', d.get('actual_round')),d.get('ACTUALPLAYER', d.get('actual_player')),d.get('PLAYERLAUNCH', d.get('player_launch')))
            if req=="RANDOMVALUES":
                self.SendRandom(conn,gamename,addr,d.get('ACTUALROUND', d.get('actual_round')),d.get('ACTUALPLAYER', d.get('actual_player')),d.get('PLAYERLAUNCH', d.get('player_launch')))
            if req=="PLAY":
                self.Play(gamename,d['PLAY'],d.get('ACTUALROUND', d.get('actual_round')),d.get('ACTUALPLAYER', d.get('actual_player')),d.get('PLAYERLAUNCH', d.get('player_launch')))
            if req=="WAIT4PLAYER":
                if 'WAITFOR' in d:
                    self.SendHit(conn,gamename,addr,d.get('ACTUALROUND', d.get('actual_round')),d.get('ACTUALPLAYER', d.get('actual_player')),d.get('PLAYERLAUNCH', d.get('player_launch')),d['WAITFOR'])
                else:
                    self.SendHit(conn,gamename,addr,d.get('ACTUALROUND', d.get('actual_round')),d.get('ACTUALPLAYER', d.get('actual_player')),d.get('PLAYERLAUNCH', d.get('player_launch')))
            if req=="EXIT":
                with self.room_lock:
                    self.LeaveGame(addr,gamename)

#
# New implementation of SendMessage in JSON
#
    def SendMessage2(self,conn,gamename,addr,msg):
        # Try to determine color
        userid = "{}-{}".format(addr[0],addr[1])
        try:
            MsgColor = self.color[userid]
        except KeyError:
            MsgColor = '31' # FallBaaaack to Blaaaaaack
        #self.logs.debug("\033[{}m[{}][{}-{}] Sending : {}\033[0m".format(MsgColor,gamename,addr[0],addr[1],msg))
        #conn.send(msg)
        # Print Debug
        # Try to send or timeout
        old_timeout = conn.gettimeout() # Save old timeout settings
        conn.settimeout(self.send_timeout) # Enable timeout for this request
        try:
            msg = json.dumps(msg)
            #msg = msg.encode('UTF-8')# No need anymore since python3 ! See : https://medium.com/better-programming/strings-unicode-and-bytes-in-python-3-everything-you-always-wanted-to-know-27dc02ff2686
            msg = str(msg) + str(self.delim)
            self.logs.debug("\033[{}m[{}][{}-{}] Sending : {}\033[0m".format(MsgColor,gamename,addr[0],addr[1],msg))
            #msg = msg.decode('UTF-8')
            msg = msg.encode('UTF-8') # Convert unicode to bytes
            conn.send(msg)
        except Exception as e: # If timeout reached
            self.logs.debug("Error is {}".format(e))
            self.logs.error("Error or timeout ({}) has been reached for connection with client {}. Killing thread.".format(self.send_timeout,addr))
            sys.exit(2)
        conn.settimeout(old_timeout) # Restore previous timeout

#
# Set Launch flag to True (game is ready to go - new version) - Trigger send of LAUNCH to clients via SetReady2
#
    def Launch(self,gamename):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                LstGames.Launch=True

#
# Randomize Player names
#
    def Shuffle(self,gamename):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                random.shuffle(LstGames.PlayersNames)

#
# Handle someone who leave the game
#

    def SomeoneLeaving(self,addr,gamename,Pl,NetStatus):
        userid = "{}-{}".format(addr[0],addr[1])
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                if NetStatus=='YOUAREMASTER':
                    LstGames.Aborted=True
                if hasattr(LstGames, 'RoomCapacity'):
                    Pl = LstGames.RoomGroups.pop(userid, [])
                for P in Pl:
                    try:
                        LstGames.PlayersNames.remove(P) # Remove players if they are ready
                    except:
                        pass # When there is still noone in the game (nobody's ready)
                self.logs.debug("Some has left. Remaining in game {} : {}".format(gamename,LstGames.PlayersNames))
                self.LeaveGame(addr,gamename)

#
# Send Server version
#

    def SendVersion(self,conn,gamename,addr):
        d={'GAMENAME':gamename,'REQUEST':'VERSION','VERSION':self.Config.pyDartsVersion}
        self.SendMessage2(conn,gamename,addr,d)

# PLAYERS NAMES
# Add players names to list (sent by master server - will be sent
#

    def AddPlayerNames2(self,gamename,playernames):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                for player in playernames:
                    self.logs.debug("Adding player {} to game {}".format(player,gamename))
                    LstGames.PlayersNames.append(player)

#
# Add players names in queue for a specific user
#
    def SendPlayers(self,conn,gamename,addr): #JSON
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                d={'GAMENAME':gamename,'REQUEST':'PLAYERNAMES','PLAYERNAMES':LstGames.PlayersNames}
                self.SendMessage2(conn,gamename,addr,d)

# GAME OPTIONS
# Add game options if they are received from master client
#
    def AddOpts(self,gamename,Opts,nb_darts,nb_sets=1): #JSON
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                LstGames.Opts=Opts
                LstGames.nb_darts = nb_darts
                LstGames.nbsets = nb_sets

    def SendOpts(self,conn,gamename,addr): # JSON
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                d={'GAMENAME':gamename,'REQUEST':'GAMEOPTS','GAMEOPTS':LstGames.Opts,'nb_darts':LstGames.nb_darts,'NBDARTS':LstGames.nb_darts,'NBSETS':LstGames.nbsets}
                self.SendMessage2(conn,gamename,addr,d)
# CHOOSED GAME
# Set Choosed game as server want
#
    def SetChoosedGame(self,gamename,ChoosedGame):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                LstGames.ChoosedGame = ChoosedGame
                self.logs.debug("Setting choosed game for {} : {}".format(gamename,LstGames.ChoosedGame))

    def SendGame(self,conn,gamename,addr): # JSON Version
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                d={'GAMENAME':gamename,'CHOOSEDGAME':LstGames.ChoosedGame}
                self.SendMessage2(conn,gamename,addr,d)

#
# Create or Join a game
#
    def JoinGame2(self,conn,gamename,addr,request=None):
        request = request or {}
        userid = '{}-{}'.format(*addr[:2])
        game = next((g for g in self.Games if g.GameName == gamename), None)
        pin = request.get('ROOMPIN')
        valid = isinstance(pin,str) and len(pin)==4 and pin.isascii() and pin.isdigit()
        status = 'ROOMREFUSED'
        if game is None:
            if request.get('ROOMMODE') != 'join' and (pin is None or valid):
                game = CNetGames.CNetGames(gamename)
                game.RoomPin = pin
                self.Games.append(game)
                status = 'YOUAREMASTER'
        elif request.get('ROOMMODE') != 'create' and not game.Aborted:
            secret = getattr(game,'RoomPin',None)
            if secret is None or userid in game.MembersId:
                status = 'YOUARESLAVE'
            elif pin is None:
                status = 'PINREQUIRED'
            else:
                now = time.monotonic()
                self.pin_attempts = {k:v for k,v in self.pin_attempts.items() if v[1]>now}
                key = (addr[0],gamename)
                count, expiry = self.pin_attempts.get(key,(0,now+300))
                if count >= 5 or (key not in self.pin_attempts and len(self.pin_attempts)>=10000):
                    status = 'PINLOCKED'
                elif valid and hmac.compare_digest(secret,pin):
                    status = 'YOUARESLAVE'
                else:
                    self.pin_attempts[key] = (count+1,expiry)
                    status = 'PINWRONG'
        if status in ('YOUAREMASTER','YOUARESLAVE') and userid not in game.MembersId:
            game.MembersId.append(userid)
        self.SendMessage2(conn,gamename,addr,{'GAMENAME':gamename,'REQUEST':'NETSTATUS','NETSTATUS':status,'PRIVATE':bool(game is not None and getattr(game,'RoomPin',None) is not None)})

#
#  Increment the number of ready players and tell everybody that everybody's ready
#

    def SetReady2(self,conn,gamename,addr,Players,capacity=None):
        userid = "{}-{}".format(*addr[:2])
        d = {'REQUEST':'ROOMREFUSED','MESSAGE':'Salon indisponible','GAMENAME':gamename}
        with self.room_lock:
            for game in self.Games:
                if game.GameName != gamename or userid not in game.MembersId:
                    continue
                limit = getattr(game, 'RoomCapacity', None)
                valid = isinstance(Players, list) and all(isinstance(p, str) for p in Players)
                new = list(dict.fromkeys(Players)) if valid else []
                admitted = getattr(game, 'RoomGroups', {})
                previous = admitted.get(userid)
                others = set(game.PlayersNames) - set(previous or [])
                if (limit is None and game.MembersId[0] == userid
                        and type(capacity) is int and 2 <= capacity <= 12
                        and not game.Launch and not game.Aborted and new
                        and len(others | set(new)) <= capacity):
                    limit = game.RoomCapacity = capacity
                if game.Aborted:
                    d.update(REQUEST='ABORT', PLAYERSNAMES=[])
                elif limit is None:
                    # Preserve legacy rooms that did not negotiate a capacity.
                    game.PlayersNames.extend(p for p in new if p not in game.PlayersNames)
                    d.update(REQUEST='LAUNCH' if game.Launch else 'PLAYERSNAMES',
                                PLAYERSNAMES=list(game.PlayersNames))
                elif previous == new:
                    d.update(REQUEST='LAUNCH' if game.Launch else 'PLAYERSNAMES',
                                PLAYERSNAMES=list(game.PlayersNames), MAXPLAYERS=limit)
                elif game.Launch:
                    d['MESSAGE'] = 'Partie déjà lancée.'
                elif not new or previous is not None or len(new) != len(Players) or others.intersection(new):
                    d['MESSAGE'] = 'Un nom est déjà utilisé dans ce salon.'
                elif len(others) + len(new) > limit:
                    d['MESSAGE'] = 'Places disponibles : {}. Votre groupe : {}.'.format(max(0,limit-len(others)),len(new))
                else:
                    game.PlayersNames.extend(new)
                    admitted[userid] = new
                    game.RoomGroups = admitted
                    d.update(REQUEST='PLAYERSNAMES', PLAYERSNAMES=list(game.PlayersNames), MAXPLAYERS=limit)
                break
        self.SendMessage2(conn,gamename,addr,d)

    def SendStatus(self,conn,gamename,addr):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                while LstGames.PlayersReady != len(LstGames.PlayersNames):
                    time.sleep(0.1) # To avoid getting all the cpu
                    pass
                d={'GAMENAME':gamename,'REQUEST':'EVERYBODYISREADY'}
                self.SendMessage2(conn,gamename,addr,d)
#
# Check if master client has sent all information to server (if true, send them to clients)
#
    def CheckGameReady(self,gamename):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                if LstGames.GameReady:
                    return True
                else:
                    return False
#
# If all data has been received by the server, set the game setup readyu to be downloaded
#
    def SetGameReady(self,gamename):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                self.logs.debug("{} is now complete. No more options to receive from server.".format(gamename))
                LstGames.GameReady = True # All data has been received by server

#
# Random values
#

    def StoreRamdom(self,gamename,rand,actual_round,actual_player,player_launch):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                # Delete any previously stored value
                LstGames.RandomValues={}
                # Store new values
                hitkey="{}{}{}".format(actual_round,actual_player,player_launch)
                LstGames.RandomValues[hitkey] = rand


    def SendRandom(self,conn,gamename,addr,actual_round,actual_player,player_launch):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                hitkey="{}{}{}".format(actual_round,actual_player,player_launch)
                while hitkey not in LstGames.RandomValues:
                    time.sleep(0.1) # To avoid getting all the cpu
                    pass
                rand=LstGames.RandomValues[hitkey]
                d={'GAMENAME':gamename,'REQUEST':'RANDOMVALUES','RANDOMVALUES':rand,'actual_player':actual_player,'ACTUALPLAYER':actual_player,'actual_round':actual_round,'ACTUALROUND':actual_round,'player_launch':player_launch,'PLAYERLAUNCH':player_launch}
                self.SendMessage2(conn,gamename,addr,d)


#
# Play
#

    def Play(self,gamename,hit,actual_round,actual_player,player_launch):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                # Delete any stored values
                LstGames.HitValues={}
                # In any case, store actual hit
                self.logs.debug("Storing hit {} for round {}, player {}, launch {} and game {}".format(hit,actual_round,actual_player,player_launch,gamename))
                hitkey="{}{}{}".format(actual_round,actual_player,player_launch)
                LstGames.HitValues[hitkey]=hit

    def SendHit(self,conn,gamename,addr,actual_round,actual_player,player_launch,waitfor=False):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                hitkey="{}{}{}".format(actual_round,actual_player,player_launch)
                if waitfor==False:
                    while hitkey not in LstGames.HitValues:
                        time.sleep(0.1) # To avoid getting all the cpu
                        pass
                    hit=LstGames.HitValues[hitkey]
                    d={'GAMENAME':gamename,'REQUEST':'SOMEONEPLAYED','PLAY':hit,'actual_round':actual_round,'ACTUALROUND':actual_round,'player_launch':player_launch,'PLAYERLAUNCH':player_launch,'actual_player':actual_player,'ACTUALPLAYER':actual_player}
                else:
                    while hitkey not in LstGames.HitValues or LstGames.HitValues[hitkey]!=waitfor:
                        time.sleep(0.1) # To avoid getting all the cpu
                        pass
                    d={'GAMENAME':gamename,'REQUEST':'SOMEONEPLAYED','PLAY':waitfor,'actual_round':actual_round,'ACTUALROUND':actual_round,'player_launch':player_launch,'PLAYERLAUNCH':player_launch,'actual_player':actual_player,'ACTUALPLAYER':actual_player}
                hit=LstGames.HitValues[hitkey]
                self.SendMessage2(conn,gamename,addr,d)



#
# Leave a game
#
    def LeaveGame(self,addr,gamename=None):
        # Remove user from Members
        userid = "{}-{}".format(addr[0],addr[1])
        for LstGames in self.Games:
            if (gamename!=None and LstGames.GameName == gamename) or gamename == None:
                if userid in LstGames.MembersId:
                    self.logs.debug("Removing {} from members of game named {}".format(addr,LstGames.GameName))
                    #filter(lambda a: a != userid, self.Games[gamename].MembersId)
                    if hasattr(LstGames, 'RoomGroups') and not LstGames.Launch:
                        if LstGames.MembersId[0] == userid:
                            LstGames.Aborted = True
                        group = LstGames.RoomGroups.pop(userid, [])
                        LstGames.PlayersNames[:] = [p for p in LstGames.PlayersNames if p not in group]
                    LstGames.MembersId.remove(userid)
        # Remove color from color list (try/except is here if there is multiple connection from same ip address it will remove all of them)
        try:
            del self.color[userid]
        except:
            pass
        # Remove game if no more members
        index2del = -1
        for key,val in enumerate(self.Games):
            if len(self.Games[key].MembersId) == 0:
                index2del = key
        if index2del >= 0:
            self.logs.warning("No more members in this game : {}. Removing.".format(self.Games[index2del].GameName))
            del self.Games[index2del]

#
# Close connection method
#
    def closecx(self):
        self.conn.close()
