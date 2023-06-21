import time

class Arpy:
    def __init__(self):
        self.enabled = False
        self.root_note = 48
        self.gate_percent = 0.75  # percentage
        self.steps_per_beat = 2  # eighth notes
        self.set_bpm(100)
        self.arps = {
            'major'        : (0, 4, 7, 12),
            'minor7th'     : (0, 3, 7, 10),
            'diminished'   : (0, 3, 6, 3),
            'suspended4th' : (0, 5, 7, 12),
            'octaves'      : (0, 12, 0, -12),
            'octaves2'     : (0, 12, 24, -12),
            'octaves3'     : (0, -12, -12, 0),
            'root'         : (0, 0, 0, 0),
        }
        self.arp_id = 'major'
        self.arp_pos = 0
        self.note_on_handler = lambda note,: print("note on standin",note)
        self.note_off_handler = lambda note: print("note off standin", note)
        self.note_played = None
        self.last_beat_time = time.monotonic()

    def set_bpm(self, bpm):
        self.bpm = bpm
        self.per_beat_time = 60 / bpm / self.steps_per_beat
        self.note_duration = self.gate_percent * self.per_beat_time
        print("per_beat_time:", self.per_beat_time)

    def on(self):
        self.enabled = True
        self.last_beat_time = time.monotonic() - self.per_beat_time

    def update(self):
        if not self.enabled: return
        now = time.monotonic()

        if now - self.last_beat_time > self.per_beat_time:
            self.last_beat_time = now
            arp = self.arps[self.arp_id]
            self.note_played = self.root_note + arp[self.arp_pos]
            self.note_on_handler( self.note_played )
            self.arp_pos = (self.arp_pos+1) % len(arp)

        if now - self.last_beat_time > self.note_duration and self.note_played:
            self.note_off_handler( self.note_played )
            self.note_played = None
