from matplotlib import pyplot as plt
from spacepy.pybats import ImfInput
from parse_acedata import parse_from_ruth, parse_from_web

from datetime import timedelta
import numpy as np

imf_orig=ImfInput('imf_jan2005.dat')

print imf_orig.keys()

imf_moments_new=parse_from_ruth('ace_swepam_2005016.txt')

for key in imf_moments_new.keys():
    imf_moments_new[key]=np.array(imf_moments_new[key])

imf_b_new=parse_from_web('ACE_MAG_Data.txt')

for key in imf_b_new.keys():
    imf_b_new[key]=np.array(imf_b_new[key])

from advect1d import step, updateboundary

t0=imf_moments_new['time'][0]

t_u=np.array([(t-t0).total_seconds() for t in imf_moments_new['time']])

t_b=np.array([(t-t0).total_seconds() for t in imf_b_new['time']])

nuMax=0.5

n=1000

x=np.linspace(0,1.5e6,n)
dx=x[1]-x[0]

uIn=imf_moments_new['ux']
u=np.ones(x.shape)*uIn[0]
goodUx=np.where(uIn>-9000)
uyIn=imf_moments_new['uy']
uy=np.ones(x.shape)*uyIn[0]
uzIn=imf_moments_new['uz']
uz=np.ones(x.shape)*uzIn[0]
bxIn=imf_b_new['bx']
bx=np.ones(x.shape)*bxIn[0]
byIn=imf_b_new['by']
by=np.ones(x.shape)*uyIn[0]
bzIn=imf_b_new['bz']
bz=np.ones(x.shape)*uzIn[0]
TIn=imf_moments_new['T']
T=np.ones(x.shape)*TIn[0]


dt=nuMax/np.abs(np.max(u))*dx

rho=u

t=0
tmax=t_u[goodUx][-1]
#tmax=t+10*dt

rhoIn=imf_moments_new['rho']

rho=np.ones(x.shape)*rhoIn[0]
#rho[200:400]=1
#u=np.abs(u)

goodRho=np.where(rhoIn>-9000)
goodUy=np.where(uyIn>-9000)
goodUz=np.where(uzIn>-9000)
goodbx=np.where(bxIn>-900)
goodby=np.where(byIn>-900)
goodbz=np.where(bzIn>-900)
goodT=np.where(TIn>-9000)

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
    step(rho,u,dx,dt,'Minmod')
    step(uy,u,dx,dt,'Minmod')
    step(uz,u,dx,dt,'Minmod')
    step(bx,u,dx,dt,'Minmod')
    step(by,u,dx,dt,'Minmod')
    step(bz,u,dx,dt,'Minmod')
    step(T,u,dx,dt,'Minmod')
    step(u,u,dx,dt,'Minmod')
    updateboundary(rho,u,t,x,imf_b_new['x'],t_b,rhoIn[goodRho],t_u[goodRho],uIn,t_u)
    updateboundary(T,u,t,x,imf_b_new['x'],t_b,TIn[goodT],t_u[goodT],uIn[goodUx],t_u[goodUx])
    updateboundary(uy,u,t,x,imf_b_new['x'],t_b,uyIn[goodUy],t_u[goodUy],uIn[goodUx],t_u[goodUx])
    updateboundary(uz,u,t,x,imf_b_new['x'],t_b,uzIn[goodUz],t_u[goodUz],uIn[goodUx],t_u[goodUx])
    updateboundary(bx,u,t,x,imf_b_new['x'],t_b,bxIn[goodbx],t_b[goodbx],uIn[goodUx],t_u[goodUx])
    updateboundary(by,u,t,x,imf_b_new['x'],t_b,byIn[goodby],t_b[goodby],uIn[goodUx],t_u[goodUx])
    updateboundary(bz,u,t,x,imf_b_new['x'],t_b,bzIn[goodbz],t_b[goodbz],uIn[goodUx],t_u[goodUx])
    updateboundary(u,u,t,x,imf_b_new['x'],t_b,uIn[goodUx],t_u[goodUx],uIn[goodUx],t_u[goodUx])
    dt=nuMax/np.abs(np.min(u))*dx
    t+=dt
    outdata['time'].append(t)
    outdata['ux'].append(u[2])
    outdata['rho'].append(rho[2])
    outdata['uy'].append(uy[2])
    outdata['uz'].append(uz[2])
    outdata['bx'].append(bx[2])
    outdata['by'].append(by[2])
    outdata['bz'].append(bz[2])
    outdata['T'].append(T[2])
    

#while t<tmax:
#    iterate()

fig=plt.figure()
#plt.ylim(-1000,0)
plt.ylim(0,10)
line,=plt.plot(x,rho)

import time
tstart=time.time()


def new_frame(f):
    print f
    for i in range(100):
        iterate()

    line.set_data(x,rho)
    import spacepy.datamodel as dm
    outhdf=dm.SpaceData()
    for key in outdata.keys():
        outhdf[key]=dm.dmarray(outdata[key])
    outhdf.toHDF5('advected.h5')
    now=time.time()
    hours_remaining=((now-tstart)*tmax/t-(now-tstart))/3600
    print hours_remaining,'hours remaining'

from matplotlib import animation
    
ani=animation.FuncAnimation(fig,new_frame,100)

#plt.plot(imf_b_new['time'],imf_b_new['x'])
plt.show()
