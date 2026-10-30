# -*- coding: utf-8 -*-
"""
Game by ... @fragarch!
"""

from include import cplayer
from include import cgame
import random

GAME_LOGO = 'Hangman.png'
HEADERS = "D1","D2","D3","","","","CASE" 
OPTIONS = {'theme': 'default' , 'max_round': 20, 'master': False, 'word_length' : 6} 
NB_DARTS = 3
GAME_RECORDS = {'Score Per Round': 'DESC', 'Dribbles': 'DESC'}

class CPlayerExtended(cplayer.Player):
    """
    Extend the basic player
    """
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        # Read the CJoueur class parameters, and add here yours if needed
        
        self.token = 'tbd'
        self.color = 'tbd'

        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record]='0'

class Game(cgame.Game):
    """
    Hangman game class
    """
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        # GameRecords is the dictionnary of stats (see above)
        self.game_records = GAME_RECORDS
        # Import game settings
        self.logo = GAME_LOGO
        self.headers = HEADERS
        self.nb_darts = NB_DARTS
        self.options = options
            
        # Hangman specific options
        self.scoreHangman = 0
        self.currentAttempts = 0
        self.currentWord = ""
        self.hintWord = ""
        self.scaleX = self.display.res['x'] * 425 / 1920          # Adapt drawing to screen
        self.scaleY = self.display.res['y'] * 544 / 1080          # Adapt drawing to screen
        self.scaleX = self.scaleX * 1.1                           # Change size
        self.scaleY = self.scaleY * 1.1 
        self.letterX = self.display.res['x'] * 122.88 / 1920 
        self.letterY = self.display.res['y'] * 162.56 / 1080 
        self.spanX = 122.88
        self.randomWord = False
        self.goodLetters = []
        self.badLetters = []
        
        # Note : all positions are for 1920/1080. We will have to resize
        self.ratioX = self.display.res['x'] / 1920
        self.ratioY = self.display.res['y'] / 1080
        
        #  Get the options
        self.max_round = int(options['max_round'])
        self.master = options['master']
        
        # Define word length (6 = 6, 7 = 7, 8 = 8, More = random 6-7-8)
        self.word_length = options['word_length']
        if (int(self.word_length) < 6) :
            self.word_length = 9
        if (int(self.word_length) > 8):
            self.randomWord = True
        
        # More fun, more videos
        self.videos = {} # To fill with success + failure

        # For rpi
        self.rpi = rpi

        self.winner = None
        self.infos = ''
        self.translate = self.display.lang.translate
        self.show_hit = False
        
    def newWordRound(self, currentPoints):
        if self.master == False and currentPoints > 0 : self.currentAttempts = 0 # master difficulty, no reset after each word
        self.rpi.set_target_leds('DB#yellow')  
        self.goodLetters = []
        self.badLetters = []
        self.hintWord = ""
        lines = []
        myLen = self.word_length
        if (self.randomWord) :
            myLen = random.randint(6,8)
        with open("games/fun/" + str(myLen) + "letters.txt") as file:
            for line in file: 
                line = line.strip()
                lines.append(line)
        theWord = random.choice(lines)
        theWord = theWord.upper()
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.listAlphabet = []
        for letter in alphabet:
            self.listAlphabet.append(letter)
            random.shuffle(self.listAlphabet)
        i = 0
        while len(self.listAlphabet) > 20:
            if(self.listAlphabet[i] not in theWord):
                self.listAlphabet.pop(i)
            else:
                i = i+1
        hint = []
        for l in theWord:
            hint.append("-")
        self.hintWord = "".join(hint)
        return theWord.upper()

    def pre_dart_check(self,  players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """

        self.show_hit = False
        return_code = 0
        # infos Can be used to create a per-player debug output
        self.infos += f"###### Player {actual_player} ######{self.lf}"
        
        if player_launch == 1 and actual_round == 1 and actual_player == 0 :
            self.display.display_background('HangmanBackground')
            self.currentWord = self.newWordRound(0)
            hint = []
            for l in self.currentWord:
                hint.append("-")
            self.hintWord = "".join(hint)
            
        self.dmd.send_text(self.hintWord, sens=None, iteration=None)
         
        
        """
        
        # You will probably save the turn to be used in case of backup turn (each first launch) :
        if player_launch == 1:
            self.save_turn(players)
            # Clean actual_players' columns
            i = 0
            for column in players[actual_player].columns:
                players[actual_player].columns[i] = ['', 'txt']
                i += 1
        """
        # Turn leds on (good letters in green , bad in red)
        targ = []
        if (len(self.goodLetters) > 0):
            for num in self.goodLetters:
                targ.append('S' + str(num))
                targ.append('D' + str(num))
                targ.append('T' + str(num))
                goodLeds = '|'.join([f'{key}#{self.colors[0]}' for key in targ])
               
        targ2 = []
        if (len(self.badLetters) > 0):
            for num in self.badLetters:
                targ2.append('S' + str(num))
                targ2.append('D' + str(num))
                targ2.append('T' + str(num))     
                badLeds = '|'.join([f'{key}#{self.colors[1]}' for key in targ2]) 
        
        if (len(self.goodLetters) + len(self.badLetters) > 0) :
            if (len(self.goodLetters) == 0) :
                self.rpi.set_target_leds(badLeds)
            elif (len(self.badLetters) == 0) :
                self.rpi.set_target_leds(goodLeds)
            else :
                self.rpi.set_target_leds(goodLeds + '|' + badLeds)              

        # Backuping scores
        self.save_turn(players)
        # Send debug output to log system. Use DEBUG or WARNING or ERROR or FATAL
        self.logs.debug(self.infos)
         
        return return_code
        
    def updateHint(self, letter, progress): #function to update shown word with letters already found
        i = 0
        while i < len(self.currentWord):
            if letter == self.currentWord[i]:
                progress[i] = letter
                i = i + 1
            else:
                i = i + 1
        return "".join(progress)

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        Function run after each dart throw - for example, add points to player
        """
        
        handler = self.init_handler()

        return_code = 0
        
        self.show_hit = False
        
        if player_launch == self.nb_darts and actual_round >= self.max_round and actual_player == len(players)-1 :
            return_code = 2
            
        hit = int(hit[1:])
        if (self.listAlphabet[hit - 1] in self.currentWord):
            self.goodLetters.append(hit)
            #self.display.play_sound('chalkSound')
            handler['sound'] = 'chalkSound'
            
            self.hintWord = self.updateHint(self.listAlphabet[hit - 1], list(self.hintWord)) # letter found, update hint on screen
            #self.dmd.send_text(self.hintWord, sens=None, iteration=None)
            handler['dmd'] = self.hintWord
            
            if (self.hintWord == self.currentWord) :
                # video successWord to add ?
                #self.display.play_sound('HangmanFound')
                handler['sound'] = 'HangmanFound'
                
                self.scoreHangman = self.scoreHangman + 1
                self.goodLetters = []
                self.badLetters = []
                self.currentWord = self.newWordRound(self.scoreHangman) 
        else :
            self.currentAttempts += 1 # letter not in word, update attempts + hangmangraphic
            #self.display.play_sound('errorSound')
            handler['sound'] = 'errorSound'
            
            self.badLetters.append(hit)
            if (self.currentAttempts == 6) :
                # video failure to add ?
                return_code = 2
                
                
        # You may want to count how many touches
        # Simple = 1 touch, Double = 2 touches, Triple = 3 touches
        players[actual_player].increment_hits(hit)

        # You may want to count darts played
        players[actual_player].darts_thrown += 1

        # It is recommanded to update stats every dart thrown
        self.refresh_stats(players, actual_round)

        # Time for shot or video ?
        handler['take_shot'] = self.time_to_take_shot_or_video(hit)
        handler['return_code'] = return_code
        return handler

        # Return code to main
        #return return_code
        
    def refresh_game_screen(self, Players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player,TxtOnLogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
       
        ClickZones={}
        # Clear screen
        # self.display.screen.fill((0,0,0))
        
        # Background image
        self.display.display_background('HangmanBackground')
        
        # Hangman graphic depends on failed hits
        self.display.display_image(self.display.file_class.get_full_filename('Hangman/hangman' + str(self.currentAttempts + 1), 'images'), 40 * self.ratioX, 150 * self.ratioY, self.scaleX, self.scaleY, True)
        

		#Ligne 1 lettres
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        nextLetter = 0
        i = 0
        while (i < 10) :
            if (alphabet[i + nextLetter] in self.listAlphabet) :
                suffix = 'w'
                if self.listAlphabet.index(alphabet[i + nextLetter]) + 1 in self.goodLetters : suffix = 'g'
                if self.listAlphabet.index(alphabet[i + nextLetter]) + 1 in self.badLetters : suffix = 'r'
                self.display.display_image(self.display.file_class.get_full_filename('Hangman/' + alphabet[i + nextLetter]  + suffix, 'images'), (534 + (i * self.spanX)) * self.ratioX, 150 * self.ratioY, self.letterX, self.letterY, True)
                self.display.display_image(self.display.file_class.get_full_filename('Hangman/' + str(self.listAlphabet.index(alphabet[i + nextLetter]) + 1), 'images'), (534 + (i * self.spanX)) * self.ratioX, 312.56 * self.ratioY, self.letterX, self.letterY, True)
                i +=1 
            else :
                nextLetter += 1
		
        #Ligne 2 lettres 
 
        while (i < 20) :
            if (alphabet[i + nextLetter] in self.listAlphabet) :
                suffix = 'w'
                if self.listAlphabet.index(alphabet[i + nextLetter]) + 1 in self.goodLetters : suffix = 'g'
                if self.listAlphabet.index(alphabet[i + nextLetter]) + 1 in self.badLetters : suffix = 'r'
                self.display.display_image(self.display.file_class.get_full_filename('Hangman/' + alphabet[i + nextLetter]  + suffix, 'images'), (534 + ((i-10) * self.spanX)) * self.ratioX, 525 * self.ratioY, self.letterX, self.letterY, True)
                self.display.display_image(self.display.file_class.get_full_filename('Hangman/' + str(self.listAlphabet.index(alphabet[i + nextLetter]) + 1), 'images'), (534 + ((i - 10) * self.spanX)) * self.ratioX, 687.56 * self.ratioY, self.letterX, self.letterY, True)
                i +=1 
            else :
                nextLetter += 1
                   
        #Affichage indice + score
        self.display.blit_text(f"{self.hintWord}", 20 * self.ratioX, 870 * self.ratioY, 800 * self.ratioX, 250 * self.ratioY, color=(255, 255, 255), align='Center', valign='Center', margin=False)
        self.display.blit_text("Score: " + f"{self.scoreHangman}", 870 * self.ratioX, 900 * self.ratioY, 400 * self.ratioX, 250 * self.ratioY, color=(255, 255, 0), align='Center', valign='Center', margin=False)
        
            
        # Show round number   
        right_x = int(self.display.res['x'] * 13 / 16)
        right_y = 20
        right_width = int(self.display.res['x'] * 3 / 16)
        right_height = int(self.display.res['y'] / 16)

        self.display.blit_text(f"Round", right_x, right_y, int(right_width / 3), right_height, color=(246, 85, 41), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{actual_round} / {max_round}", right_x + int(right_width / 2), 0, self.display.res['x'] - right_x - int(right_width / 2), right_height * 2, color=(246, 85, 41), align='Right', valign='top', margin=False)
               
        # Refresh screen
        if end_of_game :
            ClickZones = self.display.end_of_game_menu(logo, stat_button=False)

        self.display.update_screen()

        return [ClickZones]

    def refresh_stats(self, players, actual_round):
        """
        Method to frefresh player.stat - Adapt to the stats you want.
        They represent mathematical formulas used to calculate stats. Refreshed after every launch
        """
        for player in players:
            player.stats['Score Per Round'] = player.score_per_round(actual_round)
            
   # Display name of the player if given, Player X otherwise
    def display_player_name(self, display, pos_x, pos_y, actual_player, player):
        """
        
        """

    def display_segment(self):
        """
        Display or not the hit segment
        """
        return self.show_hit
        
    def early_player_button(self, players, actual_player, actual_round):
        """
        Run when player push PLAYERBUTTON before last dart
        return code :
            1. Next player
            2. Last round reach
            3. Winner is
        """
        return_code = 1
        
        
        # Victory for current player
        return_code = 3
        
        if actual_round == int(self.max_round) and actual_player == self.nb_players - 1:
            self.logs.debug("At last round, default action is to return game over.")
            self.logs.debug("If it's not what you expect, raise a bug please.")
            # If its a early_player_button just at the last round - return GameOver
            return_code = 2
        return return_code
        
    def miss_button(self, players, actual_player, actual_round, player_launch):
        """
        EMPTY
        """

    def check_players_allowed(self, nb_players):
        return nb_players <= 1
