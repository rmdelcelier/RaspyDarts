#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket # Network
import sys # Various things
import json # Encode array in json for transport
import time # To sleep, for instance
from include import CArgs # Argument parsing
from include import CLogs # Import Clogs from path
from include import CConfig # Import Config Class to read config file
from include import CMail # Class used to notify people by email (stored in a sqlite db)
#
# This script provide a server to share Game Names, players and so on !
#

class CMasterServer:
    def __init__(self,NetIp,NetPort,Logs,Config):
        self.Config=Config
        self.TCP_IP = NetIp
        self.TCP_PORT = NetPort
        self.BUFFER_SIZE = 4096  # Usually 1024, unit is char in this case
        # Create socket object
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Set socket options
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.TCP_IP, self.TCP_PORT))
        self.s.listen(25) # Max number of clients
        #self.Games = [] # Init Games array - deprecated
        #self.MsgQueue = [] # Queue of Message Dict - deprecated
        self.colorlist = [color for color in range(31,39)] # First color will be red, and then green, yellow, blue, rose, cyan, grey, and back to first color.
        self.Logs=Logs
        # Storage (Sqlite)
        self.db = CMail.CMasterServerDb(self.Logs,Config)
        # Socket properties
        self.delim='|' # Delimiter for msg - so the client knows that the end of the msg has been reached

#
# Main loop
#
    def __main__(self):
        self.color = {}
        self.room_capacities = {}
        self.private_rooms = set()
        #self.Games=[]-deprecated
        i=0
        pl=1
        nbgames=26
        # Test mode, create fake games
        if self.Config.GetValue('Server','mastertest'):# if test mode
            self.Logs.Log("DEBUG","Inserting fake games in MasterServer for test purpose")
            for i in range(1,nbgames+1):
                pl+=1
                if pl==13:
                    pl=1
                game={'GAMECREATOR':'test','GAMETYPE':'Cricket','GAMENAME':'SAMPLEGAME{}'.format(i),'SERVERIP':'1.2.3.{}'.format(i),'SERVERPORT':1234,'PLAYERS':pl}
                self.db.insert_game(game)
        # Close opened games
        if self.Config.GetValue('Server','masterclosegames'):# if the user request to close the existing games
            self.Logs.Log("DEBUG","Closing all existing games ")
            self.db.close_all_games()
        #
        # Master server Loop
        #
        while True:
            # Sleep a bit to reduce CPU
            time.sleep(0.2)
            # Init data variable
            data=""
            # Listen for connection - a particularity for Master Server is that every request is a new connection (because it's pretty rare and requests are not particulary linked)
            self.cx, addr = self.s.accept()
            # Create an id for client, based on IP + port
            cxid="{}-{}".format(addr[0],addr[1])
            # Log
            self.Logs.Log("DEBUG","{} client joined server on port {}.".format(addr[0],addr[1]))
            # Try to receive data
            try:
                data = self.cx.recv(self.BUFFER_SIZE) # Buffer_size stands for bytes of data to be received
            except:
                pass # Nothing to receive (or wrong data) - pass

            # If data is ok
            if data!="":
                # Load Json data
                try:
                    Ddata=json.loads(str(data.decode('UTF-8')))
                    req=Ddata['REQUEST']
                except:
                    self.Logs.Log("ERROR","Received non JSON data : {}".format(data))
                    Ddata=None
                    req=None
                # Log full data
                self.Logs.Log("DEBUG",format(data))
                # Please create Game :)
                if req == 'CREATION':
                    self.Logs.Log("DEBUG","Hu hu ! We received a creation notice :) from {}. We put it in storage.".format(cxid))
                    del Ddata['REQUEST']
                    Ddata['STATUS']='OPEN'
                    capacity = Ddata.pop('MAXPLAYERS', None)
                    private = Ddata.pop('PRIVATE', False) is True
                    self.db.insert_game(Ddata)
                    key = Ddata['GAMENAME']
                    self.private_rooms.discard(key)
                    if private:
                        self.private_rooms.add(key)
                    if type(capacity) is int and 2 <= capacity <= 12:
                        self.room_capacities[key] = capacity
                    else:
                        self.room_capacities.pop(key, None)
                    if self.Config.GetValue('Server','notifications')=='1':
                        # Notify people that a game is available (by email)
                        try:
                            mail = CMail.CMail(self.Logs,ConfigServer)
                            emails = self.db.get_emails()
                            if emails and len(emails)>0:
                                mail.notify_created_game(emails,Ddata['GAMENAME'],Ddata['GAMETYPE'],Ddata['GAMECREATOR'])
                        except Exception as e:
                            self.Logs.Log("WARNING","Unable to notify registred users that the game has been created")
                    else:
                        self.Logs.Log("DEBUG","Bypassing notifications of registred users, as requested")
                # Add thoses people to the game
                elif req == 'JOIN':
                    self.Logs.Log("DEBUG","We received a join notice :) from {}. We add players.".format(cxid))
                    self.db.add_players(Ddata['GAMENAME'],int(Ddata['PLAYERS']))
                # Remove those players from the game
                elif req == 'LEAVE':
                    self.Logs.Log("DEBUG","We received a leaving notice :) from {}. We remove players.".format(cxid))
                    self.db.remove_players(Ddata['GAMENAME'],int(Ddata['PLAYERS']))
                # Please give me a list of available games !!
                elif req == 'LIST':
                    self.Logs.Log("DEBUG","Hu hu ! We received a listing request :) from {}. Let send it.".format(cxid))
                    #time.sleep( 30 )
                    rows = self.db.get_games()
                    open_names = {row.get('GAMENAME') for row in rows}
                    self.room_capacities = {
                        k: v for k, v in self.room_capacities.items()
                        if k in open_names
                    }
                    self.private_rooms.intersection_update(open_names)
                    gamelist = [
                        dict(row, MAXPLAYERS=self.room_capacities[row['GAMENAME']])
                        if row.get('GAMENAME') in self.room_capacities else row
                        for row in rows
                    ]
                    gamelist = [dict(row, PRIVATE=True) if row.get('GAMENAME') in self.private_rooms else row for row in gamelist]
                    if (len(gamelist)==0):
                        self.Logs.Log("DEBUG","List is empty. Sending notice of emptiness")
                        r={'RESPONSE':'EMPTY'}
                    else:
                        #r=self.Games - deprecated
                        r=gamelist
                    self.send(r)
                # Please delete the game - based on game name
                # REMOVAL is still handled here for backward compatibility with v1.0.x
                elif req == 'LAUNCH' or req == 'REMOVAL':
                    self.Logs.Log("DEBUG","Hurry ! We received a launching request ! from {} for game {}. Let archive it.".format(cxid,Ddata['GAMENAME']))
                    self.db.remove_game(Ddata['GAMENAME'])
                    self.room_capacities.pop(Ddata['GAMENAME'], None)
                    self.private_rooms.discard(Ddata['GAMENAME'])
                elif req == 'CANCEL':
                    self.Logs.Log("DEBUG","Ho ! We received a cancel request (delete) from {} for game {}. Let delete it.".format(cxid,Ddata['GAMENAME']))
                    self.db.delete_game(Ddata['GAMENAME'])
                    self.room_capacities.pop(Ddata['GAMENAME'], None)
                    self.private_rooms.discard(Ddata['GAMENAME'])
                elif req == 'GETVERSION':
                    self.Logs.Log("DEBUG","Someone is interested by the size of our dart. Sending {}".format(self.Config.pyDartsVersion))
                    d={'REQUEST':'VERSION','VERSION':self.Config.pyDartsVersion}
                    self.send(d)
                else:
                    self.Logs.Log("ERROR","Unhandled message : {}".format(data))
            self.Logs.Log("DEBUG","Closing connexion with {}".format(cxid))
            self.cx.close()

