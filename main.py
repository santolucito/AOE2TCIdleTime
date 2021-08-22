import os
import glob
from typing import ItemsView

from construct.core import Switch
from mgz import header, body

from pprint import pprint

from constants import *
from utils import *
from player import *

SAVEGAMEPATH = "/mnt/c/Users/mark-omi/Games/Age of Empires 2 DE/76561198177849325/savegame"

list_of_files = glob.glob(SAVEGAMEPATH+"/*.aoe2record") 
list_of_files = sorted(list_of_files, key=os.path.getctime)
target_file = list_of_files[-4]
#target_file = SAVEGAMEPATH + "/MP Replay v101.101.50700.0 @2021.07.26 210453 (1).aoe2record"
#target_file = "problem.aoe2record"
players = {}



#TODO how to make this work cross-platform
with open(target_file, 'rb') as data:
    eof = os.fstat(data.fileno()).st_size
    info = header.parse_stream(data)
    for p in info.de.players:
        if (p.type == "human"):
            players[p.player_number] = Player((p.name.value).decode("utf-8"), p.player_number)
            print (players[p.player_number].name + " : " + str(p.player_number))
        elif (p.player_number >= 1):
            print ((p.ai_name.value).decode("utf-8") + " (AI) : " + str(p.player_number))
    body.meta.parse_stream(data)
    
    while data.tell() < eof:
        op = body.operation.parse_stream(data)
        #TODO perhaps a bit inefficient - an action message can only apply to a single player
        for p_num, p_data in players.items():
            if isCastleResearch(op, players, p_num) or players[p_num].clicked_castle == True:
                    players[p_num].clicked_castle = True
                    players[p_num].total_time_until_castle_click = players[p_num].time_elapsed_so_far

            elif (op.type == "action" and not op.action.type_int in [103, 130]): #103, 130 are unknown commands
                if (isVillQueue(op.action, p_num)):
                    players[p_num].tc_id = op.action.building_ids[0]
                production_info_updates = inducedTCWorkTime(op.action, players, p_num)
                players[p_num].tc_work_time += production_info_updates["tc_work_time"]
                players[p_num].num_vills_produced += production_info_updates["vill_production_change"]
                players[p_num].tc_technologies += production_info_updates["new_tech"]

                if isFeudalResearch(op, players, p_num):
                    players[p_num].total_time_until_feudal_click = players[p_num].time_elapsed_so_far 

            elif (op.type == "sync"):
                players[p_num].time_elapsed_so_far += op.time_increment
        
        if bothCastle(players):
            break

        if (op.type == "action" and op.action.type != "move" and False):
            print(op)
            printPlayerDetails()
            wait = input()

    for _, p in players.items():
        printPlayerDetails(p)

