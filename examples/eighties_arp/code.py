# synthio_eighties_arp.py --
# 19 Jun 2023 - @todbot / Tod Kurt
#
import time, random
import board, audiopwmio, audiomixer, synthio
import ulab.numpy as np
from arpy import Arpy

num_voices = 3       # how many voices for each note
lpf_basef = 2500     # filter lowest frequency
lpf_resonance = 1.5  # filter q

audio = audiopwmio.PWMAudioOut(board.RX)  # RX pin on QTPY RP2040
#audio = audiobusio.I2SOut(bit_clock=board.MOSI, word_select=board.MISO, data=board.SCK)

mixer = audiomixer.Mixer(channel_count=1, sample_rate=22050, buffer_size=2048)
synth = synthio.Synthesizer(channel_count=1, sample_rate=22050)
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
        f = fo * (1 + i*0.01)
        lpf_f = fo * 8  # a kind of key tracking
        filter = synth.low_pass_filter( lpf_f, lpf_resonance )
        voices.append( synthio.Note( frequency=f, filter=filter, envelope=amp_env, waveform=wave_saw) )
    synth.press(voices)

def note_off(n):
    print("my note off", n)
    synth.release(voices)

arpy = Arpy()
arpy.note_on_handler = note_on
arpy.note_off_handler = note_off
arpy.on()

arpy.root_note = 37
arpy.arp_id = 'octaves2'
arpy.set_bpm(110)

while True:
    arpy.update()