#
# Send the msg and append the delimiter
#
    def send(self,msg):
        msg=json.dumps(msg)+self.delim
        msg=msg.encode('UTF-8')
        self.cx.send(msg)

#
# Init
#
Logs = CLogs.CLogs()
Args = CArgs.CArgs()
Config=CConfig.CConfig(Args,Logs)
ConfigGlobals=Config.ReadConfigFile("SectionGlobals") # Read config file for main configuration
ConfigAdvanced=Config.ReadConfigFile("SectionAdvanced") # Read config file for main configuration
ConfigServer=Config.ReadConfigFile("Server") # Read config file for server specific configuration
Logs.SetConfig(Config)
Args.SetLogs(Logs)

# Verbosity
debuglevel = int(Config.GetValue('SectionGlobals','debuglevel'))
if debuglevel>=1 and debuglevel<=4:
    Logs.UpdateFacility(debuglevel)

# Getting Interface or setting default
ServerInterface = Config.GetValue('SectionAdvanced','listen')

# Setting Ip from interface
ServerIp = Args.get_ip_address(ServerInterface)

if ServerIp==None:
    Logs.Log("FATAL","Unable to determine Ip address from interface {}. Use -h for help.".format(ServerInterface))
    sys.exit(1)
# Getting port or set default
ServerPort = int(Config.GetValue('SectionGlobals','masterport'))

Logs.Log("DEBUG","Starting Master Server on interface {} ({}), on port {}".format(ServerInterface,ServerIp,ServerPort))

#
# Launch
#
Master=CMasterServer(ServerIp,ServerPort,Logs,Config)
Master.__main__()
# END
