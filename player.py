
class Player:
    def __init__(self, name, player_id):
        self.name = name
        self.player_id = player_id
        self.tc_id = 0
        self.clicked_castle = False
        self.num_vills_produced = 0
        self.tc_work_time = 0
        self.total_time_until_castle_click = 0
        self.total_time_until_feudal_click = 0
        self.precastle_work_time = 0
        self.prefeudal_work_time = 0

