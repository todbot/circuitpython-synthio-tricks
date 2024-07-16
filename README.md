

CircuitPython Synthio Tricks
===============

This is a small list of tricks and techniques I use for my experiments 
in making synthesizers with [`synthio`](https://docs.circuitpython.org/en/latest/shared-bindings/synthio/index.html), and similar to my ["circuitpython-tricks"](https://github.com/todbot/circuitpython-tricks) page. 
Some of the synths/boards I've made that can use these techniques:
[`pico_touch_synth`](https://github.com/todbot/picotouch_synth), 
[`qtpy_synth`](https://github.com/todbot/qtpy_synth), 
[`pico_test_synth`](https://github.com/todbot/pico_test_synth), 
[`macropadsynthplug`](https://github.com/todbot/macropadsynthplug). 
Also check out the "larger-tricks" directory for other examples. 

<!--ts-->
   * [What is synthio?](#what-is-synthio)
      * [How synthio differs from other synthesis systems](#how-synthio-differs-from-other-synthesis-systems)
      * [What synthio is not](#what-synthio-is-not)
      * [Some examples](#some-examples)
   * [Getting started](#getting-started)
      * [Which boards does synthio work on?](#which-boards-does-synthio-work-on)
      * [Audio out hardware](#audio-out-hardware)
         * [Ready-made boards](#ready-made-boards)
         * [RC filter and audiopwmio.PWMAudioOut](#rc-filter-and-audiopwmiopwmaudioout)
         * [I2S stereo DAC](#i2s-stereo-dac)
      * [Play a note every second](#play-a-note-every-second)
      * [Play a chord](#play-a-chord)
      * [USB MIDI Input](#usb-midi-input)
      * [Serial MIDI Input](#serial-midi-input)
      * [Using AudioMixer for adjustable volume &amp; fewer glitches](#using-audiomixer-for-adjustable-volume--fewer-glitches)
   * [Basic Synth Techniques](#basic-synth-techniques)
      * [Amplitude envelopes](#amplitude-envelopes)
         * [Envelope for entire synth](#envelope-for-entire-synth)
         * [Using synthio.Note for per-note velocity envelopes](#using-synthionote-for-per-note-velocity-envelopes)
      * [LFOs](#lfos)
         * [Printing LFO output](#printing-lfo-output)
         * [Vibrato: pitch bend with LFO](#vibrato-pitch-bend-with-lfo)
         * [Tremolo: volume change with LFO](#tremolo-volume-change-with-lfo)
      * [Pitch Bend / Portamento](#pitch-bend-portamento)
         * [Pitch bend, by hand](#pitch-bend-by-hand)
         * [Pitch bend, bend lfo](#pitch-bend-bend-lfo)
      * [Waveforms](#waveforms)
         * [Making your own waves](#making-your-own-waves)
         * [Wavetable morphing](#wavetable-morphing)
      * [Filters](#filters)
      * [Filter modulation](#filter-modulation)
   * [Advanced Techniques](#advanced-techniques)
      * [Keeping track of pressed notes](#keeping-track-of-pressed-notes)
      * [Detuning oscillators for fatter sound](#detuning-oscillators-for-fatter-sound)
      * [Turn WAV files info oscillators](#turn-wav-files-info-oscillators)
      * [Using WAV wavetables](#using-wav-wavetables)
      * [Using LFO values in your own code](#using-lfo-values-in-your-own-code)
      * [Using synthio.Math with synthio.LFO](#using-synthiomath-with-synthiolfo)
      * [Drum synthesis](#drum-synthesis)
   * [Examples](#examples)

<!-- Added by: tod, at: Thu Jun  1 10:59:15 PDT 2023 -->

<!--te-->

## What is `synthio`?

- CircuitPython [core library](https://docs.circuitpython.org/en/latest/shared-bindings/synthio/index.html)
   available since 8.2.0-beta0 and still in development!
- Features:
  - Polyphonic (12 oscillator) & stereo, 16-bit, with adjustable sample rate
  - Oscillators are single-cycle waveform-based allowing for real-time adjustable wavetables
  - ADSR [amplitude envelope](https://docs.circuitpython.org/en/latest/shared-bindings/synthio/index.html#synthio.Envelope) per oscillator
  - Oscillator [ring modulation](https://docs.circuitpython.org/en/latest/shared-bindings/synthio/index.html#synthio.Note.ring_frequency) w/ customizable ring oscillator waveform
  - Extensive [LFO system](https://docs.circuitpython.org/en/latest/shared-bindings/synthio/index.html#synthio.LFO)
    - multiple LFOs per oscillator (amplitude, panning, pitch bend, ring mod)
    - LFOs can repeat or run once (becoming a kind of envelope)
    - Each LFO can have a custom waveform with linear interpolation
    - LFO outputs can be used by user code
    - LFOs can plug into one another
    - Customizable LFO wavetables and can be applied to your own code
  - [Math blocks](https://docs.circuitpython.org/en/latest/shared-bindings/synthio/index.html#synthio.Math)
     with [14 three-term Math operations](https://docs.circuitpython.org/en/latest/shared-bindings/synthio/index.html#synthio.Math) to adjust LFO ranges, offsets, scales
  - Utility functions to easily convert from [MIDI note to frequency](https://docs.circuitpython.org/en/latest/shared-bindings/synthio/index.html#synthio.midi_to_hz) or [V/Oct modular to frequency](https://docs.circuitpython.org/en/latest/shared-bindings/synthio/index.html#synthio.voct_to_hz)
  - Two-pole resonant low-pass (LPF) / high-pass (HPF) / band-pass (BPF) / notch filter, per-oscillator
  - Plugs into existing the [`AudioMixer`](https://docs.circuitpython.org/en/latest/shared-bindings/audiomixer/index.html) system for use alongside `audiocore.WaveFile` sample playing

### How `synthio` differs from other synthesis systems

Signal flow in traditional sythesis systems is "wired up" once
(either physically with circuits or virtually with software components)
and then controlled with various inputs.   For instance, one may create oscillator, filter, and
amplifier objects, flowing audio from one to the other.
You then twiddle these objects to, for example, adjust pitch and trigger filter and
amplifier envelope generators.

In `synthio`, the signal chain is re-created each time a note is triggered.
The `synthio.Note` object is the holder of the oscillator (`note.waveform`),
the filter (`note.filter`), the amplitude envelope (`note.envelope`), among others.

In many cases, to change these features, you create new versions of them with different parameters,
e.g.
- `note.filter = synth.low_pass_filter(1200,1.3)` -- create a new LPF at 1200 Hz w/ 1.3 resonance
- `note.envelope = synthio.Envelope(release_time=0.8)` -- create an envelope w/ 0.8 sec release time

Thus, if you're getting started in the reference docs, the best place to start is
[synthio.Note](https://docs.circuitpython.org/en/latest/shared-bindings/synthio/index.html#synthio.Note).

### What `synthio` is not

While `synthio` has extensive modulation capabilities, the signal flow is fixed. It is not a modular-style
synthesis engine. Conceptually it is VCO->VCF->VCA and that cannot be changed.
You cannot treat an oscillator as an LFO, nor can you use an LFO as an audio oscillator.
(however there is built-in ring modulation for multi-waveform mixing)
You cannot swap out the default 2-pole Biquad filter for a 4-pole Moog-style ladder filter emulation,
and you cannot stack filters.
But since each `synthio.Note` is its own entire signal chain, you can create interesting effects by creating
multiple Notes at the same frequency but with different waveform, filter, amplitude, and modulation settings.


### Some examples

If you're familiar with CircuitPython and synthesis, and want to dive in, there are larger
[synthio-tricks examples](examples/) with wiring diagrams. In there you'll find:

- [eighties_dystopia](examples/eighties_dystopia/code.py) - A swirling ominous wub that evolves over time
- [eighties_arp](examples/eighties_arp/code.py) - An arpeggio explorer for non-musicians
- [monosynth1](examples/monosynth1/code.py) - A complete MIDI monosynth w/ adjustable filter



## Getting started

### Which boards does `synthio` work on?

There's a good chance `synthio` works on your CircuitPython board. Some boards I like:
- Adafruit QT Py RP2040 with `audiopwmio` and PWM circuit
- Raspberry Pi Pico with `audiopwmio` and PWM circuit
- Adafruit QT Py ESP32-S3 with `audiobusio` and PCM5102 I2S board
- Lolin S2 Mini ESP32-S2 with `audiobusio` and PCM5102 I2S board

Since `synthio` is built in to CircuitPython and CirPy has varying support on different boards,
you will need to check your board's "Built-in modules avialble" section on
[circuitpython.org/downloads](https://circuitpython.org/downloads).
Here's what that section looks like for the QTPy RP2040:

<img src="./imgs/circuitpython_download_qtpyrp2040.jpg">

Note that `synthio` is there, and two audio output methods. CircuitPython supports three
different audio output techniques, with varying availability:

- [`audioio.AudioOut`](https://docs.circuitpython.org/en/latest/shared-bindings/audioio/index.html)
   -- output to built-in DAC (usually SAMD51 "M4" boards)
- [`audiobusio.I2SOut`](https://docs.circuitpython.org/en/latest/shared-bindings/audiobusio/index.html)
   -- output to external I2S DAC board (RP2040, ESP32S2/3, SAMD51 "M4", nRF52)
- [`audiopwmio.PWMAudioOut`](https://docs.circuitpython.org/en/latest/shared-bindings/audiopwmio/index.html)
   -- output PWM that needs external RC filter to convert to audio (RP2040, nRF52)

Notice that not all audio output techniques are supported everywhere.
An I2S DAC board is the most widely supported, and highest quality.
Even so, this guide will focus mostly on PWMAudioOut on Pico RP2040 because it's quick and simple,
but any of the above will work.

###  Audio out hardware

Because there are many audio output methods, there are many different circuits.

#### Ready-made boards

The simplest will be ready-made boards, like
  - [PicoADK](https://github.com/DatanoiseTV/PicoADK-Hardware)
  - [Pimoroni Pico Audio Pack](https://shop.pimoroni.com/products/pico-audio-pack)
  - [Pimoroni Pico DV Demo Base](https://shop.pimoroni.com/products/pimoroni-pico-dv-demo-base)
  - [Adafruit Feather RP2040 Prop-Maker](https://www.adafruit.com/product/5768)

These all have built in I2S DACs and use `audiobusio.I2SOut`.

#### RC filter and `audiopwmio.PWMAudioOut`

  The Pico and some other chips can output sound using PWM (~10-bit resolution) with an RC-filter.
  (R1=1k, C1=100nF, [Sparkfun TRRS](https://www.sparkfun.com/products/11570))

  <img src="./imgs/synthio_pico_pwm_bb.jpg" width=500>

  Note: this is a very minimal RC filter stage that doesn't do DC-blocking
  and proper line driving, but is strong enough to power many headphones.
  See [here for a more complete RC filter circuit](https://www.youtube.com/watch?v=rwPTpMuvSXg).


#### I2S stereo DAC

  An example I2S DAC is the [I2S PCM5102](https://amzn.to/3MGOTJH).

  An I2S DAC board is capable of stereo CD-quality sound and they're very affordable.
  The line out is also strong enough to drive many headphones too, but I usually feed
  the output into a portable bluetooth speaker with line in.

  <img src="./imgs/synthio_pico_i2s_bb.jpg" width=500>

  Note that in addition to the three I2S signals:
   - PCM5102 BCK pin = `bit_clock`,
   - PCM5102 LRCK pin = `word_select`
   - PCM5102 DIN pin = `data`

  you will need to wire:
   - PCM5102 SCK pin to GND

  in addition to wiring up Vin & Gnd.  For more details,  check out
  [this post on PCM5102 modules](https://todbot.com/blog/2023/05/16/cheap-stereo-line-out-i2s-dac-for-circuitpython-arduino-synths/).


### Play a note every second

Use one of the above circuits, we can now hear what `synthio` is doing.

```py
import board, time
import synthio

# for PWM audio with an RC filter
import audiopwmio
audio = audiopwmio.PWMAudioOut(board.GP10)

# for I2S audio with external I2S DAC board
#import audiobusio
#audio = audiobusio.I2SOut(bit_clock=board.GP11, word_select=board.GP12, data=board.GP10)

# for I2S audio on Feather RP2040 Prop-Maker
#extpwr_pin = digitalio.DigitalInOut(board.EXTERNAL_POWER)
#extpwr_pin.switch_to_output(value=True)
#audio = audiobusio.I2SOut(bit_clock=board.I2S_BIT_CLOCK, word_select=board.I2S_WORD_SELECT, data=board.I2S_DATA)

synth = synthio.Synthesizer(sample_rate=22050)
audio.play(synth)

while True:
    synth.press(65) # midi note 65 = F4
    time.sleep(0.5)
    synth.release(65) # release the note we pressed
    time.sleep(0.5)
```

We'll be assuming PWMAudioOut in the examples below, but if you're using an I2S DAC instead,
the `audio` line would look like the commented out part above. The particular choices for the three
signals depends on the chip, and CircuitPython will tell you in the REPL is a particular pin combination
isn't supported. On RP2040-based boards like the Pico,
[many pin combos are available for I2S](https://learn.adafruit.com/adafruit-i2s-stereo-decoder-uda1334a/circuitpython-wiring-test#wheres-my-i2s-2995476).

The `synthio.Synthesizer` also needs a `sample_rate` to operate at. While it can operate at 44.1 kHz CD quality,
these demos we will operate at half that. This will give these results a more "low-fi" quality but does
free up the Pico to do other things like update a display if you use these tricks in your own code.

### Play a chord

To play notes simultaneously, send a list of notes to `synth.press()`.
Here we send a 3-note list of [MIDI note numbers](http://notebook.zoeblade.com/Pitches.html)
that represent musical notes (F4, A4, C5), an F-major chord.

```py
import board, time
import audiopwmio
import synthio

audio = audiopwmio.PWMAudioOut(board.GP10)
synth = synthio.Synthesizer(sample_rate=22050)
audio.play(synth)

while True:
  synth.press( (65,69,72) ) # midi notes 65,69,72  = F4, A4, C5
  time.sleep(0.5)
  synth.release( (65,69,72) )
  time.sleep(0.5)
```


### USB MIDI Input

How about a MIDI synth in 20 lines of CircuitPython?

(To use with a USB MIDI keyboard, plug both the keyboard & CirPy device into a computer,
and on the computer run a DAW like Ardour, LMMS, Ableton Live, etc,
to forward MIDI from keyboard to CirPy)

```py
import board
import audiopwmio
import synthio
import usb_midi
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff

audio = audiopwmio.PWMAudioOut(board.GP10)
synth = synthio.Synthesizer(sample_rate=22050)
audio.play(synth)

midi = adafruit_midi.MIDI(midi_in=usb_midi.ports[0], in_channel=0 )

while True:
    msg = midi.receive()
    if isinstance(msg, NoteOn) and msg.velocity != 0:
        print("noteOn: ", msg.note, "vel:", msg.velocity)
        synth.press( msg.note )
    elif isinstance(msg,NoteOff) or isinstance(msg,NoteOn) and msg.velocity==0:
        print("noteOff:", msg.note, "vel:", msg.velocity)
        synth.release( msg.note )

```

### Serial MIDI Input

The same as above, but replace the `usb_midi` with a `busio.UART`

```py
# ... as before
import busio
uart = busio.UART(tx=board.TX, rx=board.RX, baudrate=31250, timeout=0.001)
midi = adafruit_midi.MIDI(midi_in=uart, in_channel=0 )
while True:
  msg = midi.receive()
  # ... as before
```

For wiring up a serial MIDI, you should check out
[MIDI In for 3.3V Microcontrollers](https://diyelectromusic.wordpress.com/2021/02/15/midi-in-for-3-3v-microcontrollers/) page by diyelectromusic.  You can also try out
[this 6N138-based circuit](./imgs/monosynth1_bb.png)
I use for my [monosynth1 demo](https://www.youtube.com/watch?v=S1-TDjxE3Qs)


### Using AudioMixer for adjustable volume & fewer glitches

Stick an AudioMixer in between `audio` and `synth` and we get three benefits:
- Volume control over the entire synth
- Can plug other players (like `WaveFile`) to play samples simultaneously
- An audio buffer that helps eliminate glitches from other I/O

```py
import audiomixer
audio = audiopwmio.PWMAudioOut(board.GP10)
mixer = audiomixer.Mixer(sample_rate=22050, buffer_size=2048)
synth = synthio.Synthesizer(sample_rate=22050)
audio.play(mixer)
mixer.voice[0].play(synth)
mixer.voice[0].level = 0.25  # 25% volume might be better
```

Setting the AudioMixer `buffer_size` argument is handy for reducing giltches that happen when the chip is
doing other work like updating a display reading I2C sensors. Increase the buffer to eliminate glitches
but it does increase latency.

## Basic Synth Techniques

There are a handful of common techniques used to make a raw electronic waveform sound more like musical
instruments or sounds in the real world. Here are some of them.

### Amplitude envelopes

The amplitude envelope describes how a sound's loudness changes over time.
In synthesizers, [ADSR envelopes](https://en.wikipedia.org/wiki/Envelope_(music))
are used to describe that change. In `synthio`, you get the standard ADSR parameters,
and a default fast attack, max sustain level, fast release envelope.

#### Envelope for entire synth

To create your own envelope with a slower attack and release time, and apply it to every note:


```py
import board, time, audiopwmio, synthio
audio = audiopwmio.PWMAudioOut(board.GP10)
synth = synthio.Synthesizer(sample_rate=22050)
audio.play(synth)

amp_env_slow = synthio.Envelope(attack_time=0.2, release_time=0.8, sustain_level=1.0)
amp_env_fast = synthio.Envelope(attack_time=0.01, release_time=0.2, sustain_level=0.5)
synth.envelope = amp_env_slow  # could also set in synth constructor

while True:
  synth.press(65) # midi note 65 = F4
  time.sleep(0.5)
  synth.release(65)
  time.sleep(1.0)
  synth.envelope = amp_env_fast
  synth.press(65)
  time.sleep(0.5)
  synth.release(65)
  time.sleep(1.0)
  synth.envelope = amp_env_slow
```

#### Using `synthio.Note` for per-note velocity envelopes

To give you more control over each oscillator, `synthio.Note` lets you override
the default envelope and waveform of your `synth` with per-note versions.
For instance, you can create a new envelope based on incoming MIDI note velocity to
make a more expressive instrument. You will have to convert MIDI notes to frequency by hand,
but synthio provides a helper for that.

```py
import board, time, audiopwmio, synthio, random
audio = audiopwmio.PWMAudioOut(board.GP10)
synth = synthio.Synthesizer(sample_rate=22050)
audio.play(synth)

while True:
    midi_note = 65
    velocity = random.choice( (1, 0.1, 0.5) )  # 3 different fake velocity values 0.0-1.0
    print("vel:",velocity)
    amp_env = synthio.Envelope( attack_time=0.1 + 0.6*(1-velocity),  # high velocity, short attack
                                release_time=0.1 + 0.9*(1-velocity) ) # low velocity, long release
    note = synthio.Note( synthio.midi_to_hz(midi_note), envelope=amp_env )
    synth.press(note) # press with note object
    time.sleep(0.5)
    synth.release(note) # must release with same note object
    time.sleep(2.0)
```

The choice of how you scale velocity to attack times, sustain levels and so on,
is dependent on your application.

For an example of how to use this with MIDI velocity,
see [synthio_midi_synth.py](https://gist.github.com/todbot/96a654c5fa27625147d65c45c8bfd47b)


### LFOs

LFOs (Low-Frequency Oscillators) were named back when it was very different
to build an audio-rate oscillator vs an oscillator that changed over a few seconds.
In synthesis, LFOs are often used to "automate" the knob twiddling one would do to perform an instrument.
`synthio.LFO` is a flexible LFO system that can perform just about any kind of
automated twiddling you can imagine.

#### Printing LFO output

The `synthio.LFO`s are also just a source of varying numbers and those numbers you can use
as inputs to some parameter you want to vary. So you can just print them out!
Here's the simplest way to use a `synthio.LFO`.

```py
import time, board, synthio, audiopwmio

audio = audiopwmio.PWMAudioOut(board.GP10)
synth = synthio.Synthesizer(sample_rate=22050)
audio.play(synth)

mylfo = synthio.LFO(rate=0.3, scale=1, offset=1)
synth.blocks.append(mylfo)

while True:
    print(mylfo.value)
    time.sleep(0.05)
```

(instead of hooking up the LFO to a `synthio.Note` object, we're having it run globally via the
[`synth.blocks`](https://docs.circuitpython.org/en/latest/shared-bindings/synthio/index.html#synthio.Synthesizer.blocks) feature)

By default the waveform is a triangle and you can see the output of `mylfo.value`
smoothly vary from 0 to 1 to 0 to -1 to 0, and so on.
This means it has a range of 2. If you want just a positive triangle LFO going from 0 to 1 to 0,
you should set `scale=0.5, offset=0.5`.


The waveforms for `synthio.LFO` can be any waveform, even the same waveforms used for oscillators,
but you can also use much smaller datasets to LFO because by default it will do interpolation
between values for you.

To show the flexibilty of LFOs, here's a quick non-sound exmaple that prints out three different LFOs,
with custom waveforms.

```py
# orig from @jepler 15 May 2023 11:23a in #circuitpython-dev/synthio
import board, time, audiopwmio, synthio
import ulab.numpy as np

SAMPLE_SIZE = 1024
SAMPLE_VOLUME = 32767
ramp = np.linspace(-SAMPLE_VOLUME, SAMPLE_VOLUME, SAMPLE_SIZE, endpoint=False, dtype=np.int16)
sine = np.array(
    np.sin(np.linspace(0, 2 * np.pi, SAMPLE_SIZE, endpoint=False)) * SAMPLE_VOLUME,
    dtype=np.int16,
)

l = synthio.LFO(ramp, rate=4, offset=1)
m = synthio.LFO(sine, rate=2, offset=l, scale=8)
n = synthio.LFO(sine, rate=m, offset=-2, scale=l)
lfos = [l, m, n]

audio = audiopwmio.PWMAudioOut(board.GP10)
synth = synthio.Synthesizer(sample_rate=22050)  # not outputting sound, just its LFO ticking
audio.play(synth)
synth.blocks[:] = lfos  # attach LFOs to synth so they get ticked

while True:
    print("(", ",".join(str(lfo.value) for lfo in lfos), ")" )
    time.sleep(0.01)
```

If you run this with the [Mu plotter](https://codewith.mu/en/tutorials/1.2/plotter)
you'll see all three LFOs, and you can see how the "n" LFO's rate is being changed by the "m" LFO.

<img src="./imgs/synthio_lfo_demo1.png" width=500>


#### Vibrato: pitch bend with LFO

Some instruments like voice and violin can vary their pitch while sounding a note.
To emulate that, we can use an LFO.  Here we create an LFO with a rate of 5 Hz and amplitude of 0.5% max.
For each note, we apply that LFO to the note's `bend` property to create vibrato.

If you'd like the LFO to start over on each note on, do `lfo.retrigger()`.

```py
import board, time, audiopwmio, synthio
audio = audiopwmio.PWMAudioOut(board.GP10)
synth = synthio.Synthesizer(sample_rate=22050)
audio.play(synth)

lfo = synthio.LFO(rate=5, scale=0.05)  # 5 Hz lfo at 0.5%

while True:
    midi_note = 65
    note = synthio.Note( synthio.midi_to_hz(midi_note), bend=lfo )
    synth.press(note)
    time.sleep(1.0)
    synth.release(note)
    time.sleep(1.0)

```


#### Tremolo: volume change with LFO

Similarly, we can create rhythmic changes in loudness with an LFO attached to `note.amplitude`.
And since each note can get their own LFO, you can make little "songs" with just a few notes.
Here's a [demo video of this "LFO song"](https://www.youtube.com/watch?v=m_ALNCWXor0).


```py
import board, time, audiopwmio, synthio
audio = audiopwmio.PWMAudioOut(board.GP10)
synth = synthio.Synthesizer(sample_rate=22050)
audio.play(synth)

lfo_tremo1 = synthio.LFO(rate=3)  # 3 Hz for fastest note
lfo_tremo2 = synthio.LFO(rate=2)  # 2 Hz for middle note
lfo_tremo3 = synthio.LFO(rate=1)  # 1 Hz for lower note
lfo_tremo4 = synthio.LFO(rate=0.75) # 0.75 Hz for lowest bass note

midi_note = 65
note1 = synthio.Note( synthio.midi_to_hz(midi_note), amplitude=lfo_tremo1)
note2 = synthio.Note( synthio.midi_to_hz(midi_note-7), amplitude=lfo_tremo2)
note3 = synthio.Note( synthio.midi_to_hz(midi_note-12), amplitude=lfo_tremo3)
note4 = synthio.Note( synthio.midi_to_hz(midi_note-24), amplitude=lfo_tremo4)
synth.press( (note1, note2, note3, note4) )

while True:
    print("hi, we're just groovin")
    time.sleep(1)
```

         
### Pitch bend / Portamento

Pitch bend, portamento, pitch glide, or glissando are all roughly equivalent in 
synthesizers: a continuous smooth glide between two notes. While `synthio` doesn't
provide this exact functionality, we can achieve the effect via a variety of means. 

#### Pitch bend, by hand

There are several different ways to glide the pitch from one note to another. 
The most obvious way is to do it "by hand" by modifying the `note.frequency` property 
over time. (orig from a [discussion w/@shion on mastodon](https://mastodon.social/@todbot/112610331112413354))

```py
# ... synthio audio set up as normal ...
def bend_note(note, start_notenum, end_notenum, bend_time=3):
    bend_steps = 100  # arbitrarily chosen
    bend_deltat = bend_time / bend_steps
    f = synthio.midi_to_hz(start_notenum)
    for i in range(glide_steps):
        slid_notenum = start_notenum + i*((end_notenum - start_notenum)/bend_steps)
        note.frequency = synthio.midi_to_hz(slid_notenum)
        time.sleep(bend_deltat)  # note the time.sleep()!

while True:
    note = synthio.Note(synthio.midi_to_hz(70))
    synth.press(note)
    note_glide(note, 70,30)
    note_glide(note, 30,40, 0.1)
    note_glide(note, 40,70, 0.1)
    synth.release(note)
```

#### Pitch bend, bend lfo

The above approach isn't very efficient. So far the best way I've found to do 
pitch-bend is to use an LFO on the `note.bend` property, like with [vibrato](#vibrato-pitch-bend-with-lfo),
but with a specially-constructed "line" LFO in one-shot mode. 

```py
# ... synthio audio set up as normal ...
def bend_note(note, start_notenum, end_notenum, bend_time=1):
    bend_amount = (end_notenum - start_notenum) / 12
    # special two-point line LFO that goes from 0 to bend_amount
    bend_lfo = synthio.LFO( waveform=np.linspace(-16384, 16383, num=2, dtype=np.int16),
        rate=1/bend_time, scale=bend_amount, offset=bend_amount/2, once=True)
    note.bend = bend_lfo

start_notenum = 40  # E2
end_notenum = 52  # E3
while True:
    print("start:", start_notenum, "end:", end_notenum)
    note = synthio.Note(synthio.midi_to_hz(start_notenum), panning=0 )
    synth.press(note)
    time.sleep(2)
    bend_note(note, start_notenum, end_notenum, 0.75)
    synth.release(note)
    time.sleep(1)
    start_notenum = end_notenum
    end_notenum = random.randint(22,64)
```
Note that in addition to passing in the start note number to `synthio.Note()`, 
we must pass in the start note number and end MIDI note number to `bend_note()`.


### Waveforms

The default oscillator waveform in `synthio.Synthesizer` is a square-wave with 50% duty-cycle.
But synthio will accept any buffer of data and treat it as a single-cycle waveform.
One of the easiest ways to make the waveform buffers that synthio expects is to use
[`ulab.numpy`](https://learn.adafruit.com/ulab-crunch-numbers-fast-with-circuitpython/ulab-numpy-phrasebook).
The numpy functions also have useful tools like `np.linspace()` to generate a line through a number space
and trig functions like `np.sin()`. Once you have a waveform, set it with either `synth.waveform`
or creating a new `synthio.Note(waveform=...)`

#### Making your own waves

Here's an example that creates two new waveforms: a sine way and a sawtooth wave, and then plays
them a two-note chord, first with sine waves, then with sawtooth waves.

```py
import board, time, audiopwmio, synthio
import ulab.numpy as np
audio = audiopwmio.PWMAudioOut(board.GP10)
synth = synthio.Synthesizer(sample_rate=22050)
audio.play(synth)
# create sine & sawtooth single-cycle waveforms to act as oscillators
SAMPLE_SIZE = 512
SAMPLE_VOLUME = 32000  # 0-32767
wave_sine = np.array(np.sin(np.linspace(0, 2*np.pi, SAMPLE_SIZE, endpoint=False)) * SAMPLE_VOLUME, dtype=np.int16)
wave_saw = np.linspace(SAMPLE_VOLUME, -SAMPLE_VOLUME, num=SAMPLE_SIZE, dtype=np.int16)

midi_note = 65
my_wave = wave_saw
while True:
    # create notes using those waveforms
    note1 = synthio.Note( synthio.midi_to_hz(midi_note), waveform=my_wave)
    note2 = synthio.Note( synthio.midi_to_hz(midi_note-7), waveform=my_wave)
    synth.press(note1)
    time.sleep(0.5)
    synth.press(note2)
    time.sleep(1)
    synth.release( (note1,note2) )
    time.sleep(0.1)
    my_wave = wave_sine if my_wave is wave_saw else wave_saw  # toggle waveform
```

#### Wavetable morphing

One of the coolest things about `synthio` being wavetable-based, is that we can alter the `waveform`
_in real time_!

Given the above setup but replacing the "while" loop, this will mix between the sine & square wave.

The trick here is that we give the `synthio.Note` object an initial empty waveform buffer
and then instead of replacing that buffer with `note.waveform = some_wave` we copy with `note.waveform[:] = some_wave`.

(This avoids needing an additional `np.int16` result buffer for `lerp()`, since lerp-ing results in a `np.float32` array)

```py
[... hardware setup from above ...]
# create sine & sawtooth single-cycle waveforms to act as oscillators
SAMPLE_SIZE = 512
SAMPLE_VOLUME = 32000  # 0-32767

wave_sine = np.array(np.sin(np.linspace(0, 2*np.pi, SAMPLE_SIZE, endpoint=False)) * SAMPLE_VOLUME, dtype=np.int16)
wave_saw = np.linspace(SAMPLE_VOLUME, -SAMPLE_VOLUME, num=SAMPLE_SIZE, dtype=np.int16)

# mix between values a and b, works with numpy arrays too,  t ranges 0-1
def lerp(a, b, t):  return (1-t)*a + t*b

wave_empty = np.zeros(SAMPLE_SIZE, dtype=np.int16)  # empty buffer we'll use array slice copy "[:]" on
note = synthio.Note( frequency=220, waveform=wave_empty)
synth.press(note)

pos = 0
while True:
  print(pos)
  note.waveform[:] = lerp(wave_sine, wave_saw, pos)
  pos += 0.01
  if pos >=1: pos = 0
  time.sleep(0.01)
```

#### Filters

Filters let you change the character / timbre of the raw oscillator sound.
The filter algorithm in `synthio` is a Biquad filter, giving a two-pole (12dB)
low-pass (LP), high-pass (HP), or band-pass (BP) filters.

To set a filter at a fixed frequency, set the `Note.filter` property
using one of the `synthio.*_filter()` methods:

```py
[ ... synthio setup as normal ...]

frequency = 2000
resonance = 1.5

lpf = synth.low_pass_filter(frequency,resonance)
hpf = synth.high_pass_filter(frequency,resonance)
bpf = synth.band_pass_filter(frequency,resonance)

note1 = synth.Note(frequency=220, filter=lpf)
note2 = synth.Note(frequency=330, filter=hpf)
note3 = synth.Note(frequency=440, filter=bpf)
```

Note that making a filter is a complex operation, requiring a function,
and you cannot set the properties of a resulting filter after its created.
This makes modulating the filter a bit trickier.

Also note that currently there are some glitchy instabilties in the filter
when resonance is 2 or greater and filter frequency is close to note frequency.

#### Filter modulation

The standard synthio approach to modulation is to create a `synthio.LFO` and attach it to a property.
(see above LFO examples)  The properties must be of type `synthio.BlockInput` for this to work, though.
Not all synthio properties are `BlockInputs`, most notably, the `Note.filter` property.

So one way to modulate a filter is to use Python:

```py
# fake a looping ramp down filter sweep
fmin = 100
fmax = 1000
f = fmax
note = synth.Note(frequency=220)
synth.play(note)
while True:
  note.filter = synth.low_pass_filter(f, 1.5)  # adjust note's filter
  f = f - 10
  if f < fmin: f = fmax
  time.sleep(0.01)  # sleep determines our ramp rate
```

A more "synthio" way to modulate filter is to use an LFO but hand-copying LFO value to the filter.
This requires adding the LFO to the
[`synth.blocks`](https://docs.circuitpython.org/en/latest/shared-bindings/synthio/index.html#synthio.Synthesizer.blocks)
global runner since the LFO is not directly associated with a `Note`.

```py
fmin = 100
fmax = 1000
ramp_down = np.array( (32767,0), dtype=np.int16) # unpolar ramp down, when interpolated by LFO

f_lfo = synth.LFO(rate=0.3, scale=fmax-fmin, offset=fmin, waveform=ramp_down)
synth.blocks.append(f_lfo)  # add lfo to global LFO runner to get it to tick

note = synth.Note(frequency=220)
synth.play(note)  # start note sounding

while True:
  note.filter = synth.low_pass_filter(f_lfo.value, 1.5) # adjust its filter
  time.sleep(0.001)
```

This is a fairly advanced technique as it requires keeping track of the LFO objects stuffed
into `synth.blocks` so they can be removed later.  See "Keeping track of pressed notes" below for
one technique for doing this.


## Advanced Techniques


### Keeping track of pressed notes

When passing `synthio.Note` objects to `synth.press()` instead of MIDI note numbers,
your code must remmeber that `Note` object so it can pass it into `synth.release()` to stop it playing.

One way to do this is with a Python dict, where the key is whatever your unique identifier is
(e.g. MIDI note number here for simplicity) and the value is the note object.

```py

# setup as before to get `synth` & `midi` objects
notes_pressed = {}  # which notes being pressed. key=midi note, val=note object
while True:
    msg = midi.receive()
    if isinstance(msg, NoteOn) and msg.velocity != 0:  # NoteOn
        note = synthio.Note(frequency=synthio.midi_to_hz(msg.note), waveform=wave_saw, #..etc )
        synthio.press(note)
        notes_pressed[msg.note] = note
    elif isinstance(msg,NoteOff) or isinstance(msg,NoteOn) and msg.velocity==0:  # NoteOff
        note = notes_pressed.get(msg.note, None) # let's us get back None w/o try/except
        if note:
            syntho.release(note)
```


### Detuning oscillators for fatter sound

Since we have fine-grained control over a note's frequency with `note.frequency`, this means we can do a
common technique for getting a "fatter" sound.

```py
import board, time, audiopwmio, synthio
audio = audiopwmio.PWMAudioOut(board.TX)
synth = synthio.Synthesizer(sample_rate=22050)
audio.play(synth)

detune = 0.005  # how much to detune, 0.7% here
num_oscs = 1
midi_note = 45
while True:
    print("num_oscs:", num_oscs)
    notes = []  # holds note objs being pressed
    # simple detune, always detunes up
    for i in range(num_oscs):
        f = synthio.midi_to_hz(midi_note) * (1 + i*detune)
        notes.append( synthio.Note(frequency=f) )
    synth.press(notes)
    time.sleep(1)
    synth.release(notes)
    time.sleep(0.1)
    # increment number of detuned oscillators
    num_oscs = num_oscs+1 if num_oscs < 5 else 1
```


### Turn WAV files info oscillators

Thanks to [`adafruit_wave`](https://github.com/adafruit/Adafruit_CircuitPython_wave) it is really
easy to load up a WAV file into a buffer and use it as a synthio waveform. Two great repositories of
single-cycle waveforms are [AKWF FREE](https://www.adventurekid.se/akrt/waveforms/adventure-kid-waveforms/)
and [waveeditonline.com](http://waveeditonline.com/)

```py
# orig from @jepler 31 May 2023 1:34p #circuitpython-dev/synthio
import adafruit_wave

# reads in entire wave
def read_waveform(filename):
    with adafruit_wave.open(filename) as w:
        if w.getsampwidth() != 2 or w.getnchannels() != 1:
            raise ValueError("unsupported format")
        return memoryview(w.readframes(w.getnframes())).cast('h')

# this verion lets you lerp() it to mix w/ another wave
def read_waveform_ulab(filename):
    with adafruit_wave.open(filename) as w:
        if w.getsampwidth() != 2 or w.getnchannels() != 1:
            raise ValueError("unsupported format")
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)


my_wave = read_waveform("AKWF_granular_0001.wav")

```

### Using WAV Wavetables

The [waveeditonline.com](http://waveeditonline.com/) site has specially constructed WAV files
called "wavetables" that contain 64 single-cycle waveforms, each waveform having 256 samples.
The waveforms in a wavetable are usually harmonically-related, so scanning through them
can produce interesting effects that could sound similar to using a filter,
without needing to use `synth.filter`!

The code below will load up one of these wavetables, and let you pick different
waveforms within by setting `wavetable.set_wave_pos(n)`.

```py
import board, time, audiopwmio, synthio
import ulab.numpy as np
import adafruit_wave

audio = audiopwmio.PWMAudioOut(board.GP10)
synth = synthio.Synthesizer(sample_rate=22050)
audio.play(synth)

# mix between values a and b, works with numpy arrays too,  t ranges 0-1
def lerp(a, b, t):  return (1-t)*a + t*b

class Wavetable:
    def __init__(self, filepath, wave_len=256):
        self.w = adafruit_wave.open(filepath)
        self.wave_len = wave_len  # how many samples in each wave
        if self.w.getsampwidth() != 2 or self.w.getnchannels() != 1:
            raise ValueError("unsupported WAV format")
        self.waveform = np.zeros(wave_len, dtype=np.int16)  # empty buffer we'll copy into
        self.num_waves = self.w.getnframes() / self.wave_len

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

wavetable = Wavetable("BRAIDS02.WAV", 256) # from http://waveeditonline.com/index-17.html

note = synthio.Note(frequency=220, waveform=wavetable.waveform)
synth.press( note )  # start an oscillator going

# scan through the wavetable, morphing through each one
i=0
di=0.1  # how fast to scan
while True:
    i = i + di
    if i <=0 or i >= wavetable.num_waves: di = -di
    wavetable.set_wave_pos(i)
    time.sleep(0.001)
```


### Using LFO values in your own code

[tbd]

### Using `synthio.Math` with `synthio.LFO`

[tbd]

### Drum synthesis

[tbd, but check out [gamblor's drums.py gist](https://gist.github.com/gamblor21/15a430929abf0e10eeaba8a45b01f5a8)]

### Examples

Here are some [larger synthio-tricks examples with wiring diagrams](examples/).


### Troubleshooting


#### Glitches when `code.py` is saved or CIRCUITPY drive access

#### Distortion in audio

####
