import board, time, audiopwmio, synthio, random
import ulab.numpy as np
import audiobusio, audiomixer
audio = audiobusio.I2SOut(bit_clock=board.GP11, word_select=board.GP12, data=board.GP10)
#audio = audiopwmio.PWMAudioOut(board.GP10)
#synth = synthio.Synthesizer(sample_rate=22050)
mixer = audiomixer.Mixer(sample_rate=28000, channel_count=1, buffer_size=4096)
synth = synthio.Synthesizer(sample_rate=28000, channel_count=1)
audio.play(mixer)
mixer.voice[0].play(synth)
mixer.voice[0].level = 0.75  # cut the loudness a bit

# standard linear interpolate
def lerp(a, b, t):  return (1-t)*a + t*b

# standard quad ease-in-out function
def quadeaseinout(a,b,t):
    t = 2 * t * t if t < 0.5 else 1 - pow(-2*t + 2, 2) / 2
    return a + t * (b-a)

import adafruit_wave
def read_waveform(filename, n=0, start=0):
    with adafruit_wave.open(filename) as w:
        if w.getsampwidth() != 2 or w.getnchannels() != 1:
            raise ValueError("unsupported format")
        n = w.getnframes() if n==0 else n
        w.setpos(start)
        return memoryview(w.readframes(n)).cast('h')

SAMPLE_SIZE = 256
wave_saw = np.linspace(20000, -20000, num=SAMPLE_SIZE, dtype=np.int16)  # 20k gives us more headroom somehow
wave_noise = np.array([random.randint(-32767, 32767) for i in range(SAMPLE_SIZE)], dtype=np.int16)
wave_rampdown = np.linspace(32767, -32767, num=3, dtype=np.int16)  # for pitch LFO
wave_rampup = np.linspace(-32767, 32767, num=3, dtype=np.int16)  # for pitch LFO
#wave_akwf_g0001 = read_waveform("AKWF_granular_0001.wav")
my_wave = wave_saw

# Deep Note MIDI note names to note numbers
# A2  D1  D2  D3  A3  D4  A4  D5  A5  D6  F#6
# 45  26  38  50  57  62  69  74  81  86  90
# from https://www.phpied.com/webaudio-deep-note-part-4-multiple-sounds/
note_start = 45  # A2
notes_deepnote = ( 26, 38, 50, 57,  62, 69, 74, 81,
                   62, 69, 74, 81,  86, 86, 90, 90 );
# Deep Note lifecycle
stage1_time = 3  # static random chaos
stage2_time = 3  # moving random chaos
stage3_time = 8  # converge on big chord
stage4_time = 5  # hold on big chord
time_steps = 100 # iterations per stage

num_oscs = 6

notes = [None] * num_oscs
lfos = [None] * num_oscs

notesS1 = [random.uniform(note_start, note_start+12) for _ in range(num_oscs)]
notesS2 = [random.uniform(note_start+30, note_start) for _ in range(num_oscs)]
notesS3 = notes_deepnote[0:num_oscs]

amp_env = synthio.Envelope(attack_time=0.5, release_time=3, sustain_level=0.85, attack_level=0.85)
for i in range(num_oscs):
    lfos[i] = synthio.LFO(rate=0.0001,
                          scale=random.uniform(0.25,0.5),
                          phase_offset=random.random(),
                          waveform=wave_noise)
    notes[i] = synthio.Note( synthio.midi_to_hz(notesS1[i]),
                             waveform=my_wave
                             envelope=amp_env, bend=lfos[i])

# stage 1 is static random chaos (as set above with random LFOs)
print("starting stage 1")
synth.press(notes)
time.sleep(stage1_time)

#print("debug wait")
#time.sleep(10)

# stage 2 is moving chaos, where oscs move randomly towards a random destination pitch over a (random) time
print("starting stage 2")
for t in range(time_steps):
    for i in range(num_oscs):
        notes[i].frequency = lerp( synthio.midi_to_hz(notesS1[i]),
                                   synthio.midi_to_hz(notesS2[i]), t/time_steps)
        lfos[i].scale = lfos[i].scale * 0.97
    time.sleep(stage2_time/time_steps)

# stage 3 is converge on big chord
print("starting stage 3")
for t in range(time_steps):
    for i in range(num_oscs):
        lfos[i].scale = max(lfos[i].scale * 0.99,  0.001)
        notes[i].frequency = lerp( synthio.midi_to_hz(notesS2[i]),
                                   synthio.midi_to_hz(notesS3[i]), t/time_steps)
    time.sleep(stage3_time/time_steps)
    #print(notes[i].frequency, lfos[i].scale, t/time_steps)

print("starting stage 4")

time.sleep(stage4_time)
synth.release_all()

while True:
    print("done")
    time.sleep(1)
