from enum import Enum
from math import sqrt
from multiprocessing import Process, Value, Array
from piaudio import Audio
import common, colors
import numpy
import psmove
import random
import time

def calculate_flash_time(r,g,b, score):
def track_move(move_serial, move_num, team, num_teams, team_colors, dead_move, force_color, music_speed, move_opts):
class Game_mode():
	def __init__(self, moves, command_queue, ns, music):#Joust has teams and game_mode init vars
	def generate_random_teams(self, num_teams):
	def track_moves(self):
	def change_all_move_colors(self, r, g, b):
	def count_down(self):
	def get_change_time(self, speed_up):
	def change_music_speed(self, fast):
	def check_music_speed(self):
	def check_end_game(self):
	def stop_tracking_moves(self):
	def end_game(self):
	def end_game_sound(self, winning_team):
	def game_loop(self):
	def check_command_queue(self):
	def update_status(self,game_status,winning_team=-1):
	def kill_game(self):
