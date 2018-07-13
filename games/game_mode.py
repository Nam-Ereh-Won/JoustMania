from enum import Enum
from math import sqrt
from multiprocessing import Process, Value, Array
from piaudio import Audio
import common, colors
import numpy
import psmove
import random
import time
from abc import ABC, abstractmethod

#How fast the music can go
SLOW_MUSIC_SPEED = 0.7
MID_MUSIC_SPEED = 1.0
FAST_MUSIC_SPEED = 1.5

#The min and max timeframe in seconds for
#the speed change to trigger, randomly selected
MIN_MUSIC_FAST_TIME = 4
MAX_MUSIC_FAST_TIME = 8
MIN_MUSIC_MID_TIME = 7
MAX_MUSIC_MID_TIME = 16
MIN_MUSIC_SLOW_TIME = 10
MAX_MUSIC_SLOW_TIME = 23

END_MIN_MUSIC_FAST_TIME = 6
END_MAX_MUSIC_FAST_TIME = 10
END_MIN_MUSIC_MID_TIME = 7
END_MAX_MUSIC_MID_TIME = 11
END_MIN_MUSIC_SLOW_TIME = 8
END_MAX_MUSIC_SLOW_TIME = 12

#Default Sensitivity of the contollers
#These are changed from the options in common
SLOW_MAX = 0.55
SLOW_WARNING = 0.35
MID_MAX = 1
MID_WARNING = 0.28
FAST_MAX = 1.8
FAST_WARNING = 0.8

#How long the speed change takes
INTERVAL_CHANGE = 1.5

#How long the winning moves shall sparkle
END_GAME_PAUSE = 6
KILL_GAME_PAUSE = 4

class Opts(Enum):
    alive = 0
    selection = 1
    holding = 2
    team = 3
    is_commander = 4

class Selections(Enum):
    nothing = 0
    a_button = 1
    trigger = 2
    triangle = 3

class Holding(Enum):
    not_holding = 0
    holding = 1

class Bool(Enum):
    no = 0
    yes = 1
	

