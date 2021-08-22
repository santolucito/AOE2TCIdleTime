
class Player:
    def __init__(self, name, player_number):
        self.name = name
        self.player_number = player_number
        self.tc_id = 0
        self.clicked_castle = False
        self.tc_technologies = []
        self.num_vills_produced = 0
        self.tc_work_time = 0
        self.time_elapsed_so_far = 0
        self.total_time_until_castle_click = 0
        self.total_time_until_feudal_click = 0
        self.precastle_work_time = 0
        self.prefeudal_work_time = 0

def printPlayerDetails(p):
    print (p.tc_id)
    print ("vills: " + str(p.num_vills_produced))
    print ("techs: " + str(p.tc_technologies))
    print ("tc work time: " + str(p.tc_work_time/1000))
    print ("clicked castle: " + str(p.clicked_castle))
    print ("total elapsed time: " + str(p.time_elapsed_so_far/1000))
    print("pre-castle effective idle time ("+p.name+"): " + str((p.time_elapsed_so_far - p.tc_work_time)/1000))
