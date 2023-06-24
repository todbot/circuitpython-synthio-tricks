# monosynth1_synthio.py -- partial synthio port of 'monosynth1' from mozzi_experiments
# 22 Jun 2023 - @todbot / Tod Kurt
# part of https://github.com/todbot/circuitpython-synthio-tricks
#
# Responds to these USB MIDI messages:
# - note on / off
# - filter cutoff      -- CC 74
# - filter resonance   -- CC 71
# - env release time   -- CC 72 / CC 18
# - osc detune amount  -- CC 93
# - pitch vibrato      -- CC 1 (modwheel)
#

import time,random
import board
import audiomixer, audiopwmio
import synthio
import ulab.numpy as np

import usb_midi
import adafruit_midi  # circup install adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
import neopixel   # circup install neopixel

oscs_per_note = 3      # how many oscillators for each note
osc_detune = 0.001     # how much to detune oscillators for phatness
filter_freq_lo = 100   # filter lowest freq
filter_freq_hi = 4500  # filter highest freq
filter_res_lo = 0.5    # filter q lowest value
filter_res_hi = 2.0    # filter q highest value
vibrato_lfo_hi = 0.1   # vibrato amount when modwheel is maxxed out
vibrato_rate = 5       # vibrato frequency

led = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)
midi = adafruit_midi.MIDI(midi_in=usb_midi.ports[0], in_channel=0 )

# set up the audio system, mixer, and synth
audio = audiopwmio.PWMAudioOut(board.RX)  # RX pin on QTPY RP2040
mixer = audiomixer.Mixer(channel_count=1, sample_rate=28000, buffer_size=2048)
synth = synthio.Synthesizer(channel_count=1, sample_rate=28000)
audio.play(mixer)
mixer.voice[0].play(synth)
mixer.voice[0].level = 0.75

# our oscillator waveform, a 512 sample downward saw wave going from +/-28k
wave_saw = np.linspace(28000, -28000, num=512, dtype=np.int16)  # max is +/-32k but gives us headroom
lfo_vibrato = synthio.LFO(rate=vibrato_rate, scale=0.01 ) # scale set with modwheel

oscs = []   # holds currently sounding oscillators
filter_freq = 2000  # current setting of filter
filter_res = 1.0    # current setting of filter
amp_env_release_time = 0.8  # current release time
note_played = 0  # current note playing

# simple range mapper, like Arduino map()
def map_range(s, a1, a2, b1, b2): return  b1 + ((s - a1) * (b2 - b1) / (a2 - a1))

# midi note on
def note_on(notenum, vel):
    amp_level = map_range(vel, 0,127, 0,1)
    amp_env = synthio.Envelope(attack_time=0.1, decay_time=0.05,
                               release_time=amp_env_release_time,
                               attack_level=amp_level, sustain_level=amp_level*0.8)
    f = synthio.midi_to_hz(notenum)
    oscs.clear()  # chuck out old oscs to make new ones
    for i in range(oscs_per_note):
        fr = f * (1 + (osc_detune*i))
        lpf = synth.low_pass_filter(filter_freq, filter_res)
        # in synthio, 'Note' objects are more like oscillators
        oscs.append( synthio.Note( frequency=fr, filter=lpf, envelope=amp_env,
                                   waveform=wave_saw, bend=lfo_vibrato) )
    synth.press(oscs)  # press the 'note' (collection of oscs acting in concert)

# midi note off
def note_off(notenum,vel):
    synth.release(oscs)
    oscs.clear()


print("monosynth1 ready, listening to incoming USB MIDI")

while True:

    # to do global filtermod we must iterate over all oscillators in each note
    for osc in oscs:
        osc.filter = synth.low_pass_filter( filter_freq, filter_res )

    msg = midi.receive()
    if isinstance(msg, NoteOn) and msg.velocity != 0:
        print("noteOn: ", msg.note, "vel=", msg.velocity)
        led.fill(0xff00ff)
        note_off( note_played, 0 )  # this is a monosynth, so if they play legato, noteoff!
        note_on(msg.note, msg.velocity)
        note_played = msg.note

    elif isinstance(msg,NoteOff) or isinstance(msg,NoteOn) and msg.velocity==0:
        print("noteOff:", msg.note, "vel=", msg.velocity)
        if msg.note == note_played:  # only release note that's sounding
            led.fill(0x00000)
            note_off(msg.note, msg.velocity)

    elif isinstance(msg,ControlChange):
        print("CC", msg.control, "=", msg.value)
        if msg.control == 1:  # mod wheel
            lfo_vibrato.scale = map_range(msg.value, 0,127, 0, vibrato_lfo_hi)
        elif msg.control == 74: # filter cutoff
            filter_freq = map_range( msg.value, 0,127, filter_freq_lo, filter_freq_hi)
        elif msg.control == 71: # filter resonance
            filter_res = map_range( msg.value, 0,127, filter_res_lo, filter_res_hi)
        elif msg.control == 72 or msg.control == 18: # env release time
            amp_env_release_time = map_range( msg.value, 0,127, 0.1, 1)
        elif msg.control == 93:  # 'chorus' amount (detune amount)
            osc_detune = map_range( msg.value, 0,127, 0, 0.01)
