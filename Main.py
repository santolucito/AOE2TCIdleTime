import os
import glob
from typing import ItemsView

from construct.core import Switch
from mgz import header, body

from pprint import pprint

SAVEGAMEPATH = "/mnt/c/Users/mark-omi/Games/Age of Empires 2 DE/76561198177849325/savegame"

list_of_files = glob.glob(SAVEGAMEPATH+"/*.aoe2record") 
latest_file = max(list_of_files, key=os.path.getctime)
#latest_file = SAVEGAMEPATH + "/MP Replay v101.101.50700.0 @2021.07.26 210453 (1).aoe2record"
players = {}

class Player:
    def __init__(self, name, player_id):
        self.name = name
        self.player_id = player_id
        self.total_time_until_castle_click = 0
        self.tc_work_time = 0
        self.tc_id = 0
        self.clicked_castle = False
        self.num_vills_produced = 0

VILL_ID = 83 #ids pulled from test runs and manual inspection of parsed save file TODO is there a better way?
VILL_TIME = 25000 #in ms, pulled from aoe2 wiki

LOOM_ID = 22
LOOM_TIME = 25000

WHEELBARROW_ID = 213
WHEELBARROW_TIME = 75000

TOWNWATCH_ID = 8
TOWNWATCH_TIME = 25000

FEUDAL_ID = 101
FEUDAL_TIME = 130000

CASTLE_ID = 102

ID_INFO = dict([(VILL_ID, VILL_TIME),
                (LOOM_ID, LOOM_TIME),
                (WHEELBARROW_ID, WHEELBARROW_TIME),
                (TOWNWATCH_ID, TOWNWATCH_TIME),
                (FEUDAL_ID, FEUDAL_TIME)
                ])
                


#TODO would like to only set to true when castle research actually starts (rather than just being queued)
#to do this, we need to keep track of when each item queued actually completes
#we are essentially rebuilding a tiny portion of the game engine by doing this
def isCastleResearch(op, p_id):
    return ((op.type == "action" and 
           op.action.type == "research" and
           op.action.technology_type == FEUDAL_ID and
           op.action.player_id == p_id)
           or
           players[p_id].clicked_castle)

def isVillQueue(action, p_id):
    global players
    if action.type == "de_queue" and action.unit_type == VILL_ID and action.player_id == p_id:
        players[p_id].tc_id = action.building_ids[0]
        return True
    else:
        return False

#TODO use the action.cancelOrder to keep track of what is being dequeued. this requires simulating exit times for queue items.
# right now we assume dequeuing is always dequeueing a vill (which also works for loom and townwatch b/c they take the same time)
# since we are only working pre-castle age, the only things we need to worry about are dequeuing wheelbarrow and feudal age (which doesn't usually happen)
# this info is not relevant to "effective" idle time calculations, but necessary for overall idle time
#TODO dequeue actions are not tagged with player number, only building id.
# need to keep track of which buildings belong to which player, then use that to tie dequeue buildings to a player
def isVillDequeue(action, p_id):
    return action.type == "order" and action.building_id == -1 and players[p_id].tc_id in action.unit_ids

def isTCResearch(action, p_id):
    return action.type == "research" and action.building_id == players[p_id].tc_id

def tcResearchTime(action):
    return ID_INFO[action.technology_type]



# to calculate tc work time, add up the build time for everything queued, and substract the build time of everything dequeued
# this assumes dequeuing a partially completed items (vills or research) should count as idle time
# e.g. queue a vill for 15 seconds, then cancelling that vill before it is completed means your tc was effectively idle for 15 seconds.
def inducedTCWorkTime(action, p_id):
    global players
    tc_work_time = 0
    if isVillQueue(action, p_id):        
        if (action.queue_amount > 1):
            print("Player "+str(p_id)+" MULTIQUE'D: " + str(action.queue_amount))
            # seems like maybe there is an issue with multiqueuing?
        players[p_id].num_vills_produced += action.queue_amount
        tc_work_time = VILL_TIME * action.queue_amount
        if (p_id == 2):
            print(players[p_id].num_vills_produced)
            #print(action)
    elif isVillDequeue(action, p_id):
        if (int.from_bytes([action.flags[0]], "little") == 1): #indicates if shift+dequeue was pressed
            tc_work_time -= VILL_TIME * 5
        else: 
            tc_work_time -= VILL_TIME
            players[p_id].num_vills_produced -= 1
    elif isTCResearch(action, p_id):
        if (p_id == 2):
            print(action)
        tc_work_time = tcResearchTime(action)
    return tc_work_time

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
            if isCastleResearch(op, p.player_id):
                players[i].clicked_castle = True
            elif (op.type == "action" and not op.action.type_int in [103, 130]): #103, 130 are unknown commands
                if (isVillQueue(op.action, p.player_id) and p.player_id ==2):
                    print(op)
                players[i].tc_work_time += inducedTCWorkTime(op.action, p.player_id)
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

