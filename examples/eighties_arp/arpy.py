import time

class Arpy:
    def __init__(self):
        self.enabled = False
        self.root_note = 48
        self.gate_percent = 0.30  # percentage
        self.set_bpm(bpm=100, steps_per_beat=2) # 100 bpm 8th notes
        self.arps = [
            ('major'        , (0, 4, 7, 12) ),    # 0
            ('minor7th'     , (0, 3, 7, 10) ),    # 1
            ('diminished'   , (0, 3, 6, 3)) ,     # 2
            ('suspended4th' , (0, 5, 7, 12) ),    # 3
            ('octaves'      , (0, 12, 0, -12) ),  # 4
            ('octaves2'     , (0, 12, 24, -12) ), # 5
            ('octaves3'     , (0, -12, -12, 0) ), # 6
            ('root'         , (0, 0, 0, 0) ),     # 7
        ]
        self.arp_id = 0  # which one of the arps we're currently using,
        self.arp_user = None  # list of notes if user adds arp  # FIXME
        self.arp_pos = 0
        self.note_on_handler = lambda note,: print("note on standin",note)
        self.note_off_handler = lambda note: print("note off standin", note)
        self.note_played = None  # the note that was played (for note off)
        self.last_beat_time = time.monotonic()
        self.trans_steps = 0
        self.trans_distance = 12
        self.trans_pos = 0

    def set_bpm(self, bpm, steps_per_beat=None):
        self.bpm = bpm
        if steps_per_beat:
            self.steps_per_beat = steps_per_beat
        self.per_beat_time = 60 / bpm / self.steps_per_beat
        self.note_duration = self.gate_percent * self.per_beat_time
        #print("per_beat_time:", self.per_beat_time, self.steps_per_beat)

    def set_transpose(self, distance=12, steps=0):
        self.trans_distance = distance
        self.trans_steps = steps

    def on(self):
        self.enabled = True
        self.last_beat_time = time.monotonic() - self.per_beat_time

    def set_arp(self,arp_id_or_str):
        if type(arp_id_or_str) is str:
            self.arp_id = [name for (name,arp) in self.arps].index(arp_id_or_str)
        else:
            self.arp_id = arp_id_or_str

    def arp_name(self):
        return self.arps[self.arp_id][0]

    def play(self, arp_notes):
        self.arp_user = arp_notes  # FIXME

    def next_arp(self):
        self.arp_id = (self.arp_id + 1) % len(self.arps)

    def update(self):
        if not self.enabled: return
        now = time.monotonic()

        if now - self.last_beat_time >= self.per_beat_time:
            self.last_beat_time = now
            arp = self.arps[self.arp_id][1]

            trans_amount = self.trans_distance * self.trans_pos
            if self.arp_pos == 0:  # only make musical changes at top of arp
                self.trans_pos = (self.trans_pos + 1) % (self.trans_steps+1)

            self.note_played = self.root_note + arp[self.arp_pos] + trans_amount
            self.note_on_handler( self.note_played )
            self.arp_pos = (self.arp_pos+1) % len(arp)

        if now - self.last_beat_time > self.note_duration and self.note_played:
            self.note_off_handler( self.note_played )
            self.note_played = None
