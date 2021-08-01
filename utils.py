from constants import *

class Player:
    def __init__(self, name, player_id):
        self.name = name
        self.player_id = player_id
        self.total_time_until_castle_click = 0
        self.tc_work_time = 0
        self.tc_id = 0
        self.clicked_castle = False
        self.num_vills_produced = 0

#TODO would like to only set to true when castle research actually starts (rather than just being queued)
#to do this, we need to keep track of when each item queued actually completes
#we are essentially rebuilding a tiny portion of the game engine by doing this
def isCastleResearch(op, players, p_id):
    return ((op.type == "action" and 
           op.action.type == "research" and
           op.action.technology_type == FEUDAL_ID and
           op.action.player_id == p_id)
           or
           players[p_id].clicked_castle)

def isVillQueue(action, p_id):
    if action.type == "de_queue" and action.unit_type == VILL_ID and action.player_id == p_id:
        return True
    else:
        return False

#TODO use the action.cancelOrder to keep track of what is being dequeued. this requires simulating exit times for queue items.
# right now we assume dequeuing is always dequeueing a vill (which also works for loom and townwatch b/c they take the same time)
# since we are only working pre-castle age, the only things we need to worry about are dequeuing wheelbarrow and feudal age (which doesn't usually happen)
# this info is not relevant to "effective" idle time calculations, but necessary for overall idle time
#TODO dequeue actions are not tagged with player number, only building id.
# need to keep track of which buildings belong to which player, then use that to tie dequeue buildings to a player
def isVillDequeue(action, p_id, tc_id):
    return action.type == "order" and action.building_id == -1 and tc_id in action.unit_ids

def isTCResearch(action, p_id, tc_id):
    return action.type == "research" and action.building_id == tc_id 

def tcResearchTime(action):
    return ID_INFO[action.technology_type]



# to calculate tc work time, add up the build time for everything queued, and substract the build time of everything dequeued
# this assumes dequeuing a partially completed items (vills or research) should count as idle time
# e.g. queue a vill for 15 seconds, then cancelling that vill before it is completed means your tc was effectively idle for 15 seconds.
def inducedTCWorkTime(action, players, p_id):
    tc_work_time = 0
    vill_production_change = 0
    if isVillQueue(action, p_id):        
        if (action.queue_amount > 1):
            print("Player "+str(p_id)+" MULTIQUE'D: " + str(action.queue_amount))
        vill_production_change += action.queue_amount
        tc_work_time = VILL_TIME * action.queue_amount
    elif isVillDequeue(action, p_id, players[p_id].tc_id):
        if (int.from_bytes([action.flags[0]], "little") == 1): #indicates if shift+dequeue was pressed
            tc_work_time -= VILL_TIME * 5
        else: 
            tc_work_time -= VILL_TIME
            vill_production_change -= 1
    elif isTCResearch(action, p_id, players[p_id].tc_id):
        if (p_id == 2):
            print(action)
        tc_work_time = tcResearchTime(action)
    return {"tc_work_time": tc_work_time,
            "vill_production_change": vill_production_change}

