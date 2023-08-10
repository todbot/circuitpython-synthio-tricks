# wavetable_midisynth_code.py -- simple wavetable synth that responds to MIDI
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
