import argparse
import os
import subprocess
import sys
from math import ceil

from .splitpoints import read_chapters, align_splits

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('soundfile',
            help='Sound file to split, or a sample rate in Hz to use for '
                 'calculating split points. If no file is specified, '
                 'the output and format parameters are ignored.')
    argparser.add_argument('-o', '--output', default='',
            help='Output directory for track files '
                 '(default: current directory)')
    argparser.add_argument('-O', '--overwrite', action='store_true',
            help='Overwrite existing files (skipped by default)')
    argparser.add_argument('-f', '--format',
            help='Output file format (default: same as input)')
    argparser.add_argument('playlist', type=argparse.FileType('rb'),
            help='MPLS file with track timecodes')
    argalign = argparser.add_mutually_exclusive_group()
    argalign.add_argument('-a', '--align', type=int,
            help='Align track splits to 1/n second margins, where the input '
                 'sample rate is divisible by n')
    argalign.add_argument('--cd', action='store_const', const=75, dest='align',
            help='Align track splits to Audio CD sectors, equivalent to -a 75')
    roundmodes = {'down': int, 'nearest': round, 'up': ceil}
    argparser.add_argument('-r', '--round', default='down',
            choices=roundmodes.keys(),
            help='Rounding method when split points need to be aligned '
                 '(default: down)')
    argparser.add_argument('-v', '--verbose', action='store_true',
            help='Print chapter timings and progress')
    argparser.add_argument('--sox', action='store_true',
            help='Use SoX to write split tracks instead of the internal '
                 'writing library')
    args = argparser.parse_args()
    args.round = roundmodes[args.round]

    with args.playlist:
        chapters, precision = read_chapters(args.playlist)

    if args.verbose:
        for num, chapter in enumerate(chapters):
            print(f'{num + 1:>2}: {int(chapter / precision / 60):>3}:'
                  f'{int(chapter / precision) % 60:02}.'
                  f'{int(chapter / precision * 1000000) % 1000000:06}')

    if os.path.exists(args.soundfile):
        import soundfile
        infile = soundfile.SoundFile(args.soundfile)
        samplerate = infile.samplerate
    else:
        try:
            samplerate = int(args.soundfile)
            infile = None
        except ValueError:
            argparser.error(f'{args.soundfile} is not a file or a sample rate')

    if args.align is None:
        args.align = samplerate
    elif not (samplerate / args.align).is_integer():
        argparser.error(f'sample rate {samplerate} is not evenly divisible '
                        f'into {args.align} blocks per second.')

    # Calculate split points in terms of samples
    splits = align_splits(chapters, precision, samplerate,
            args.align, args.round)

    # If no actual input file, print split points and exit
    if infile is None:
        print('\n'.join([str(i) for i in splits]))
        return

    with infile:
        if args.format is None:
            args.format = infile.format
            extension = os.path.splitext(args.soundfile)[1]
        else:
            extension = '.' + args.format.lower()

        # Make sure the last track ends where the input file ends
        while len(splits) > 0 and splits[-1] > len(infile):
            print(f'Warning: track {len(splits)} starts after the end of the '
                  f'input file', file=sys.stderr)
            splits.pop()
        if len(splits) == 0 or splits[-1] < len(infile):
            splits.append(len(infile))

        import numpy
        lengths = numpy.diff(splits)

        # Prepare our output directory
        if args.output != '':
            os.makedirs(args.output, exist_ok=True)

        if not args.sox:
            # Seek to the actual start of the first track if necessary
            if splits[0] != 0:
                infile.seek(splits[0], soundfile.SEEK_SET)

            # Prepare a buffer for audio data
            if infile.subtype == 'FLOAT':
                dtype = 'float32'
            elif infile.subtype in ('PCM_U8', 'PCM_S8', 'PCM_16'):
                dtype = 'int16'
            elif 'PCM' in infile.subtype:
                dtype = 'int32'
            else: # safe fallback
                dtype = 'float64'
            buffersize = 16384
            rdbuff = numpy.ndarray((buffersize, infile.channels), dtype=dtype)

        for track, length in enumerate(lengths):
            outname = os.path.join(args.output, f'{track + 1:0>2}{extension}')
            if not args.overwrite and os.path.exists(outname):
                print(f'{outname} already exists, skipping...',
                        file=sys.stderr)
                if not args.sox:
                    infile.seek(length, soundfile.SEEK_CUR)
                continue

            if args.verbose:
                print(f'Writing {outname} starting at {splits[track]}...')

            if args.sox:
                try:
                    subprocess.call(('sox', args.soundfile, outname, 'trim',
                            f'{splits[track]}s', f'{length}s'))
                except FileNotFoundError:
                    print('Could not find SoX executable, make sure it is '
                          'in PATH.', file=sys.stderr)
                    return
            else:
                with soundfile.SoundFile(outname, 'w', infile.samplerate,
                        infile.channels, infile.subtype,
                        format=args.format) as outfile:
                    while length > 0:
                        rdsize = min(len(rdbuff), length)
                        outfile.write(infile.read(rdsize, out=rdbuff))
                        length -= rdsize
