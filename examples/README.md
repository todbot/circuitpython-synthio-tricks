
synthio-tricks examples
=======================


- [eighties_dystopia](eighties_dystopia/code.py) - A swirling ominous wub that evolves over time

  - video demo: [eighties dystopia in synthio](https://www.youtube.com/watch?v=EcDqYh-DzVA)
  - also includes a version for the [PicoADK](https://github.com/DatanoiseTV/PicoADK-Hardware)
  - also includes a version for the [Pimoroni PicoAudio Pack](https://shop.pimoroni.com/products/pico-audio-pack)
  - wiring diagram:

    <img src="../imgs/eighties_dystopia_bb.png" width=400>

- [tiny_lfo_song](tiny_lfo_song/code.py) - A simple generative piece using only LFOs

  - video demo: [tiny LFO song in CircuitPython synthio](https://www.youtube.com/watch?v=m_ALNCWXor0)
  - also includes a version for the [PicoADK](https://github.com/DatanoiseTV/PicoADK-Hardware)
  - also includes a version for the [Pimoroni PicoAudio Pack](https://shop.pimoroni.com/products/pico-audio-pack)

- [monosynth1](monosynth1/code.py) - A complete USB & Serial MIDI monosynth that responds to
  MIDI velocity and CCs, with adjustable filter, vibrato, release time. Great for basslines.

  - video demo: [monosynth1 in synthio](https://www.youtube.com/watch?v=S1-TDjxE3Qs)
  - wiring diagram:

    <img src="../imgs/monosynth1_bb.png" width=400>

- [eighties_arp](eighties_arp/code.py) - An arpeggio explorer for non-musicians and test bed for my "Arpy" library

  - video demo: [eighties arp in synthio](https://www.youtube.com/watch?v=noj92Ae0IQI)
  - wiring diagram:

    <img src="../imgs/eighties_arp_bb.png" width=400>

- [wavetable_midisynth](wavetable_midisynth/code.py) - MIDI synth using morphing wavetables

  - video demo: [wavetable_midisynth demo, a circuitpython-synthio-trick](https://www.youtube.com/watch?v=CrxaB_AVQqM)
  - also includes a version for [Raspberry Pi Pico and I2S DAC](wavetable_midisynth/code_i2s.py)
  - set `auto_play=True` if you don't have a MIDI keyboard and it'll play its own little tune
  - wiring diagram:
    - for QTPy RP2040 PWM version, same as "eighties_dystopia"

- [falling_forever](falling_forever/code.py) - Use morphing wavetables and LFOs to make weird sounds

  - video demo: [falling_forever: playign with wavetables in CircuitPython](https://www.youtube.com/watch?v=V3454a47xIs)
  - also includes a version for [Raspberry Pi Pico and I2S DAC](falling_forever/code_i2s.py)
  - wiring diagram:
    - for QTPy RP2040 PWM version, same as "eighties_dystopia"
