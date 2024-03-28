# Built-in Python functions
import sys
import logging

# External Python libraries
import numpy as np
import matplotlib.pyplot as plt
import spiceypy as spice
import typing
from matplotlib.colors import LinearSegmentedColormap

# Local Python libraries
import mild_spice as mild


_mylog = mild.make_logger(level=logging.INFO)


def gal_to_earth_vec(times):
    '''
    find if the boom's FOV is pointing at Earth
    '''

    intersection_state = []

    abcor = 'NONE'

    for et in times:
        state, _ = spice.spkezr('GALILEO ORBITER', et, 'J2000', abcor, 'EARTH')
        galileo_position = state[:3]

        earth_position, _ = spice.spkezr('EARTH', et, 'J2000', abcor, 'GALILEO ORBITER')
        direction_vector = np.array(galileo_position) - np.array(earth_position[:3])

        _mylog.critical("This doesn't work because there is not FOV info for the boom and \
        no SPICE info for magnetometer. Galileo predates SPICE, so they are still putting \
        together the mission kernels.")
        intersection_state.append(spice.fovray('-77024', direction_vector, 'J2000', abcor, 'GALILEO ORBITER', et)[0])


    return intersection_state



def where_is(name: str,times: typing.List[float]) -> np.ndarray:

    '''
    find position of object [name] relative to jupiter
    '''

    abcor = 'LT+S'

    obj_pos = spice.spkpos(name, times, 'J2000', abcor, 'JUPITER')[0]

    return obj_pos.T

def callisto_orbit_time() -> typing.List[float]:

    '''
    find orbital position of callisto for one full orbit
    '''

    startt = spice.str2et('02 November 1996, 16:00 UTC')
    endt = startt + mild.CONSTANTS['CALLISTO_ORBIT_PERIOD'].value
    orbit_time = np.linspace(startt,endt,num=100)

    return orbit_time

def mag_see_earth() -> typing.List[bool]:

    '''
    find times when Galileo boom pointing at Earth
    '''

    inst = -77024



    return

def wrt_jupiter(times: typing.List[float],NAIF: int) -> typing.Tuple[typing.List[np.ndarray], typing.List[np.ndarray]]:

    pos = []
    vel = []

    abcor = 'LT+S'
    for et in times:
        state_vec = spice.spkacs(NAIF,et,"J2000", abcor,599)[0]
        pos.append(state_vec[:3])
        vel.append(state_vec[3:])

    return pos, vel




def main() -> None:


    # load metakernel that directs to all kernels
    mild.loadme("Galileo_Callisto_MetaKernal.txt", _mylog)

    RJ = int((mild.CONSTANTS['JUPITER_RADIUS'].value)/1000) # Jupiter radius

    C3_pass = mild.make_pass(mild.IMPORTANT_DATES['C3_START'], mild.IMPORTANT_DATES['C3_END'])
    C9_pass = mild.make_pass(mild.IMPORTANT_DATES['C9_START'], mild.IMPORTANT_DATES['C9_END'])

    CA = [mild.IMPORTANT_DATES['C3_CA'],
            mild.IMPORTANT_DATES['C9_CA'],
            mild.IMPORTANT_DATES['C20_CA'],
            mild.IMPORTANT_DATES['C22_CA'],
            mild.IMPORTANT_DATES['C23_CA']]

    # find all positions
    calli_ca_pos = where_is('CALLISTO',mild.utc2eph(CA))
    gal_C3_pos = where_is('GALILEO ORBITER',C3_pass)
    gal_C9_pos = where_is('GALILEO ORBITER',C9_pass)
    cal_orbit_pos = where_is('CALLISTO', callisto_orbit_time())
    sun_pos = np.mean(where_is('SUN',callisto_orbit_time()),axis=1)

    # make state


    spos, svel = wrt_jupiter(mild.utc2eph(CA),10)
    cpos, cvel = wrt_jupiter(mild.utc2eph(CA),504)

    vis2gal = gal_to_earth_vec(mild.utc2eph(CA))
    print(vis2gal)

    '''
    fig, ax = plt.subplots()
    sunx = [posi[0] for posi in spos]
    suny = [posi[1] for posi in spos]
    sunz = [posi[2] for posi in spos]
    sunvx = [veli[0] for veli in svel]
    sunvy = [veli[1] for veli in svel]
    sunvz = [veli[2] for veli in svel]

    calx = [posi[0] for posi in cpos]
    caly = [posi[1] for posi in cpos]
    calz = [posi[2] for posi in cpos]
    calvx = [veli[0] for veli in cvel]
    calvy = [veli[1] for veli in cvel]
    calvz = [veli[2] for veli in cvel]

    relative_time = [t - min(mild.utc2eph(CA)) for t in mild.utc2eph(CA)]
    colors = [(0.8, 0.8, 1), (0, 0, 0.5)]  # Light blue to dark blue
    colorc = [(1, 0.8, 0.8), (0.5, 0, 0)]  # Light red to dark red
    cm = LinearSegmentedColormap.from_list('custom_cmap', colors)
    cmc = LinearSegmentedColormap.from_list('custom_cmap', colorc)

    plt.quiver(np.divide(sunx,RJ),np.divide(suny,RJ),sunvx,sunvy,color="k", scale = 200)
    plt.scatter(np.divide(sunx,RJ),np.divide(suny,RJ),c=relative_time, cmap=cm, vmin=min(relative_time), vmax=max(relative_time),label='sun')
    plt.scatter(np.divide(calx,RJ),np.divide(caly,RJ),c='r', label='callisto')
    plt.colorbar(label='Time')
    plt.legend()
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.show()


    # PLOT STUFF
    fig, ax = plt.subplots()

    plt.plot(np.divide(cal_orbit_pos[0],RJ), np.divide(cal_orbit_pos[1],RJ), color="black", label = 'callisto orbit')
    plt.plot(np.divide(gal_C3_pos[0, :], RJ), np.divide(gal_C3_pos[1, :], RJ), color ="blue", label='C3')
    plt.plot(np.divide(gal_C9_pos[0, :], RJ), np.divide(gal_C9_pos[1, :], RJ), color ="red", label='C9')


    ax.add_patch(plt.Circle((np.divide(calli_ca_pos[0,0], RJ), np.divide(calli_ca_pos[1,0], RJ)), 1, color='blue'))
    ax.add_patch(plt.Circle((np.divide(calli_ca_pos[0,1], RJ), np.divide(calli_ca_pos[1,1], RJ)), 1, color='red'))
    ax.add_patch(plt.Circle((np.divide(calli_ca_pos[0,2], RJ), np.divide(calli_ca_pos[1,2], RJ)), 1, color='yellow'))
    ax.add_patch(plt.Circle((np.divide(calli_ca_pos[0,3], RJ), np.divide(calli_ca_pos[1,3], RJ)), 1, color='yellow'))
    ax.add_patch(plt.Circle((np.divide(calli_ca_pos[0,4], RJ), np.divide(calli_ca_pos[1,4], RJ)), 1, color='yellow'))

    ax.add_patch(plt.Circle((0, 0), 1, color='k'))

    plt.arrow(0, 0, (sun_pos[0]/1000)/RJ, (sun_pos[1]/1000)/RJ,width = 0.05,head_width = 1)
    plt.legend()
    plt.xlabel('X [$R_J$]')
    plt.ylabel('Y [$R_J$]')

    plt.show()
    '''

    # Clean up the kernels
    spice.kclear()

if __name__ == '__main__':
    main()
