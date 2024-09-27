# Built-in Python functions
import sys
import logging

# External Python libraries
import math
import numpy as np
import matplotlib.pyplot as plt
import spiceypy as spice
import typing
from matplotlib.colors import LinearSegmentedColormap
from datetime import datetime

# Local Python libraries
import mild_spice as mild

# GLOBAL VARIABLES
_mylog = mild.make_logger(level=logging.INFO)
callisto_radius = 2410.3  # km
K = 1000*(1.2e4)# keV -> Kelvin
kg = 1.66e-27 # amu -> kg
R = 8.314 # ideal gas law constant

'''
CALCULATES THE EXPECTED PLASMA FIELD FROM PILEUP FOR THE CALLISTO FLYBYS

'''
def extract_time(data,time) -> str:
    '''
    extract the formatted time from the .tab file
    '''
    line_no = data.splitlines()[time]
    timestamp_str = line_no.split()[0]
    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%f')
    formatted_timestamp = timestamp.strftime('%d %B %Y, %H:%M:%S.%f UTC')
    
    return formatted_timestamp


def calc_A(beta,P1,P0,M0) -> float:
    ''' 
    Calculate magnitude of plasma effect for balanced 
    tangential discontinuity
    
    beta = magnetosphere beta
    P1 = pressure of ionosphere
    P0 = pressure of magnetosphere
    M0 = mach number
    '''
    
    gamma = 5/3
    A = beta*(1 - P1/P0) + beta*gamma*(M0**2) + 1
    A = A**0.5
    
    return A

class Model():
    '''
    plasma toy model to match Liuzzo shape
    '''
    def __init__(self,A,Bms,distance=None,theta=None):
        self.plasma_Amp = A                                             # A*background field
        self.theta_fall_off = 1                                         # cos^x(theta)
        self.r_fall_off = 3                                             # r^-x
        self.range_fall_off = callisto_radius*1000                                         # r/x
        self.Bms = Bms
        
    def calc_amp_field(self,distance,theta):
        #distance = [d / (callisto_radius * 1000) for d in distance]     # callisto radii to surface
        distance = np.array(distance) + callisto_radius*1000
        theta = np.array(theta)
        model_strength = self.Bms + self.plasma_Amp * (((distance/self.range_fall_off) ** (-self.r_fall_off))*(np.cos(theta) ** self.theta_fall_off))


        return model_strength   

