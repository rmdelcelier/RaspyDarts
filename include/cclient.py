#!/usr/bin/env python

import socket
import time
import sys
import select
import json

def debug(func):
    def wrapper(*args, **kargs):
        print(f"=DEBUG= Calling {func.__name__} with args:{args}, kargs={kargs}")
        start = time.perf_counter()
        result = func(*args, **kargs)
        duration = time.perf_counter() - start
        print(f"=DEBUG= Result of {func.__name__} is {result}")
        print(f"=DEBUG= {func.__name__} took {int(duration * 1000)} ms")
        return result
    return wrapper

class Client():
    def __init__(self, logs):
        self.buffer_size = 256 # unit is char in our case
        self.logs = logs
        self.wait4gametimeout = 60
        self.timeout = 60 # Time for an open connexion timeout (1 hour)
        self.connexion_timeout = 10 # Timeout for a connexion (in seconds)
        self.ack_timeout = 10 # Timeout for a ack to come back
        # Socket properties
        self.delimiter='|'

    #@debug
    def connect_host(self,TCP_IP,TCP_PORT):
        """
        Join selected server
        """
        self.connexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connexion.settimeout(self.connexion_timeout)
        self.connexion.connect((TCP_IP, TCP_PORT))
        #self.connexion.settimeout(None)
        #self.connexion.setblocking(1)

    #@debug
    def test_host(self,server):
        """
        test host
        """
        try:
            host=server.split(':')[0]
            port=int(server.split(':')[1])
            self.connect_host(host,port)
        except:
            return False

        self.connexion.close()
        return True

    #@debug
    def play(self,actual_round,actual_player,playerlaunch,Message):
        """
        Player plays
        """
        ret = self.send({'GAMENAME': self.gamename, 'REQUEST': 'PLAY', \
                'ACTUALPLAYER': actual_player, \
                'ACTUALROUND': actual_round, \
                'PLAYERLAUNCH': playerlaunch, \
                'PLAY': Message})
        if ret is not None:
            return ret

    #@debug
    def wait_someone_play(self,actual_round,actual_player,playerlaunch,waitfor=False):
        """
        Wait for someone play
        """
        if waitfor is False:
            request = {'GAMENAME': self.gamename, 'REQUEST': 'WAIT4PLAYER', 'ACTUALPLAYER': actual_player, \
                    'ACTUALROUND': actual_round, 'PLAYERLAUNCH': playerlaunch}
        else:
            request = {'GAMENAME': self.gamename, 'REQUEST': 'WAIT4PLAYER', 'ACTUALPLAYER': actual_player, \
                    'ACTUALROUND': actual_round, 'PLAYERLAUNCH': playerlaunch, 'WAITFOR': waitfor}

        self.send(request)
        data = {}
        data['REQUEST'] = None
        data['ACTUALPLAYER'] = None
        data['ACTUALROUND'] = None
        data['PLAYERLAUNCH'] = None

        if not waitfor:
            while data['REQUEST'] != 'SOMEONEPLAYED' or data['ACTUALPLAYER'] != actual_player \
                    or data['ACTUALROUND'] != actual_round or data['PLAYERLAUNCH'] != playerlaunch:
                data = self.receive()
                if data == 'TIMEOUT':
                    return 'TIMEOUT'
            self.logs.debug(f"Received acceptable hit : {data['PLAY']} from remote server.")
            if isinstance(data['PLAY'], str):
                return data['PLAY'].upper()
            else:
                return data['PLAY']
        else:
            while data['REQUEST'] != 'SOMEONEPLAYED' or data['ACTUALPLAYER'] != actual_player \
                    or data['ACTUALROUND'] != actual_round or data['PLAYERLAUNCH'] != playerlaunch or data['PLAY'] != waitfor:
                data = self.receive()
                if data == 'TIMEOUT':
                    return 'TIMEOUT'
            self.logs.debug(f"Received {data['PLAY']} from remote server, as expected !")
            if isinstance(data['PLAY'], str):
                return data['PLAY'].upper()
            else:
                return data['PLAY']

    #@debug
    def send_players(self, names):
        """
        Send Player Names (in one line, comma separated)
        """
        self.send({'GAMENAME': self.gamename, 'REQUEST': 'HEREAREPLAYERNAMES', 'PLAYERNAMES': names})

    #@debug
    def next_set(self, players):
        """
        Send new player's order
        """
        if self.send({'GAMENAME': self.gamename, 'REQUEST': 'NEXTSET', 'PLAYERSNAMES': players}) is None:
            data = {}
            data = self.receive()
            while 'REQUEST' not in data:
                time.sleep(0.2)
                data = self.receive()
            return data
        else:
            return 'TIMEOUT'

    #@debug
    def wait_next_set(self, set_number):
        """
        Wait from server new player's order for next set
        """
        if self.send({'GAMENAME': self.gamename, 'REQUEST': 'WAITNEXTSET', 'SETNUMBER': set_number}) is None:
            data = {}
            while 'REQUEST' not in data:
                time.sleep(0.2)
                data = self.receive()
            self.logs.debug(f"Received next set players' list : {data}")

            if data['REQUEST'] == 'NEXTSET':
                print(f"data['PLAYERSNAMES']={data['PLAYERSNAMES']}")
                print(f"type= {type(data['PLAYERSNAMES'])}")

                return data['PLAYERSNAMES'][:]
        else:
            return 'TIMEOUT'

    #@debug
    def get_players(self): # JSON
        """
        Get player names (in one line, comma separated). The Ack is the player names return
        """
        data = {'GAMENAME': self.gamename, 'REQUEST': 'PLAYERNAMES'}
        self.send(data)
        data = []
        while "PLAYERNAMES" not in data:
            data = self.receive()
        self.logs.debug(f"Received players' list : {data['PLAYERSNAMES']}")
        return data["PLAYERNAMES"]

    #@debug
    def send_options(self, options, nb_darts, nb_sets): # JSON
        """
        Send game Options
        """
        data = {'GAMENAME': self.gamename, 'REQUEST': 'HEREAREGAMEOPTS', 'GAMEOPTS': options, 'NBDARTS': nb_darts, 'NBSETS': nb_sets}
        self.send(data)

    #@debug
    def get_options(self): # JSON
        """
        Get game Options
        """
        request = {'GAMENAME': self.gamename, 'REQUEST': 'GAMEOPTS'}
        data = {}
        self.send(request)
        while 'GAMEOPTS' not in data:
            data = self.receive()
        return data['GAMEOPTS'], data['NBSETS']

    #@debug
    def send_game(self, game):
        """
        Send Choosed Game to server. Wait for an ACK
        """
        self.send({'GAMENAME': self.gamename, 'REQUEST': 'HEREISCHOOSEDGAME', 'CHOOSEDGAME': game})

    #@debug
    def get_game(self):
        """
        Get the game from master server - JSON
        """
        data = {'GAMENAME': self.gamename, 'REQUEST': 'GETCHOOSEDGAME'}
        self.send(data)
        data = []
        while "CHOOSEDGAME" not in data:
            data = self.receive()
        return data["CHOOSEDGAME"]

    #@debug
    def get_random(self, actual_round, actual_player, playerlaunch):
        """
        Get Random values
        """
        request={'GAMENAME':self.gamename,'REQUEST':'RANDOMVALUES','ACTUALROUND':actual_round,'ACTUALPLAYER':actual_player,'PLAYERLAUNCH':playerlaunch}
        self.send(request)
        data={}
        data['REQUEST']=None
        data['ACTUALPLAYER']=None
        data['PLAYERLAUNCH']=None
        data['ACTUALROUND']=None
        while data['REQUEST']!="RANDOMVALUES" or data['ACTUALPLAYER']!=actual_player or data['ACTUALROUND']!=actual_round or data['PLAYERLAUNCH']!=playerlaunch:
            data = self.receive()
        self.logs.debug("Received acceptables random values {} for player {}".format(data['RANDOMVALUES'],data['ACTUALPLAYER']))
        return data['RANDOMVALUES']

    #@debug
    def send_random(self,rand,actual_round,actual_player,playerlaunch):
        """
        Send Random values
        """
        self.send({'GAMENAME': self.gamename, 'REQUEST': 'HEREARERANDOMVALUES', 'RANDOMVALUES': rand, \
                'ACTUALPLAYER': actual_player, 'ACTUALROUND': actual_round, 'PLAYERLAUNCH': playerlaunch})

    #@debug
    def get_server_version(self,gamename):
        """
        Request server version
        """
        self.logs.debug('Getting server version...')
        data = {'REQUEST':'GETVERSION','GAMENAME':gamename}
        self.send(data)
        while data['REQUEST'] != "VERSION":
            data = self.receive()
        return data['VERSION']

    #@debug
    def send_local_players(self, players, capacity=None):
        """
        Send list of players
        """
        request = {'GAMENAME': self.gamename, 'REQUEST': 'READY', 'PLAYERSNAMES': players}
        if capacity is not None:
            request['MAXPLAYERS'] = capacity
        self.send(request)
        data = {}
        while 'REQUEST' not in data:
            data = self.receive()
            if not isinstance(data, dict):
                return {'REQUEST': 'ROOMREFUSED', 'MESSAGE': 'Le serveur ne répond pas.'}
        return data

    #@debug
    def close_host(self):
        """
        Explicitely tell the server we are leaving
        """
        time.sleep(1)
        data = {'GAMENAME': self.gamename, 'REQUEST':'EXIT'}
        self.send(data)
        self.connexion.close()

    #@debug
    def send(self, message, delimiter='|'):
        """
        Send a message
        """
        self.logs.debug(f"Sending to game server : {message.get('REQUEST')}... ")
        message = json.dumps(message) # Converting to JSON
        message = f"{message}{delimiter}" # Append delimiter
        message = message.encode('UTF-8')# Encoding in byte format - utf-8
        try:
            send_len = self.connexion.sendall(message) # UTF-8 encoding and send
            self.logs.debug(f"Sent {len(message)} bytes")
            error = self.ack() # Wait for ACK for each message
            if error is not None:
                return error
            else:
                return None
        except:
            return 'ERROR'

    #@debug
    def receive(self, BUF=False, TIMEOUT=False):
        """
        Wait for a message
        """
        if not BUF:
            BUF = self.buffer_size
        if not TIMEOUT:
            TIMEOUT = self.timeout

        old_timeout = self.connexion.gettimeout() # Save old timeout settings
        buf = '' # Init buffer
        data = False # Init data
        # Run until something happen (data can arrive in multiple message - depends of quantity and buffer size)
        counter = 0
        while True:
            counter += 1
            time.sleep(0.2)# Avoid consuming all cpu. Was 0.1, now I prefer 0.2 to reduce cpu again
            # Try to retrieve the whole message in a specified time
            if counter > self.timeout * 5:
                self.logs.fatal(f"Timeout ({self.timeout}) because of no response from server. Aborting.")
                return 'TIMEOUT'
            try:
                self.connexion.settimeout(TIMEOUT) # Enable timeout for this request
                data = self.connexion.recv(BUF) # Receive data
            except BlockingIOError:
                # Raising this seems to be normal in python3, either with setblocking True or False, either on server and/or client.
                #self.logs.debug("BlockingIOError raised. Received {}".format(data))
                # So passing...
                pass
            except socket.timeout as e: # If timeout reached
                self.logs.fatal(f"Bad data received or timeout ({self.timeout}) has been reached for connection with game server. Aborting.")
                #sys.exit(2)
                return 'TIMEOUT'
            except Exception as e:
                self.logs.error("An error occured : {}".format(e))
            # Try to understand the message
            if data:
                try:
                    #data=json.loads(str(data.decode('UTF-8')))
                    buf += data.decode('utf-8') # Decode utf-8 data (convert bytes to unicode)
                    #buf += json.loads(str(data.decode('UTF-8')))
                    if buf.find(self.delimiter)!=-1: # If signal of end of message is found
                        msg = buf.split(self.delimiter, 1) # Remove delimiter
                        self.connexion.settimeout(old_timeout) # Restore original timeout settings
                        self.logs.debug("OK. Received : {}".format(buf))
                        return json.loads(str(msg[0])) # Return message converted to json
                except Exception as exception:
                    self.logs.error(f"Wrong data : {data}")
                    self.logs.error(f"Exception was : {exception}")
                    sys.exit(1)

    #@debug
    def ack(self):
        data = {'REQUEST': None}
        old_timeout = self.connexion.gettimeout() # Save old timeout settings

        while data['REQUEST'] != 'ACK':
            try:
                self.connexion.settimeout(self.ack_timeout) # Enable timeout for this request
                data = str(self.connexion.recv(19).decode('UTF-8'))
                self.logs.debug(f"Received : [{data}]")
                if data != '':
                    data = data.split(self.delimiter, 1) # Split with delimiter
                    data = str(data[0]) # take only message part of splitted array
                    data = json.loads(data)
            except socket.timeout as exception: # If timeout reached
                self.logs.debug(f"Error was {exception}")
                self.logs.fatal(f"Cannot get ACK in delay ({self.ack_timeout} sec) from remote server. Aborting. Sorry the cause is probably a bug in server or a version mismatch.")
                #sys.exit(2)
                return 'TIMEOUT'
            except Exception as exception:
                self.logs.warning(f"Problem receiving ack : {exception}")
                data = {'REQUEST': None}
                pass

        self.logs.debug("Received : {}".format(data))
        return None

    #@debug
    def join2(self, game, pin=None, mode=None):
        """
        Join a game (json version)
        """
        self.gamename =  game
        request = {'REQUEST': 'JOIN', 'GAMENAME': game}
        if pin is not None:
            request['ROOMPIN'] = pin
        if mode is not None:
            request['ROOMMODE'] = mode
        self.send(request)
        # The server should return one of the following
        data = {}
        while "NETSTATUS" not in data and data != 'TIMEOUT':
            data = self.receive()
        # Return
        if data == 'TIMEOUT':
            return 'TIMEOUT'
        if mode == 'create' and pin is not None and data.get('PRIVATE') is not True:
            return 'PRIVACYUNSUPPORTED'
        return str(data['NETSTATUS'])


    #@debug
    def leave_game(self, game, players, status):
        self.send({'REQUEST': 'LEAVE', 'GAMENAME': game, "NETSTATUS": status, \
                "PLAYERSNAMES": players})

