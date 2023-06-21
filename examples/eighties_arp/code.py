# synthio_eighties_arp.py --
# 19 Jun 2023 - @todbot / Tod Kurt
#
import time, random
import board, analogio, audiopwmio, audiomixer, synthio
import ulab.numpy as np
from arpy import Arpy

num_voices = 3       # how many voices for each note
lpf_basef = 2500     # filter lowest frequency
lpf_resonance = 1.5  # filter q

knobA = analogio.AnalogIn(board.A0)
knobB = analogio.AnalogIn(board.A1)

audio = audiopwmio.PWMAudioOut(board.RX)  # RX pin on QTPY RP2040
#audio = audiobusio.I2SOut(bit_clock=board.MOSI, word_select=board.MISO, data=board.SCK)

mixer = audiomixer.Mixer(channel_count=1, sample_rate=28000, buffer_size=2048)
synth = synthio.Synthesizer(channel_count=1, sample_rate=28000)
audio.play(mixer)
mixer.voice[0].play(synth)
mixer.voice[0].level = 0.8

# our oscillator waveform, a 512 sample downward saw wave going from 25k to -25k
wave_saw = np.linspace(25000, -25000, num=512, dtype=np.int16)  # max is +/-32k but gives us headroom
amp_env = synthio.Envelope(attack_level=1, sustain_level=1, release_time=0.5)

voices=[]  # holds our currently sounding voices ('Notes' in synthio speak)

def note_on(n):
    print("my note on ", n)
    fo = synthio.midi_to_hz(n)
    voices.clear()  # delete any old voices
    for i in range(num_voices):
        f = fo * (1 + i*0.007)
        lpf_f = fo * 8  # a kind of key tracking
        lpf = synth.low_pass_filter( lpf_f, lpf_resonance )
        voices.append( synthio.Note( frequency=f, filter=lpf, envelope=amp_env, waveform=wave_saw) )
    synth.press(voices)

def note_off(n):
    print("my note off", n)
    synth.release(voices)

# simple range mapper, like Arduino map()
def map_range(s, a1, a2, b1, b2): return  b1 + ((s - a1) * (b2 - b1) / (a2 - a1))

arpy = Arpy()
arpy.note_on_handler = note_on
arpy.note_off_handler = note_off
arpy.on()

arpy.root_note = 37
arpy.arp_id = 'suspended4th'
#arpy.arp_id = 'root'
arpy.set_bpm(110)
arpy.set_transpose(distance=12, steps=1)

knobfilter = 0.5
knobAval = knobA.value
knobBval = knobB.value

while True:
    # filter noisy adc
    knobAval = knobAval * knobfilter + (1-knobfilter) * knobA.value
    knobBval = knobBval * knobfilter + (1-knobfilter) * knobB.value

    arpy.root_note = int(map_range( knobAval, 0,65535, 24, 72) )
    arpy.set_bpm( map_range(knobBval, 0,65535, 40, 180 ) )
    arpy.update()
