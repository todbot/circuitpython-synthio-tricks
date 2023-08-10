# wavetable_synth_code.py --
# 26 Jul 2023 - @todbot / Tod Kurt
#
# Demonstrate using wavetables to make a MIDI synth
#
# Needs WAV files from waveeditonline.com
# - BRAIDS02.WAV - http://waveeditonline.com/index-17.html
#
# External libraries needed:
# - adafruit_wave  - circup install adafruit_wave
# - adafruit_midi  - circup install adafruit_midi
#
# Pins used on QTPY RP2040:
# - board.SCK - Audio PWM output (needs RC filter output)
#
# For an I2S version of this using Pico and I2S DAC, see code_i2s.py
#

import board, time, audiopwmio, audiomixer, synthio
import ulab.numpy as np
import adafruit_wave

import usb_midi
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff

midi_channel = 1
wavetable_fname = "wav/PLAITS02.WAV" # from http://waveeditonline.com/index-17.html
wavetable_sample_size = 256
sample_rate = 28000
wave_lfo_min = 10
wave_lfo_max = 25

midi_usb  = adafruit_midi.MIDI(midi_in=usb_midi.ports[0], in_channel=midi_channel-1)

audio = audiopwmio.PWMAudioOut(board.MOSI)
mixer = audiomixer.Mixer(buffer_size=4096, voice_count=1, sample_rate=sample_rate, channel_count=1,
                         bits_per_sample=16, samples_signed=True)
audio.play(mixer) # attach mixer to audio playback
synth = synthio.Synthesizer(sample_rate=sample_rate)
mixer.play(synth) # attach synth to mixer

# mix between values a and b, works with numpy arrays too,  t ranges 0-1
def lerp(a, b, t):  return (1-t)*a + t*b

class Wavetable:
    """ A 'waveform' for synthio.Note that uses a wavetable w/ a scannable wave position."""
    def __init__(self, filepath, wave_len=256):
        self.w = adafruit_wave.open(filepath)
        print("w", self.w.getsampwidth(), self.w.getnchannels(), self.w.getnframes())
        self.wave_len = wave_len  # how many samples in each wave
        if self.w.getsampwidth() != 2 or self.w.getnchannels() != 1:
            raise ValueError("unsupported WAV format")
        self.waveform = np.zeros(wave_len, dtype=np.int16)  # empty buffer we'll copy into
        self.num_waves = self.w.getnframes() // self.wave_len
        self.set_wave_pos(0)

    def set_wave_pos(self, pos):
        """Pick where in wavetable to be, morphing between waves"""
        pos = min(max(pos, 0), self.num_waves-1)  # constrain
        samp_pos = int(pos) * self.wave_len  # get sample position
        self.w.setpos(samp_pos)
        waveA = np.frombuffer(self.w.readframes(self.wave_len), dtype=np.int16)
        self.w.setpos(samp_pos + self.wave_len)  # one wave up
        waveB = np.frombuffer(self.w.readframes(self.wave_len), dtype=np.int16)
        pos_frac = pos - int(pos)  # fractional position between wave A & B
        self.waveform[:] = lerp(waveA, waveB, pos_frac) # mix waveforms A & B


wavetable1 = Wavetable(wavetable_fname, wave_len=wavetable_sample_size)

amp_env = synthio.Envelope(sustain_level=0.8, attack_time=0.03, release_time=0.4)
wave_lfo = synthio.LFO(rate=0.1, waveform=np.array((0,32767), dtype=np.int16) )
lpf = synth.low_pass_filter(4000, 0.5)  # cut some of the annoying harmonics

synth.blocks.append(wave_lfo)  # attach wavelfo to global lfo runner since not attached to note

notes_pressed = {}  # keys = midi note num, value = synthio.Note,

def note_on(notenum, vel):
    # release old note at this notenum if present
    if oldnote := notes_pressed.pop(notenum, None):
        print("oldnote", oldnote, notes_pressed)
        synth.release(oldnote)

    f = synthio.midi_to_hz(notenum)
    note = synthio.Note( frequency=f, waveform=wavetable1.waveform, envelope=amp_env, filter=lpf )
    synth.press(note)
    notes_pressed[notenum] = note

def note_off(notenum,vel):
    if note := notes_pressed.pop(notenum, None):
        synth.release(note)

last_update_time = 0
def update_synth():
    global last_update_time
    # only update 100 times a sec to lighten the load
    if time.monotonic() - last_update_time > 0.01:
       last_update_time = time.monotonic()
       print( wave_lfo.value )
       wavetable1.set_wave_pos( wave_lfo.value )

def set_wave_lfo_minmax(wmin, wmax):
    scale = (wmax - wmin)
    wave_lfo.scale = scale
    wave_lfo.offset = wmin

set_wave_lfo_minmax(wave_lfo_min, wave_lfo_max)

print("wavetable simplesynth")

while True:
    msg = midi_usb.receive()

    update_synth()

    if isinstance(msg, NoteOn) and msg.velocity != 0:
        print("noteOn: ", msg.note, "vel=", msg.velocity)
        note_on(msg.note, msg.velocity)

    elif isinstance(msg,NoteOff) or isinstance(msg,NoteOn) and msg.velocity==0:
        print("noteOff:", msg.note, "vel=", msg.velocity)
        note_off(msg.note, msg.velocity)


###############################################################################

# simpletouchsynth_code.py -- simple touchpad synth, touch pads more to move filter freq
# 12 Jul 2023 - @todbot / Tod Kurt
# part of https://github.com/todbot/qtpy_synth
#
# Needed libraries to install:
#  circup install asyncio neopixel adafruit_debouncer adafruit_displayio_ssd1306 adafruit_display_text adafruit_midi
#