###################
# Notice Master Server (if it is up). Master Server role is to centralize games so people can play together worldwide.
###################

class MasterClient():
    def __init__(self, logs):
        self.buffer_size = 4096 # unit is char in our case - bigger
        self.logs = logs
        self.connexion_timeout = 10

    #@debug
    def connect_master(self, ip, port):
        self.logs.debug(f"Connect to master server: {ip}:{port}")

        self.connexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        old_timeout = self.connexion.gettimeout() # Save old timeout settings
        self.connexion.settimeout(self.connexion_timeout)
        self.connexion.connect((ip, port))
        self.connexion.settimeout(old_timeout)# Restore old timeout

    #@debug
    def wait_list(self,NuPl):
        """
        Wait for Listing
        """
        got_it = False
        while not got_it:
            self.send({'REQUEST': 'LIST'})
            data = self.receive()
            if data and data != "":
                try:
                    data = json.loads(data)
                except:
                    self.logs.error(f"Error loading json data for : {data}")
                if 'RESPONSE' in data and data['RESPONSE'] == 'EMPTY':
                    return 0
                serverlist = data
                got_it = True
            else:
                return False

        # Clean list from all games where there is not enough room for us
        index = 0
        filtered_serverlist = []
        self.logs.debug("Received :".format(serverlist))
        for server in serverlist:
            if int(server['PLAYERS']) + int(NuPl) <= 12: # If it goes up to the max number of players
                filtered_serverlist.append(serverlist[index])
            index += 1

        if len(filtered_serverlist) == 0:
            return False

        return filtered_serverlist

    #@debug
    def send(self, message): # JSON
        """
        Send a message to the server
        """
        self.logs.debug("Sending to master server : {}... ".format(message))
        self.connexion.sendall(json.dumps(message).encode('UTF-8'))

    #@debug
    def send_game_info(self, host, alias, port, game_name, gametype, creator, number_of_players, nb_sets, capacity=None, private=False):
        """
        Send game infos
        """
        if not alias:
            ip = host
        else:
            ip = alias

        self.send({'REQUEST': 'CREATION', 'SERVERIP': ip, 'SERVERPORT': port, \
                'GAMENAME': game_name, 'GAMETYPE': gametype, 'GAMECREATOR': creator, \
                'PLAYERS': number_of_players, 'NBSETS': nb_sets, 'MAXPLAYERS': capacity, 'PRIVATE': private})

    #@debug
    def join_game(self, game, number_of_players):
        """
        Join a game
        """
        self.send({'REQUEST': 'JOIN', 'GAMENAME': game, 'PLAYERS': number_of_players})

    #@debug
    def leave_game(self, game, number_of_players):
        """
        Send leave game
        """
        self.send({'REQUEST': 'LEAVE', 'GAMENAME': game, 'PLAYERS': number_of_players})

    #@debug
    def launch_game(self, game):
        """
        Send a removal query to server
        """
        self.send({'REQUEST': 'LAUNCH', 'GAMENAME': game})

    #@debug
    def cancel_game(self, game):
        """
        Send a delete query to server
        """
        self.send({'REQUEST': 'CANCEL', 'GAMENAME': game})

    #@debug
    def close_connection(self):
        """
        Explicitely tell the server we are leaving
        """
        self.connexion.close()

    #@debug
    def receive(self, delimiter='|'):
        """
        Receive Data and be sure that the end has been reached, looking for the delimiter
        """
        old_timeout = self.connexion.gettimeout() # Save old timeout settings
        buf = '' # Init buffer
        data = False # Init data
        # Run until something happen (data can arrive in multiple message - depends of quantity and buffer size)
        while True:
            time.sleep(0.2)# Avoid consuming all cpu. Was 0.1, now I prefer 0.2 to reduce cpu again
            try:
                #self.connexion.settimeout(self.connexion_timeout) # Enable timeout for this request
                data = self.connexion.recv(self.buffer_size) # Receive data
                self.logs.debug(f"Received : {data}")
            except socket.timeout as exception: # If timeout reached
                self.logs.error("Master Server reached timeout ({self.connexion_timeout} sec)")
                return False # CX problem signal. Stop trying
            if data:
                buf += data.decode('utf-8') # Decode utf-8 data
                if buf.find(delimiter) != -1: # If signal of end of message is found
                    msg = buf.split(delimiter, 1) # Remove delimiter
                    self.connexion.settimeout(old_timeout) # Restore original timeout settings
                    return str(msg[0]) # Return message
