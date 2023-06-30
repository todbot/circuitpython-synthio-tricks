# synthio_tiny_lfo_song_picoadk.py -- tiny "song" made with just LFOs in synthio for PicoADK board
# 29 May 2023 - @todbot / Tod Kurt
# video demo: https://youtu.be/WBqk-VfTb0o
# requires CircuitPython 8.2.0-beta0 or later
# Uses standard Raspberry Pi Pico CircuitPython build

import time, random
import board, digitalio, audiobusio, audiomixer, synthio, rainbowio
import ulab.numpy as np
import neopixel

# PicoADK board: LED, PCM5100 mute pin, and I2S audio
led = neopixel.NeoPixel(board.GP15, 1, brightness=0.1)

mute_pin = digitalio.DigitalInOut(board.GP25)
mute_pin.switch_to_output(value=True)

audio = audiobusio.I2SOut(bit_clock=board.GP17, word_select=board.GP18, data=board.GP16)
# PicoADK board end

# normally we run
synth = synthio.Synthesizer(channel_count=1, sample_rate=28000)
audio.play(synth)

# we like sawtooth waves better than default square
wave_saw = np.linspace(30000, -30000, num=512, dtype=np.int16)  # max is +/-32k but gives us headroom

lfo_tremo1 = synthio.LFO(rate=3)  # 3 Hz for fastest note
lfo_tremo2 = synthio.LFO(rate=2)  # 2 Hz for middle note
lfo_tremo3 = synthio.LFO(rate=1)  # 1 Hz for lower note
lfo_tremo4 = synthio.LFO(rate=0.75) # 0.75 Hz for lowest bass note

def do_notes(midi_note):
    note1 = synthio.Note( synthio.midi_to_hz(midi_note+0), amplitude=lfo_tremo1, waveform=wave_saw)
    note2 = synthio.Note( synthio.midi_to_hz(midi_note-7), amplitude=lfo_tremo2, waveform=wave_saw)
    note3 = synthio.Note( synthio.midi_to_hz(midi_note-12), amplitude=lfo_tremo3,waveform=wave_saw)
    note4 = synthio.Note( synthio.midi_to_hz(midi_note-24), amplitude=lfo_tremo4, waveform=wave_saw)
    synth.release_all_then_press( (note1, note2, note3, note4) )
    for lfo in (lfo_tremo1,lfo_tremo2,lfo_tremo3,lfo_tremo4):
        lfo.retrigger()

start_note = 65
song_notes = (start_note+0, start_note+5, start_note-3)
i=0
last_time = 0
while True:
    r = (1+lfo_tremo4.value) * 127
    b = (1+lfo_tremo3.value) * 127
    led.fill( (r, 0, b)  )  # make LED track LFO state, for two of the LFOs
    if time.monotonic() - last_time > 8:
        last_time = time.monotonic()
        print("hi, we're just groovin",i)
        do_notes(song_notes[i])
        i= (i+1) % len(song_notes)