import asyncio
import time
import random
import synthio
import ulab.numpy as np

import displayio, terminalio, vectorio
from adafruit_display_text import bitmap_label as label

import usb_midi
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange

from qtpy_synth import QTPySynthHardware

class SynthConfig():
    def __init__(self):
        self.filter_type = 'lpf'
        self.filter_f = 2000
        self.filter_q = 1.2
        self.filter_mod = 0

qts = QTPySynthHardware()
cfg = SynthConfig()

touch_midi_notes = [40, 48, 52, 60] # can be float
notes_playing = {}  # dict of notes currently playing

# let's get the midi going
midi_usb = adafruit_midi.MIDI(midi_in=usb_midi.ports[0], in_channel=0 )
midi_uart = adafruit_midi.MIDI(midi_in=qts.midi_uart, in_channel=0 )

# set up some default synth parameters
wave_saw = np.linspace(30000,-30000, num=512, dtype=np.int16)  # default squ is too clippy, should be 3dB down or so
amp_env = synthio.Envelope(sustain_level=0.8, release_time=0.6, attack_time=0.001)
qts.synth.envelope = amp_env

# set up display with our 3 chunks of info
disp_group = displayio.Group()
qts.display.root_group = disp_group

labels_pos = ( (5,5), (50,5), (100,5), (15,50) )  #  filter_f, filter_type, filter_q,  hellotext
disp_info = displayio.Group()
for (x,y) in labels_pos:
    disp_info.append( label.Label(terminalio.FONT, text="-", x=x, y=y) )
disp_group.append(disp_info)
disp_info[3].text = "simpletouchsynth"

def map_range(s, a1, a2, b1, b2):  return  b1 + ((s - a1) * (b2 - b1) / (a2 - a1))

def display_update():
    f_str = "%4d" % (cfg.filter_f + cfg.filter_mod)
    q_str = "%1.1f" % cfg.filter_q

    if f_str != disp_info[0].text:
        disp_info[0].text = f_str

    if cfg.filter_type != disp_info[1].text:
        disp_info[1].text = cfg.filter_type

    if q_str != disp_info[2].text:
        disp_info[2].text = q_str
        print("edit q", q_str)

def note_on( notenum, vel=64):
    print("note_on", notenum, vel)
    cfg.filter_mod = (vel/127) * 1500
    f = synthio.midi_to_hz(notenum)
    note = synthio.Note( frequency=f, waveform=wave_saw, filter=make_filter() )
    notes_playing[notenum] = note
    qts.synth.press( note )
    qts.led.fill(0xff00ff)

def note_off( notenum, vel=0):
    print("note_off", notenum, vel)
    if note := notes_playing[notenum]:
        qts.synth.release( note )
    qts.led.fill(0)

# how to do this
def touch_hold(i,v):  # callback
    vn = min(max(0, v), 2000)  # ensure touch info stays positive
    cfg.filter_mod  =  (vn/2000) * 3000   # range 0-3000
    print("hold %d %d %d" % (i,vn, cfg.filter_mod))

filter_types = ['lpf', 'hpf', 'bpf']

def make_filter():
    freq = cfg.filter_f + cfg.filter_mod
    if cfg.filter_type == 'lpf':
        filter = qts.synth.low_pass_filter(freq, cfg.filter_q)
    elif cfg.filter_type == 'hpf':
        filter = qts.synth.high_pass_filter(freq, cfg.filter_q)
    elif cfg.filter_type == 'bpf':
        filter = qts.synth.band_pass_filter(freq, cfg.filter_q)
    else:
        print("unknown filter type", cfg.filter_type)
    return filter


# --------------------------------------------------------

async def display_updater():
    while True:
        print("knobs:", int(qts.knobA//255), int(qts.knobB//255),
            #qts.touchins[0].raw_value, qts.touchins[1].raw_value,
            #qts.touchins[3].raw_value, qts.touchins[2].raw_value
        )
        display_update()
        await asyncio.sleep(0.1)

async def input_handler():
    while True:
        (knobA, knobB) = qts.read_pots()

        if key := qts.check_key():
            if key.pressed:
                ftpos = (filter_types.index(cfg.filter_type)+1) % len(filter_types)
                cfg.filter_type = filter_types[ ftpos ]

        if touches := qts.check_touch():
            for touch in touches:
                if touch.pressed: note_on( touch_midi_notes[touch.key_number] )
                if touch.released: note_off( touch_midi_notes[touch.key_number] )

        qts.check_touch_hold(touch_hold)

        cfg.filter_f = map_range( knobA, 0,65535, 30, 8000)
        cfg.filter_q = map_range( knobB, 0,65535, 0.1, 3.0)

        await asyncio.sleep(0.01)

async def synth_updater():
    # for any notes playing, adjust its filter in realtime
    while True:
        for n in notes_playing.values():
            if n:
                n.filter = make_filter()
        await asyncio.sleep(0.01)

async def midi_handler():
    while True:
        while msg := midi_usb.receive() or midi_uart.receive():
            if isinstance(msg, NoteOn) and msg.velocity != 0:
                note_on(msg.note, msg.velocity)
            elif isinstance(msg,NoteOff) or isinstance(msg,NoteOn) and msg.velocity==0:
                note_off(msg.note, msg.velocity)
        await asyncio.sleep(0.001)

print("-- qtpy_synth simpletouchsynth ready --")

async def main():
    task1 = asyncio.create_task(display_updater())
    task2 = asyncio.create_task(input_handler())
    task3 = asyncio.create_task(synth_updater())
    task4 = asyncio.create_task(midi_handler())
    await asyncio.gather(task1,task2,task3,task4)

asyncio.run(main())
