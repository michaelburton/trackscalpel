import os
from . import MPLS

def read_chapters(mpls):
    header, _ = MPLS.load_header(mpls)

    # Read play items and calculate each PlayItem's absolute start time
    mpls.seek(header['PlayListStartAddress'], os.SEEK_SET)
    pl, _ = MPLS.load_PlayList(mpls)
    duration = 0
    for item in pl['PlayItems']:
        item['INTimeMod'] = duration - item['INTime']
        duration += item['OUTTime'] - item['INTime']

    # And now the playlist marks
    mpls.seek(header['PlayListMarkStartAddress'], os.SEEK_SET)
    marks, _ = MPLS.load_PlayListMark(mpls)
    # Each PlayMark's timestamp is given relative to its PlayItem's InTime,
    # and so needs to be corrected to absolute time
    chapters = [mark['MarkTimeStamp'] +
            pl['PlayItems'][mark['RefToPlayItemID']]['INTimeMod']
            for mark in marks['PlayListMarks'] if mark['MarkType'] == 1]

    return chapters, 45000

def align_splits(chapters, precision, samplerate, align, rounder):
    blocksize = samplerate // align
    return [rounder(x * align / precision) * blocksize for x in chapters]
