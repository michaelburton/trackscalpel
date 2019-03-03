import argparse
import MPLS
import numpy
import os
import soundfile
from math import ceil

def read_chapters(mpls):
    header, _ = MPLS.load_header(mpls)

    # Read play items and calculate timings
    mpls.seek(header['PlayListStartAddress'], os.SEEK_SET)
    pl, _ = MPLS.load_PlayList(mpls)
    duration = 0
    for item in pl['PlayItems']:
        item['INTimeMod'] = duration - item['INTime']
        duration += item['OUTTime'] - item['INTime']

    # And now the playlist marks
    mpls.seek(header['PlayListMarkStartAddress'], os.SEEK_SET)
    marks, _ = MPLS.load_PlayListMark(mpls)
    chapters = [mark['MarkTimeStamp'] +
            pl['PlayItems'][mark['RefToPlayItemID']]['INTimeMod']
            for mark in marks['PlayListMarks'] if mark['MarkType'] == 1]

    return chapters, 45000

argparser = argparse.ArgumentParser()
argparser.add_argument('soundfile', help='Sound file to split')
argparser.add_argument('playlist', type=argparse.FileType('rb'),
        help='MPLS file with track timecodes')
argparser.add_argument('-o', '--output', default='',
        help='Output directory for track files (default: current directory)')
argparser.add_argument('-O', '--overwrite', action='store_true',
        help='Overwrite existing files (skipped by default)')
argparser.add_argument('-f', '--format',
        help='Output file format (default: same as input)')
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
args = argparser.parse_args()
args.round = roundmodes[args.round]

chapters, precision = read_chapters(args.playlist)
if args.verbose:
    for num, chapter in enumerate(chapters):
        print(f'{num + 1:>2}: {int(chapter / precision / 60):>3}:'
              f'{int(chapter / precision) % 60:02}.'
              f'{int(chapter / precision * 1000000) % 1000000:06}')

with soundfile.SoundFile(args.soundfile) as infile:
    if args.format is None:
        args.format = infile.format
        extension = os.path.splitext(args.soundfile)[1]
    else:
        extension = '.' + args.format.lower()

    # Figure out what sample format to read
    dtype = None # use default
    if infile.subtype.startswith('PCM'):
        dtype = 'int32'

    if args.align is None:
        args.align = infile.samplerate
    elif not (infile.samplerate / args.align).is_integer():
        argparser.error(f'Input sample rate {infile.samplerate} is not '
                f'evenly divisible into {args.align} blocks per second.')

    # Calculate split points and track lengths in terms of samples
    blocksize = infile.samplerate // args.align
    splits = [args.round(x * args.align / precision) * blocksize
            for x in chapters]
    # Add an extra split at EOF for the final track if necessary
    if splits[-1] < len(infile):
        splits.append(len(infile))
    lengths = numpy.diff(splits)

    # Seek to the actual start of the first track if necessary
    if splits[0] != 0:
        infile.seek(splits[0])

    # Prepare our output directory
    if args.output != '':
        os.makedirs(args.output, exist_ok=True)

    for track, length in enumerate(lengths):
        outname = os.path.join(args.output, f'{track + 1:0>2}{extension}')
        if not args.overwrite and os.path.exists(outname):
            print(f'{outname} already exists, skipping...')
            continue

        if args.verbose:
            print(f'Writing {outname}...')

        with soundfile.SoundFile(outname, 'w', infile.samplerate,
                infile.channels, infile.subtype, format=args.format) as outf:
            while length > 0:
                rdsize = min(4096, length)
                outf.write(infile.read(rdsize, dtype=dtype))
                length -= rdsize
