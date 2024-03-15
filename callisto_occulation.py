import numpy as np
import matplotlib.pyplot as plt
import spiceypy as spice
import typing


import mild_spice as mild


def where_is(name: str,times: typing.List[float]) -> np.ndarray:

    '''
    find position of object [name] relative to jupiter
    '''

    obj_pos = spice.spkpos(name, times, 'J2000', 'NONE', 'JUPITER')[0]

    return obj_pos.T

def callisto_orbit_time() -> typing.List[float]:

    '''
    find orbital position of callisto for one full orbit
    '''

    startt = spice.str2et('02 November 1996, 16:00 UTC')
    endt = startt + mild.CONSTANTS['CALLISTO_ORBIT_PERIOD'].value
    orbit_time = np.linspace(startt,endt,num=100)

    return orbit_time

def occult_times() -> typing.List[float]:
    '''
    find times when callisto is occulting Galileo
    '''

    dark_times = spice.gfoclt(occtype="ANY",front="CALLISTO",back="SUN",obsrvr="GALILEO ORBITER")
    print(dark_times[0:3])

    return



def main() -> None:

    # load metakernel that directs to all kernels
    mild.loadme("./Galileo_Callisto_MetaKernal.txt")

    RJ = int((mild.CONSTANTS['JUPITER_RADIUS'].value)/1000)

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


    # Clean up the kernels
    spice.kclear()

if __name__ == '__main__':
    main()
