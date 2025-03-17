# synthio_tiny_lfo_song.py -- tiny "song" made with just LFOs in synthio
# 29 May 2023 - @todbot / Tod Kurt
# video demo: https://www.youtube.com/watch?v=m_ALNCWXor0
# requires CircuitPython 8.2.0-beta0 or later
import board, time, audiopwmio, synthio, random
import ulab.numpy as np
audio = audiopwmio.PWMAudioOut(board.GP10)
synth = synthio.Synthesizer(sample_rate=22050)
audio.play(synth)

synth.envelope = synthio.Envelope(attack_time=0.1, release_time=0.05)

lfo_wav = np.array([0,32000,0], dtype=np.int16)
lfo_tremo1 = synthio.LFO(rate=3,    waveform=lfo_wav)  # 3 Hz for fastest note
lfo_tremo2 = synthio.LFO(rate=2,    waveform=lfo_wav)  # 2 Hz for middle note
lfo_tremo3 = synthio.LFO(rate=1,    waveform=lfo_wav)  # 1 Hz for lower note
lfo_tremo4 = synthio.LFO(rate=0.75, waveform=lfo_wav)  # 0.75 Hz for lowest bass note


def do_notes(midi_note):
    note1 = synthio.Note( synthio.midi_to_hz(midi_note), amplitude=lfo_tremo1)
    note2 = synthio.Note( synthio.midi_to_hz(midi_note-7), amplitude=lfo_tremo2)
    note3 = synthio.Note( synthio.midi_to_hz(midi_note-12), amplitude=lfo_tremo3)
    note4 = synthio.Note( synthio.midi_to_hz(midi_note-24), amplitude=lfo_tremo4)
    synth.release_all_then_press( (note1, note2, note3, note4) )

start_note = 65
song_notes = (start_note+0, start_note+5, start_note-3)
i=0
while True:
    print("hi, we're just groovin")
    do_notes(song_notes[i])
    i= (i+1) % len(song_notes)
    time.sleep(8)
