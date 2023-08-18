# falling_forever_i2s_code.py -- you're falling... falling...
# 26 Jul 2023 - @todbot / Tod Kurt
#
# Demonstrate using wavetables to make interesting sounds.
# This sketch creates two Wavetables, attaches them to two
# synthio.Notes, and uses opposite-polarity LFOs to pitch bend
# each note in opposite directions, all while scanning through
# the wavetables at a rate unsync'd with the LFOs.
#
# Needs two WAV files from waveeditonline.com
# - BRAIDS02.WAV - http://waveeditonline.com/index-17.html
# - HARMONIO.WAV - http://waveeditonline.com/index.html
#
# External libraries needed:
# - adafruit_wave  - circup install adafruit_wave
#
# Pins used on Raspberry Pi Pico:
# - GP9 - I2S BCK
# - GP10 - I2S LRCK
# - GP11 - IS2 DIN
#
# For a PWM version of this using QTPy RP2040 and PWM audio, see code.py
#

import board, time, audiobusio, synthio
import ulab.numpy as np
import adafruit_wave

i2s_bclk, i2s_wsel, i2s_data = board.GP9, board.GP10, board.GP11
audio = audiobusio. I2SOut(bit_clock=i2s_bclk, word_select=i2s_wsel, data=i2s_data)
synth = synthio.Synthesizer(sample_rate=28672)  # 28 * 1024
audio.play(synth)

# mix between values a and b, works with numpy arrays too,  t ranges 0-1
def lerp(a, b, t):  return (1-t)*a + t*b

class Wavetable:
    """ A 'waveform' for synthio.Note that uses a wavetable w/ a scannable wave position."""
    def __init__(self, filepath, wave_len=256):
        self.w = adafruit_wave.open(filepath)
        self.wave_len = wave_len  # how many samples in each wave
        if self.w.getsampwidth() != 2 or self.w.getnchannels() != 1:
            raise ValueError("unsupported WAV format")
        self.waveform = np.zeros(wave_len, dtype=np.int16)  # empty buffer we'll copy into
        self.num_waves = self.w.getnframes() // self.wave_len
        self.set_wave_pos(0)  # set initial position

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


wavetable1 = Wavetable("wav/BRAIDS02.WAV") # from http://waveeditonline.com/index-17.html
wavetable2 = Wavetable("wav/HARMONIO.WAV") # from http://waveeditonline.com/index.html

lfo_wave_uz = np.array( (32767, 0), dtype=np.int16)  # start at max go to zero
lfo_wave_dz = np.array( (-32767, 0), dtype=np.int16) # start at min go to zero
plfo1 = synthio.LFO(rate=0.10, once=True, waveform=lfo_wave_dz)
plfo2 = synthio.LFO(rate=0.10, once=True, waveform=lfo_wave_uz)
note1 = synthio.Note(frequency=65.4, waveform=wavetable1.waveform, bend=plfo1)
note2 = synthio.Note(frequency=65.4, waveform=wavetable2.waveform, bend=plfo2, amplitude=0.7)
synth.press( (note1,note2) )

# scan through the wavetable, morphing through each one
# we could use a global LFO for this, but let's do it by hand
i = 0  # current wave in wavetable
di = 0.07  # how fast to scan through wavetable, fractional means we morph
while True:
    i = i + di
    if i <=0 or i >= wavetable1.num_waves: di = -di  # bounce!
    wavetable1.set_wave_pos(i)
    wavetable2.set_wave_pos(i/3) # moves 1/3 as much
    time.sleep(0.001)

    if plfo1.phase > 0.99:
        plfo1.retrigger()  # retrigger LFOs to start bends again
        plfo2.retrigger()  # (we do this because synthio.LFO interpolates end->start too
