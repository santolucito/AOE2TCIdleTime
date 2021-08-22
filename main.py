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
#latest_file = max(list_of_files, key=os.path.getctime)
#latest_file = SAVEGAMEPATH + "/MP Replay v101.101.50700.0 @2021.07.26 210453 (1).aoe2record"
latest_file = "problem.aoe2record"
players = {}

#TODO how to make this work cross-platform
with open(latest_file, 'rb') as data:
    eof = os.fstat(data.fileno()).st_size
    info = header.parse_stream(data)
    for p in  info.de.players:
        if (p.type == "human"):
            players[p.player_number] = Player((p.name.value).decode("utf-8"), p.player_number)
            print (players[p.player_number].name + " : " + str(p.player_number))
    body.meta.parse_stream(data)
    
    tc_work_time = 0
    while data.tell() < eof:
        op = body.operation.parse_stream(data)
        #TODO perhaps a bit inefficient - an action message can only apply to a single player
        for i, p in players.items():
            if isCastleResearch(op, players, p.player_id):
                players[i].feudal_time = players[i].total_time_until_castle_click 
            elif isCastleResearch(op, players, p.player_id):
                players[i].clicked_castle = True
            elif (op.type == "action" and not op.action.type_int in [103, 130]): #103, 130 are unknown commands
                if (isVillQueue(op.action, p.player_id)):
                    players[p.player_id].tc_id = op.action.building_ids[0]
                production_updates = inducedTCWorkTime(op.action, players, p.player_id)
                players[i].tc_work_time += production_updates["tc_work_time"]
                players[i].num_vills_produced += production_updates["vill_production_change"]
            elif (op.type == "sync"):
                players[i].total_time_until_castle_click += op.time_increment
        both_castle = True
        for i, p in players.items():
            both_castle = both_castle and p.clicked_castle
        if both_castle:
            break

    for k, p in players.items():
        pprint (p.tc_id)
        pprint (p.num_vills_produced)
        pprint (p.tc_work_time)
        pprint (p.total_time_until_castle_click)
        pprint (p.clicked_castle)
        print("pre-castle effective idle time ("+p.name+"): " + str((p.total_time_until_castle_click - p.tc_work_time)/1000))