class Game_mode(ABC):

	@classmethod
	def calculate_flash_time(cls, r,g,b, score):
		flash_percent = max(min(float(score)+0.2,1.0),0.0)
		new_r = int(common.lerp(255, r, flash_percent))
		new_g = int(common.lerp(255, g, flash_percent))
		new_b = int(common.lerp(255, b, flash_percent))
		return (new_r, new_g, new_b)

	@classmethod
	def track_move(cls, move_serial, move_num, team, num_teams, pregen_team_colors, dead_move, force_color, music_speed, move_opts):
		start = False
		no_rumble = time.time() + 1
		move_last_value = None
		move = common.get_move(move_serial, move_num)
		team_colors = pregen_team_colors
		vibrate = False
		vibration_time = time.time() + 1
		flash_lights = True
		flash_lights_timer = 0
		start_inv = False
		change_arr = [0,0,0]
		#find place for game specific logic

		while True:
			if sum(force_color) != 0:
				no_rumble_time = time.time() + 5
				time.sleep(0.01)
				move.set_leds(*force_color)
				move.update_leds()
				move.set_rumble(0)
				no_rumble = time.time() + 0.5
			elif dead_move.value == 1:
				if move.poll():
					ax, ay, az = move.get_accelerometer_frame(psmove.Frame_SecondHalf)
					total = sqrt(sum([ax**2, ay**2, az**2]))
					if move_last_value is not None:
						change_real = abs(move_last_value - total)
						change_arr[0] = change_arr[1]
						change_arr[1] = change_arr[2]
						change_arr[2] = change_real
						change = (change_arr[0] + change_arr[1]+change_arr[2])/3
						
						#my brain can't even with this part rn
						warning = SLOW_WARNING
						threshold = SLOW_MAX
						
						if vibrate:
							flash_lights_timer += 1
							if flash_lights_timer > 7:
								flash_lights_timer = 0
								flash_lights = not flash_lights
							if flash_lights:
								move.set_leds(*colors.Colors.White60.value)
							else:
								move.set_leds(*team_colors[team.value].value)
							if time.time() < vibration_time - 0.22:
								move.set_rumble(110)
							else:
								move.set_rumble(0)
							if time.time() > vibration_time:
								vibrate = False
						else:
							move.set_leds(*team_colors[team.value].value)

						if change > threshold:
							if time.time() > no_rumble:
								if red_on_kill:
									move.set_leds(*colors.Colors.Red.value)
								else:
									move.set_leds(*colors.Colors.Black.value)
								move.set_rumble(90)
								dead_move.value = 0
						elif change > warning and not vibrate:
							if time.time() > no_rumble:
								vibrate = True
								vibration_time = time.time() + 0.5

					move_last_value = total
				move.update_leds()
			
			elif dead_move.value < 1:

				time.sleep(0.5)

	def __init__(self, moves, command_queue, ns, music):

        self.command_queue = command_queue
        self.ns = ns
        self.game_mode = game_mode
        self.sensitivity = self.ns.settings['sensitivity']
        self.play_audio = self.ns.settings['play_audio']
        self.color_lock = self.ns.settings['color_lock']
        self.color_lock_choices = self.ns.settings['color_lock_choices']
        self.random_teams = self.ns.settings['random_teams']
        self.red_on_kill = self.ns.settings['red_on_kill']
		
		
		global SLOW_MAX
        global SLOW_WARNING
        global MID_MAX
        global MID_WARNING
        global FAST_MAX
        global FAST_WARNING

        SLOW_MAX = common.SLOW_MAX[self.sensitivity]
        SLOW_WARNING = common.SLOW_WARNING[self.sensitivity]
        MID_MAX = common.MID_MAX[self.sensitivity]
        MID_WARNING = common.MID_WARNING[self.sensitivity]
        FAST_MAX = common.FAST_MAX[self.sensitivity]
        FAST_WARNING = common.FAST_WARNING[self.sensitivity]
        
        self.move_serials = moves
        self.tracked_moves = {}
        self.dead_moves = {}
        self.teams = {}
        self.music_speed = Value('d', MID_MUSIC_SPEED)
        self.running = True
        self.force_move_colors = {}
		
        self.start_timer = time.time()
        self.audio_cue = 0
        self.move_opts = {}
        self.update_time = 0
		
        self.num_teams = game_mode.num_teams
		if self.num_teams < 2:
			self.num_teams = len(moves)
		self.generate_random_teams(self.num_teams)
		
		self.init_mode_config()
		
		if self.play_audio:
			self.init_mode_sfx()
            fast_resample = False
            end = False
            try:
                self.audio = music
            except:
                print('no audio loaded')
		self.change_time = time.time() + 6
        self.speed_up = False
		seld.speed_down = False
        self.currently_changing = False
		self.changing_high = False
        self.game_end = False
        self.winning_moves = []
        self.game_loop()
		

	@abstractmethod
	def init_mode_config(self):
		pass

	@abstractmethod
	def init_mode_sfx(self):
		pass
	
    def generate_random_teams(self, num_teams):
        if self.random_teams == False:
            players_per_team = (len(self.move_serials)//num_teams)+1
            team_num = [x for x in range(num_teams)]*players_per_team
            for num,move in zip(team_num,self.move_serials):
                self.teams[move] = num
        else:
            team_pick = list(range(num_teams))
            for serial in self.move_serials:
                random_choice = random.choice(team_pick)
                self.teams[serial] = random_choice
                team_pick.remove(random_choice)
                if not team_pick:
                    team_pick = list(range(num_teams))

    def track_moves(self):
        for move_num, move_serial in enumerate(self.move_serials):
            time.sleep(0.02)
            dead_move = Value('i', 1)
            force_color = Array('i', [1] * 3)
            opts = Array('i', [0] * 5)
            proc = Process(target=track_move, args=(move_serial,
                                                    move_num,
                                                    self.teams[move_serial],
                                                    self.num_teams,
                                                    self.team_colors,
                                                    dead_move,
                                                    force_color,
                                                    self.music_speed,

                                                    opts))
            proc.start()
            self.tracked_moves[move_serial] = proc
            self.dead_moves[move_serial] = dead_move
            self.force_move_colors[move_serial] = force_color
            self.move_opts[move_serial] = opts

    def change_all_move_colors(self, r, g, b):
        for color in self.force_move_colors.values():
            colors.change_color(color, r, g, b)
    def count_down(self):
        self.change_all_move_colors(80, 0, 0)
        if self.play_audio:
            self.start_beep.start_effect()
        time.sleep(0.75)
        self.change_all_move_colors(70, 100, 0)
        if self.play_audio:
            self.start_beep.start_effect()
        time.sleep(0.75)
        self.change_all_move_colors(0, 70, 0)
        if self.play_audio:
            self.start_beep.start_effect()
        time.sleep(0.75)
        self.change_all_move_colors(0, 0, 0)
        if self.play_audio:
            self.start_game.start_effect()
    def get_change_time(self, speed_up, speed_down):
        min_moves = len(self.move_serials) - 2
        if min_moves <= 0:
            min_moves = 1
        
        game_percent = (self.num_dead/min_moves)
        if game_percent > 1.0:
            game_percent = 1.0
        min_music_fast = common.lerp(MIN_MUSIC_FAST_TIME, END_MIN_MUSIC_FAST_TIME, game_percent)
        max_music_fast = common.lerp(MAX_MUSIC_FAST_TIME, END_MAX_MUSIC_FAST_TIME, game_percent)

        min_music_mid = common.lerp(MIN_MUSIC_MID_TIME, END_MIN_MUSIC_MID_TIME, game_percent)
        max_music_mid = common.lerp(MAX_MUSIC_MID_TIME, END_MAX_MUSIC_MID_TIME, game_percent)

        min_music_slow = common.lerp(MIN_MUSIC_SLOW_TIME, END_MIN_MUSIC_SLOW_TIME, game_percent)
        max_music_slow = common.lerp(MAX_MUSIC_SLOW_TIME, END_MAX_MUSIC_SLOW_TIME, game_percent)
        if speed_up == speed_down:
            added_time = random.uniform(min_music_mid, max_music_mid)
        else:
            added_time = random.uniform(min_music_fast if self.changing_high else min_music_slow, \
                                        max_music_fast if self.changing_high else max_music_slow)
        return time.time() + added_time
		
    def change_music_speed(self, fast, slow):
        change_percent = numpy.clip((time.time() - self.change_time)/INTERVAL_CHANGE, 0, 1)
        if fast or slow:
            self.music_speed.value = common.lerp((FAST_MUSIC_SPEED if fast else SLOW_MUSIC_SPEED), MID_MUSIC_SPEED, change_percent)
        else:
            self.changing_high = bool(random.getrandbits(1))
            self.music_speed.value = common.lerp(MID_MUSIC_SPEED, (FAST_MUSIC_SPEED if self.changing_high else SLOW_MUSIC_SPEED), change_percent)
        self.audio.change_ratio(self.music_speed.value)

    def check_music_speed(self):
        if time.time() > self.change_time and time.time() < self.change_time + INTERVAL_CHANGE:
            self.change_music_speed(self.speed_up, self.speed_down)
            self.currently_changing = True
        elif time.time() >= self.change_time + INTERVAL_CHANGE and self.currently_changing:
            self.music_speed.value = MID_MUSIC_SPEED if self.speed_up or self.speed_down else \
                                     (SLOW_MUSIC_SPEED if self.changing_high else FAST_MUSIC_SPEED)
            self.speed_up =  not self.speed_up #need to change this line
            self.change_time = self.get_change_time(speed_up = self.speed_up, speed_down = self.speed_down)
            self.audio.change_ratio(self.music_speed.value)
            self.currently_changing = False

	@abstractmethod
	def check_end_game(self):
		pass

    def stop_tracking_moves(self):
        for proc in self.tracked_moves.values():
            proc.terminate()
            proc.join()
            time.sleep(0.02)


    def end_game(self):
        if self.play_audio:
            try:
                self.audio.stop_audio()
            except:
                print('no audio loaded to stop')
        end_time = time.time() + END_GAME_PAUSE
        h_value = 0
        self.update_status('ending',self.winning_team)
        if self.play_audio:
            self.end_game_sound(self.winning_team)
        while (time.time() < end_time):
            time.sleep(0.01)
            win_color = colors.hsv2rgb(h_value, 1, 1)
            for win_move in self.move_serials:
                if win_move != self.last_move:
                    win_color_array = self.force_move_colors[win_move]
                    colors.change_color(win_color_array, *win_color)
                else:
                    win_color_array = self.force_move_colors[win_move]
                    colors.change_color(win_color_array, 0,0,0)
            h_value = (h_value + 0.01)
            if h_value >= 1:
                h_value = 0
        self.running = False

	@abstractmethod
	def end_game_sound(self, winning_team):
		pass

    def game_loop(self):
        self.track_moves()
		self.mode_setup()
        self.count_down()
        if self.play_audio:
            try:
                self.audio.start_audio_loop()
            except:
                print('no audio loaded to start')
		self.post_audio_setup()
        while self.running:
			#I think the loop is so fast that this causes 
			#a crash if done every loop
			if time.time() - 0.1 > self.update_time:
				self.update_time = time.time()
				self.check_command_queue()
				self.update_status('in_game')
			self.mode_logic()
			self.check_end_game()
			if self.game_end:
				self.end_game()

        self.stop_tracking_moves()
		
	@abstractmethod #maybe?
	def mode_setup(self):
		pass		
		
	@abstractmethod #maybe?
	def post_audio_setup(self):
		pass

	@abstractmethod #maybe?
	def mode_logic(self):
		pass

    def check_command_queue(self):
        package = None
        while not(self.command_queue.empty()):
            package = self.command_queue.get()
            command = package['command']
        if not(package == None):
            if command == 'killgame':
                self.kill_game()
    def update_status(self,game_status,winning_team=-1):
        data ={'game_status' : game_status,
               'game_mode' : 'No Mode',
               'winning_team' : winning_team,
               'current_track': self.audio.get_title()}
        self.ns.status = data
	
	def kill_game(self):
		if self.play_audio:
			try:
				self.audio.stop_audio()
			except:
				print('no audio loaded to stop')        
		self.update_status('killed')
		all_moves = [x for x in self.dead_moves.keys()]
		end_time = time.time() + KILL_GAME_PAUSE     
		
		bright = 255
		while (time.time() < end_time):
			time.sleep(0.01)
			color = (bright,0,0)
			for move in all_moves:
				color_array = self.force_move_colors[move]
				colors.change_color(color_array, *color)
			bright = bright - 1
			if bright < 10:
				bright = 10
		self.running = False
