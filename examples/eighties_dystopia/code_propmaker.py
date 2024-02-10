# synthio_eighties_dystopia_propmaker.py -- for Feather RP2040 Prop-Maker
# 19 Jun 2023 - @todbot / Tod Kurt
#
import time, random
import board, digitalio, audiobusio, audiomixer, synthio
import ulab.numpy as np

extpwr_pin = digitalio.DigitalInOut(board.EXTERNAL_POWER)
extpwr_pin.switch_to_output(value=True)
audio = audiobusio.I2SOut(bit_clock=board.I2S_BIT_CLOCK, word_select=board.I2S_WORD_SELECT, data=board.I2S_DATA)

mixer = audiomixer.Mixer(channel_count=2, sample_rate=22050, buffer_size=2048)
synth = synthio.Synthesizer(channel_count=2, sample_rate=22050)
audio.play(mixer)
mixer.voice[0].play(synth)
mixer.voice[0].level = 0.8

wave_saw = np.linspace(25000, -25000, num=512, dtype=np.int16)  # max is +/-32k but gives us headroom
amp_env = synthio.Envelope(attack_level=1, sustain_level=1)

notes = (33, 34, 31) #  possible notes to play MIDI A1, A1#, G1
note_duration = 15   # how long each note plays for
num_voices = 5       # how many voices for each note
lpf_basef = 500      # filter lowest frequency
lpf_resonance = 1.4  # filter q

# set up the voices (aka "Notes" in synthio-speak) w/ initial values
voices = []
for i in range(num_voices):
    voices.append( synthio.Note( frequency=0, envelope=amp_env, waveform=wave_saw ) )

def set_notes(n):
    for voice in voices:
        f = synthio.midi_to_hz( n ) + random.random()
        voice.frequency = f
    voices[0].frequency = voices[0].frequency/2  # bass note one octave down

# the LFO that modulates the filter cutoff
lfo_filtermod = synthio.LFO(rate=0.1, scale=2000, offset=2000)
# we can't attach this directly to a filter input, so stash it in the blocks runner
synth.blocks.append(lfo_filtermod)

# start the voices playing
set_notes(notes[0])
synth.press(voices)

note_pos = 0
last_note_time = 0
last_filtermod_time = 0

while True:
    # continuosly update filter, no global filter, so update each voice's filter
    for v in voices:
        v.filter = synth.low_pass_filter( lpf_basef + lfo_filtermod.value, lpf_resonance )

    if time.monotonic() - last_filtermod_time > 3:
        last_filtermod_time = time.monotonic()
        lfo_filtermod.rate = 0.01 + random.random() / 4
        print("filtermod",lfo_filtermod.rate)

    if time.monotonic() - last_note_time > note_duration:
        last_note_time = time.monotonic()
        note_pos = (note_pos+1) % len(notes)
        set_notes(notes[note_pos])
        print("note", note_pos, notes[note_pos])
