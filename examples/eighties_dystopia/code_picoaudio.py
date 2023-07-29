# synthio_eighties_dystopia_picoaudio.py -- Eighties Dystopia but on the Pimoroni PicoAudio board
# 29 Jun 2023 - @todbot / Tod Kurt
# - A swirling ominous wub that evolves over time
# - Made for PicoADK board (https://github.com/DatanoiseTV/PicoADK-Hardware),
#    running standard Pico CircuitPython 8.2.0-rc.1,
#    but will work with other boards w/ adjustments
# - No user input, just wallow in the sound
# - video demo: https://youtu.be/EcDqYh-DzVA
#
# Circuit:
# - Plug in Pico into Pico Audio board
#
# Code:
#  - Five detuned oscillators are randomly detuned very second or so
#  - A low-pass filter is slowly modulated over the filters
#  - The filter modulation rate also changes randomly every second (also reflected on neopixel)
#  - Every 15 seconds a new note is randomly chosen from the allowed note list
#  - New for PicoADK version: slow ominoous panning

import time, random
import board, digitalio, audiobusio, audiomixer, synthio
import ulab.numpy as np

notes = (33, 34, 31) # possible notes to play MIDI A1, A1#, G1
note_duration = 15   # how long each note plays for
num_voices = 5       # how many voices for each note
lpf_basef = 300      # filter lowest frequency
lpf_resonance = 1.7  # filter q

# PicoAudio board: PCM5100 mute pin and PCM5100 I2S audio (thankfully mute not required, disabled by default)
#mute_pin = digitalio.DigitalInOut(board.GP22)
#mute_pin.switch_to_output(value=True)
audio = audiobusio.I2SOut(bit_clock=board.GP10, word_select=board.GP11, data=board.GP9)

mixer = audiomixer.Mixer(channel_count=2, sample_rate=28000, buffer_size=2048)
synth = synthio.Synthesizer(channel_count=2, sample_rate=28000)
audio.play(mixer)
mixer.voice[0].play(synth)
mixer.voice[0].level = 0.8

# our oscillator waveform, a 512 sample downward saw wave going from +/-30k
wave_saw = np.linspace(30000, -30000, num=512, dtype=np.int16)  # max is +/-32k but gives us headroom
amp_env = synthio.Envelope(attack_level=1, sustain_level=1)

# set up the voices (aka "Notes" in synthio-speak) w/ initial values
voices = []
for i in range(num_voices):
    voices.append( synthio.Note( frequency=0, envelope=amp_env, waveform=wave_saw ) )

# the LFO that modulates the filter cutoff
lfo_filtermod = synthio.LFO(rate=0.05, scale=2000, offset=2000)
# we can't attach this directly to a filter input, so stash it in the blocks runner
synth.blocks.append(lfo_filtermod)

lfo_panning = synthio.LFO( rate=0.1, scale=0.5 )

# set all the voices to the "same" frequency (with random detuning)
# zeroth voice is sub-oscillator, one-octave down
def set_notes(n):
    for voice in voices:
        #f = synthio.midi_to_hz( n ) + random.uniform(0,1.0)  # what orig sketch does
        f = synthio.midi_to_hz( n + random.uniform(0,0.4) ) # more valid if we move up the scale
        voice.frequency = f
        voice.panning = lfo_panning
    voices[0].frequency = voices[0].frequency/2  # bass note one octave down

note = notes[0]
last_note_time = time.monotonic()
last_filtermod_time = time.monotonic()

# start the voices playing
set_notes(note)
synth.press(voices)

while True:
    # continuosly update filter, no global filter, so update each voice's filter
    for v in voices:
        v.filter = synth.low_pass_filter( lpf_basef + lfo_filtermod.value, lpf_resonance )

    if time.monotonic() - last_filtermod_time > 1:
        last_filtermod_time = time.monotonic()
        # randomly modulate the filter frequency ('rate' in synthio) to make more dynamic
        lfo_filtermod.rate = 0.01 + random.random() / 8
        print("filtermod",lfo_filtermod.rate)

    if time.monotonic() - last_note_time > note_duration:
        last_note_time = time.monotonic()
        # pick new note, but not one we're currently playing
        note = random.choice([n for n in notes if n != note])
        set_notes(note)
        print("note", note, ["%3.2f" % v.frequency for v in voices] )
