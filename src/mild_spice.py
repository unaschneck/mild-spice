import numpy as np
import spiceypy as spice
import typing
from astropy import units
import logging
from typing import Optional
import os

'''
Useful functionality for working with spiceypy
'''

# instrument NAIF ids: https://pirlwww.lpl.arizona.edu/resources/guide/software/SPICE/naif_ids.html
# spacecraft NAIF ids:  https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/naif_ids.html
# planet NAIF ids: https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/naif_ids.html


IMPORTANT_DATES = {
# https://nssdc.gsfc.nasa.gov/planetary/galileo_cl3_time.html
# https://nssdc.gsfc.nasa.gov/planetary/galileo_cl9_time.html
    'C3_START' : '02 November 1996, 16:00 UTC',
    'C3_CA'    : '04 November 1996, 13:30 UTC',
    'C3_END'   : '10 November 1996, 07:00 UTC',
    'C9_START' : '22 June 1997, 16:00 UTC',
    'C9_CA'    : '25 June 1997, 13:47 UTC',
    'C9_END'   : '28 June 1997, 21:12 UTC',
    'C20_CA'   : '5 May 1999, 00:00 UTC',
    'C22_CA'   : '14 August 1999, 00:00 UTC',
    'C23_CA'   : '16 September 1999, 00:00 UTC'
}

CONSTANTS = {
    'CALLISTO_ORBIT_PERIOD' : 16.689*spice.spd()*units.second,
    'JUPITER_RADIUS'        : 69950*1000*units.meter
}


def loadme(metakernel_name: str, _mylog: logging.RootLogger) -> None:

    '''
    load and display kernels
    '''

    spice.furnsh(metakernel_name) # ephemerides and geometric data

    for fname in os.listdir(os.getcwd()):
        if fname.endswith('.ti'):
            txt_kern = os.path.join(os.getcwd(),fname)
            spice.ldpool(txt_kern) # textual kernel variables

    view_kernels(_mylog)

    return

def utc2eph(utc_times: typing.List[str]) -> typing.List[float]:

    '''
    takes a list of UTC times and converts to a list of ephemersis times
    '''

    ephemeris_times = [spice.str2et(time) for time in utc_times]

    return ephemeris_times

def view_kernels(_mylog: logging.RootLogger) -> None:

    '''
    show name of all loaded kernels
    '''

    num_kernels = spice.ktotal('ALL')
    _mylog.info(f"{num_kernels} loaded kernels from {spice.kdata(0,'all',100,100,100)[0]}: " )
    for i in range(num_kernels):
        if i != 0:
            print("#",i,"\t",spice.kdata(i,'all',100,100,100)[0])

    return

def show_toolkit_version() -> None:

    '''
    print installed cspice toolkit (tk) version (vrsn)
    '''

    print(spice.tkvrsn('TOOLKIT'))
    return

def make_pass(start_time: str, end_time: str,num_pts: int = 100) -> typing.List[float]:

    '''
    make an array of times from start to end of pass
    '''

    pass_time = utc2eph([start_time,end_time])
    pass_time = np.linspace(pass_time[0],pass_time[-1],num=num_pts)

    return pass_time

def make_logger(logname="mylog", level=logging.WARNING, log_to_file=False) -> logging.RootLogger:

    '''
    make a log file for debugging and recording
    '''
    _personal_note_logger = logging.getLogger()
    _personal_note_logger.setLevel(level)

    _formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(funcName)s() [line %(lineno)d] - %(message)s'
    )

    _stream_handler = logging.StreamHandler()
    _stream_handler.setFormatter(_formatter)
    _personal_note_logger.addHandler(_stream_handler)

    # save to .log file
    if log_to_file:
        _file_handler = logging.FileHandler(logname + '.log')
        _file_handler.setFormatter(_formatter)
        _personal_note_logger.addHandler(_file_handler)

    return _personal_note_logger



