# Track Scalpel

Split an audio file based on chapter marks in a Blu-ray MPLS playlist file

## Features

* Read and write any format supported by SoundFile/libsndfile, including
  WAV, W64, AIFF and FLAC among others
* Read MPLS directly for maximum precision: MPLS timestamps are accurate to
  1/45000 of a second whereas text chapter files are accurate to 1/1000s and
  cue sheets are accurate to 1/75s
* Configurable block/sector alignment: can be sample-accurate or round
  down/up/to nearest 1/n of a second, useful for aligning to audio CD sectors
  or frames for gapless playback

## Requirements

* Python 3.6+
* NumPy and SoundFile, both available via pip

## Usage

To split a file called audio.wav with playlist 00001.mpls and put the resulting
files (01.wav, 02.wav, ...) into the current directory, run:

    python trackscalpel.py audio.wav 00001.mpls

To split a file called audio.wav with playlist 00001.mpls, align splits along
Audio CD sector boundaries, encode the tracks in FLAC format and place them in
the 'tracks' directory (tracks/01.flac, tracks/02.flac, ...), run:

    python trackscalpel.py --cd -f FLAC -o tracks audio.wav 00001.mpls

For more detailed usage information, run:

    python trackscalpel.py -h

## Acknowledgements

MPLS parsing code is from [PyGuymer](https://github.com/Guymer/PyGuymer), very
lightly modified to run under Python 3 (I just replaced `xrange` with `range`).
