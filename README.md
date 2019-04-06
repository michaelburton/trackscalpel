# Track Scalpel

Read chapters from a Blu-ray MPLS playlist file and split audio files into
tracks based on those chapters

## Features

* Read and write any format supported by SoundFile/libsndfile, including
  WAV, W64, AIFF and FLAC among others
* Can delegate splitting to SoX to support other formats
* Generate a list of sample-accurate cut points to use with other tools
* Read MPLS directly for maximum precision: MPLS timestamps are accurate to
  1/45000 of a second whereas text chapter files are accurate to 1/1000s and
  cue sheets are accurate to 1/75s
* Configurable block/sector alignment: can be sample-accurate or round
  down/up/to nearest 1/n of a second, useful for aligning to audio CD sectors
  or frames for gapless playback

## Known issues

The Python SoundFile module does not appear to provide a way to set channel
layout metadata when writing files, so while this program can read and write
5.1 and 7.1 surround, it does not write channel layout. SoX does not properly
preserve channel layout when working with WAV either, but does for FLAC so you
can work around this problem by delegating cutting to SoX and using FLAC as
both input and output format.

WAV files over 2GB are not supported. You should use a format that supports
large files such as FLAC or W64.

## Requirements

* Python 3.6+
* NumPy and SoundFile are required to read/write sound files
* [SoX](http://sox.sourceforge.net/) (optional)

## Usage

To install, run:

    pip install git+https://github.com/michaelburton/trackscalpel.git

To list the sample numbers where each chapter in playlist 00001.mpls begins
given a sample rate of 48kHz, run:

    trackscalpel 48000 00001.mpls

To split a file called audio.wav with playlist 00001.mpls and put the resulting
files (01.wav, 02.wav, ...) into the current directory, run:

    trackscalpel audio.wav 00001.mpls

To split a file called audio.wav with playlist 00001.mpls, align splits along
Audio CD sector boundaries, encode the tracks in FLAC format and place them in
the 'tracks' directory (tracks/01.flac, tracks/02.flac, ...), run:

    trackscalpel --cd -f FLAC -o tracks audio.wav 00001.mpls

For more detailed usage information, run:

    trackscalpel -h

## Acknowledgements

MPLS parsing code is from [PyGuymer](https://github.com/Guymer/PyGuymer), very
lightly modified to run under Python 3 (I just replaced `xrange` with `range`).
