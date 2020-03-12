from astropy.io import fits
from astropy.table import Table
import numpy as np
import argparse
import sys

def parseargs():
    parser = argparse.ArgumentParser()

    parser.add_argument("infile", help="ACD count file to process", type=argparse.FileType('r'))
    parser.add_argument("-o", "--outfile", help="Output filename", default="burstcube_tte.fit")

    args = parser.parse_args()
    return args

def bintablehdu_constructor(data, colnames, coltypes, hduname):
    table = Table(rows=data, names=colnames, dtype=coltypes)
    bintablehdu = fits.BinTableHDU(table, name=hduname)
    return bintablehdu

def imagehdu_constructor():
    
    return imagehdu

if __name__ == '__main__':
    # Read ADC output text file
    # Expected Format:
    ##############################################
    # Detector  Timestamp  Baseline  Pulseheight #
    ##############################################
    args = parseargs()
    outfile = args.outfile
    f = args.infile
    
    lines = f.readlines()
    input = []
    
    for x in lines:
        input.append(tuple((x.split(' ')[0],
                            x.split(' ')[1],
                            x.split(' ')[2],
                            x.split(' ')[3].strip())))
    f.close()

    elements =  input.pop(0)
    
    tstart = (input[0])[1]
    tstop = (input[-1])[1]

    # Extract Timestamps and scaled pulseheights from each event
    # and store in the scaledpulse list
    scaledpulse = []
    
    for x in input:
        scaledpulse.append([int(x[1]),int(x[3])-int(x[2])])
        
    # Define Energy Channels
    # Current: 64 channels hardcoded in increments
    # of 26
    channels = []
    emin = 0 # Min Energy
    emax = 384 # Max Energy 
    i = 1
    
    while i < 65:
        channels.append([i,emin,emax])
        emin = emax+1
        emax = emax+6 # Energy Channel Steps defined here
        i += 1
        
    # Match each scaled pulse with an energy channel range
    # and create a list of timestamp/channel pairs
    eventpairs = []
    
    for x in scaledpulse:
        for y in channels:
            if x[1] in range(y[1],y[2]+1,1):
                eventpairs.append([x[0],y[0]])

    primarykeywords = { 'CREATOR' : 'ADCtoTTE v1.0',
                        'FILETYPE' : 'BURSTCUBE PHOTON LIST',
                        'FILE-VER' : '1.0.0',
                        'DATATYPE' : 'TTE',
                        'TELESCOP' : 'BURSTCUBE',
                        'INSTRUME' : 'BURSTCUBE'}

    primaryheader = fits.Header(primarykeywords)
    
    # Construct the output HDUs
    primary_hdu = fits.PrimaryHDU(header=primaryheader)
    ebounds_hdu = bintablehdu_constructor(channels,('CHANNEL','E_MIN','E_MAX'), ('short','float','float'),'EBOUNDS')
    events_hdu = bintablehdu_constructor(eventpairs,('EVENT','PHA'), ('double','short'),'EVENTS')
    gti_hdu = bintablehdu_constructor([[tstart,tstop]],('TSTART','TSTOP'), ('double','double'), 'GTI')
    hdulist = fits.HDUList([primary_hdu,ebounds_hdu,events_hdu,gti_hdu])
    
    # Write out the tte file
    hdulist.writeto(outfile)