def main() -> None:


    # load metakernel that directs to all kernels
    mild.loadme("Galileo_Callisto_MetaKernal.txt", _mylog)   

    closest_approach_times = {
        'C3': spice.str2et('04 November 1996, 13:34 UTC'),
        'C9': spice.str2et('25 June 1997, 13:47 UTC'),
        'C10': spice.str2et('17 September 1997, 00:18 UTC'),
        #'C20': spice.str2et('5 May 1999, 13:56 UTC'),
        'C21': spice.str2et('30 June 1999, 07:46 UTC'),
        'C22': spice.str2et('14 August 1999, 08:30 UTC'),
        'C23': spice.str2et('16 September 1999, 17:27 UTC'),
        'C30': spice.str2et('25 May 2001, 11:23 UTC')
    }

    # Loop through each flyby
    for label, et in closest_approach_times.items():
        
        if label.startswith('C') and label[1:].isdigit() and 1 <= int(label[1:]) <= 30:
            mag_file = f'ORB{int(label[1:]):02}_CALL_CPHIO.TAB'
        else:
            raise Exception("MAG FILE NOT FOUND") 
            
        # read in mag data
        f = open(mag_file, 'r')
        data = f.read()
        f.close()
        time_steps = data.splitlines()


        # Initialize lists to hold position data
        positions = []
        thetas = []
        BX = []
        BY = []
        BZ = []
        BMAG = []
        X = []
        Y = []
        Z = []

        # time relative to closest approach
        normalized_time_steps = np.linspace(spice.str2et(extract_time(data,0)),spice.str2et(extract_time(data,-1)),num=len(time_steps))
        normalized_time_steps -= et

        for t in range(len(time_steps)):
            #   position, _ = spice.spkpos('GALILEO ORBITER', spice.str2et(extract_time(data,t)), 'IAU_CALLISTO', 'NONE', 'CALLISTO')
            x = float(data.splitlines()[t].split()[5])*callisto_radius*1000 # meters (in direction of travel)
            y = float(data.splitlines()[t].split()[6])*callisto_radius*1000 # meters (towards jupiter)
            z = float(data.splitlines()[t].split()[7])*callisto_radius*1000 # meters x cross y
            
            theta = np.arctan2(z,np.sqrt(x**2 + y**2))                   # angle relative to xy plane (equator)
            
            positions.append([x,y,z])
            thetas.append(theta)
            BX.append(float(data.splitlines()[t].split()[1]))           # nT
            BY.append(float(data.splitlines()[t].split()[2]))           # nT
            BZ.append(float(data.splitlines()[t].split()[3]))           # nT
            BMAG.append(float(data.splitlines()[t].split()[4]))         # nT
            X.append(x)
            Y.append(y)
            Z.append(z)
        
        

        positions = np.array(positions)
    
        # remove missing values
        BX = [np.nan if value == 999999.99 else value for value in BX]
        BY = [np.nan if value == 999999.99 else value for value in BY]
        BZ = [np.nan if value == 999999.99 else value for value in BZ]
        BMAG = [np.nan if value == 999999.99 else value for value in BMAG]
        X = [np.nan if value == 999.99999 else value for value in X]
        Y = [np.nan if value == 999.99999 else value for value in Y]
        Z = [np.nan if value == 999.99999 else value for value in Z]
        
    
        # Calculate the distance from Callisto's center for each position
        distances = np.linalg.norm(positions,axis=1) - callisto_radius*1000 # meters to surface
        
        # Find the minimum distance and its corresponding position
        min_distance = np.min(distances) 
        min_distance_index = np.argmin(distances)
        closest_position = positions[min_distance_index]
        
        # From Kliore
        
        rho1 = 2e4 # m-3
        T1 = 2*K # K
        rho2 = 5e5 # m-3
        T2 = (100/1000)*K# K
        m = 5.49e-7 # molar mass electron kg/mol

        P1 = (rho1/m)*R*T1
        P2 = (rho2/m)*R*T2
        P_ionosphere = (P1 + P2)/2 #max([P1, P2])
        print(f'P_ionosphere : {P_ionosphere}')
        
        # varies between regions (Seufert+2012, Table 1.2 and t)
        beta = [64,0.6] 
        MA = [2.8,0.02,8.5]
        MS = [0.4,0.03,1.2]
        B0 = [30,30]#[4,42]
        rho_mag = [1e5,1e4,5e5]  
        T_mag = (635/1000)*K 
        m_mag = [16*kg ,2*kg]     
        
        M1 = MS[0]
        M2 = MS[1]
        M3 = MS[2]

        P_mag1 = (rho_mag[0]/m_mag[0])*R*T_mag
        P_mag2 = (rho_mag[1]/m_mag[1])*R*T_mag
        P_mag3 = (rho_mag[2]/m_mag[1])*R*T_mag
        
        print(f'P_mag1 : {P_mag1}')
        print(f'P_mag2 : {P_mag2}')
        print(f'P_mag3 : {P_mag3}')
        
        
        # CALCULATE AMPLITUDE OF INTENSIFICATION
        A_in = calc_A(beta[0],P_ionosphere,P_mag1,M1)
        A_out1 = calc_A(beta[1],P_ionosphere,P_mag2,M2)
        A_out2 = calc_A(beta[1],P_ionosphere,P_mag3,M3)

        # CALCULATE FIELD FROM PLASMA
        plasmaB_in = B0[0]*A_in # in current sheet
        plasmaB_out1 = B0[1]*A_out1 # in lobe (min)
        plasmaB_out2 = B0[1]*A_out2 # in lobe (max)
        myA = [plasmaB_in, plasmaB_out1, plasmaB_out2]
        print(f'plasma B in: {plasmaB_in}')
        print(f'plasma B out1: {plasmaB_out1}')
        print(f'plasma B out2: {plasmaB_out2}')

        
        # construct magnetic field from pile-up along flyby
        plasma1 = Model(A=myA[0],Bms=B0[0])
        rad_mag1 = plasma1.calc_amp_field(distance = distances,theta = thetas)
        plasma2 = Model(A=myA[1],Bms=B0[1])
        rad_mag2 = plasma2.calc_amp_field(distance = distances,theta = thetas)
        plasma3 = Model(A=myA[2],Bms=B0[1])
        rad_mag3 = plasma3.calc_amp_field(distance = distances,theta = thetas)

        
        # plots
        plt.figure(figsize=(8, 6))
        plt.plot(normalized_time_steps, rad_mag1, color= 'red', label=f'A ={round(myA[0],2)} (current sheet)')
        plt.plot(normalized_time_steps, rad_mag2, color='blue',label=f'A ={round(myA[1],2)} (lobe)')
        plt.plot(normalized_time_steps, rad_mag3, color='blue',label=f'A ={round(myA[2],2)} (lobe)')
        plt.fill_between(normalized_time_steps, rad_mag2, rad_mag3, color='blue', alpha = 0.2)
        plt.plot(normalized_time_steps, BMAG, color='black',label='Bmag')

        plt.xlabel('time relative to closest approach)')
        plt.ylabel('|B| nT')
        plt.legend()
        plt.title(label)
        plt.show()
        
        # Create subplots for XY and XZ projections
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

        # XY Projection
        ax1.plot(X, Y, color='blue', label='Trajectory')
        ax1.scatter(X[0],Y[0], color='green', label='start')
        circle_xy = plt.Circle((0, 0), callisto_radius*1000, color='gray', fill=True, linestyle='--', label='Callisto')
        ax1.add_artist(circle_xy)
        ax1.scatter(closest_position[0], closest_position[1], color='red', s=100, label='Closest Approach')
        ax1.set_xlabel('X (m)')
        ax1.set_ylabel('Y (m)')
        ax1.set_title(f'XY Projection (Closest Approach: {min_distance/1000:.2f} km)')
        ax1.legend()
        ax1.grid(True)    


        # XZ Projection
        ax2.plot(X, Z, color='blue', label='Trajectory')
        ax2.scatter(X[0], Z[0], color='green', label='start')
        circle_xz = plt.Circle((0, 0), callisto_radius*1000, color='gray', fill=True, linestyle='--', label='Callisto')
        ax2.add_artist(circle_xz)
        ax2.scatter(closest_position[0], closest_position[2], color='red', s=100, label='Closest Approach')

        ax2.set_xlabel('X (m)')
        ax2.set_ylabel('Z (m)')
        ax2.set_title(f'XZ Projection (Closest Approach: {min_distance/1000:.2f} km)')
        ax2.legend()
        ax2.grid(True)
        

        
        plt.show()
        
    # Clean up the kernels
    spice.kclear()


if __name__ == '__main__':
    main()





