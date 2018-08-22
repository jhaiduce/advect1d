from matplotlib import pyplot as plt
from parse_acedata import parse_from_ruth, parse_from_web

from datetime import timedelta
import numpy as np

# Load the ACE SWEPAM data
imf_moments_new=parse_from_ruth('ace_swepam_2005016.txt')

# Convert lists to numpy arrays
for key in imf_moments_new.keys():
    imf_moments_new[key]=np.array(imf_moments_new[key])

# Load the ACE MAG data
imf_b_new=parse_from_web('ACE_MAG_Data.txt')

# Convert lists to numpy arrays
for key in imf_b_new.keys():
    imf_b_new[key]=np.array(imf_b_new[key])

from advect1d import step, updateboundary

# Use time of first SWEPAM data as epoch time
t0=imf_moments_new['time'][0]

# Subtract epoch time from time arrays and convert them to seconds
t_u=np.array([(t-t0).total_seconds() for t in imf_moments_new['time']])
t_b=np.array([(t-t0).total_seconds() for t in imf_b_new['time']])

# Maximum CFL
nuMax=0.5

# Number of grid points
n=1000

# Make the grid
x=np.linspace(0,1.5e6,n)
dx=x[1]-x[0]

# X velocity input
uIn=imf_moments_new['ux']

# X velocity state array
u=np.ones(x.shape)*uIn[0]

# Y velocity input
uyIn=imf_moments_new['uy']

# Y velocity state array
uy=np.ones(x.shape)*uyIn[0]

# Z velocity input
uzIn=imf_moments_new['uz']

# Z velocity state array
uz=np.ones(x.shape)*uzIn[0]

# Bx input
bxIn=imf_b_new['bx']

# Bx state array
bx=np.ones(x.shape)*bxIn[0]

# By input
byIn=imf_b_new['by']

# By state array
by=np.ones(x.shape)*uyIn[0]

# Bz input
bzIn=imf_b_new['bz']

# Bz state array
bz=np.ones(x.shape)*uzIn[0]

# Temperature input
TIn=imf_moments_new['T']

# Temperature state array
T=np.ones(x.shape)*TIn[0]

# Density input array
rhoIn=imf_moments_new['rho']

# Density state array
rho=np.ones(x.shape)*rhoIn[0]

# Initial time step
dt=nuMax/np.abs(np.max(u))*dx

# Set simulation time to zero, and simulation stop time to wherever data ends
t=0
tmax=t_u[goodUx][-1]

# Boolean arrays showing where valid data is present in each input array
goodUx=np.where(uIn>-9000)
goodRho=np.where(rhoIn>-9000)
goodUy=np.where(uyIn>-9000)
goodUz=np.where(uzIn>-9000)
goodbx=np.where(bxIn>-900)
goodby=np.where(byIn>-900)
goodbz=np.where(bzIn>-900)
goodT=np.where(TIn>-9000)

# Dictionary to hold output variables
outdata={
    'time':[],
    'rho':[],
    'ux':[],
    'uy':[],
    'uz':[],
    'bx':[],
    'by':[],
    'bz':[],
    'T':[],
    }

import os
if os.path.exists('advected.h5'):
    import sys
    print 'Output file already exists'
    sys.exit()

def iterate():
    global t,dt

    # Step each variable forward in time
    step(rho,u,dx,dt,'Minmod')
    step(uy,u,dx,dt,'Minmod')
    step(uz,u,dx,dt,'Minmod')
    step(bx,u,dx,dt,'Minmod')
    step(by,u,dx,dt,'Minmod')
    step(bz,u,dx,dt,'Minmod')
    step(T,u,dx,dt,'Minmod')
    
    # Velocity must be stepped last since the others depend on it
    step(u,u,dx,dt,'Minmod')

    # Update boundary conditions with values at new time step
    updateboundary(rho,u,t,x,imf_b_new['x'],t_b,rhoIn[goodRho],t_u[goodRho],uIn,t_u)
    updateboundary(T,u,t,x,imf_b_new['x'],t_b,TIn[goodT],t_u[goodT],uIn[goodUx],t_u[goodUx])
    updateboundary(uy,u,t,x,imf_b_new['x'],t_b,uyIn[goodUy],t_u[goodUy],uIn[goodUx],t_u[goodUx])
    updateboundary(uz,u,t,x,imf_b_new['x'],t_b,uzIn[goodUz],t_u[goodUz],uIn[goodUx],t_u[goodUx])
    updateboundary(bx,u,t,x,imf_b_new['x'],t_b,bxIn[goodbx],t_b[goodbx],uIn[goodUx],t_u[goodUx])
    updateboundary(by,u,t,x,imf_b_new['x'],t_b,byIn[goodby],t_b[goodby],uIn[goodUx],t_u[goodUx])
    updateboundary(bz,u,t,x,imf_b_new['x'],t_b,bzIn[goodbz],t_b[goodbz],uIn[goodUx],t_u[goodUx])
    updateboundary(u,u,t,x,imf_b_new['x'],t_b,uIn[goodUx],t_u[goodUx],uIn[goodUx],t_u[goodUx])

    # Find new time step
    dt=nuMax/np.abs(np.min(u))*dx

    # Next time
    t+=dt

    # Store output state
    outdata['time'].append(t)
    outdata['ux'].append(u[2])
    outdata['rho'].append(rho[2])
    outdata['uy'].append(uy[2])
    outdata['uz'].append(uz[2])
    outdata['bx'].append(bx[2])
    outdata['by'].append(by[2])
    outdata['bz'].append(bz[2])
    outdata['T'].append(T[2])

# Figure to show state
fig=plt.figure()
plt.ylim(0,10)
line,=plt.plot(x,rho)

import time
tstart=time.time()


def new_frame(f):
    
    # Step forward a bunch of iterations so we don't redraw on every iteration
    for i in range(100):
        iterate()

    # Update density line plot
    line.set_data(x,rho)

    # Write output to disk
    import spacepy.datamodel as dm
    outhdf=dm.SpaceData()
    for key in outdata.keys():
        outhdf[key]=dm.dmarray(outdata[key])
    outhdf.toHDF5('advected.h5')
    now=time.time()
    hours_remaining=((now-tstart)*tmax/t-(now-tstart))/3600
    print hours_remaining,'hours remaining'

from matplotlib import animation

# Animation object
ani=animation.FuncAnimation(fig,new_frame,100)

plt.show()
