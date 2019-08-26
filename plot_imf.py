from spacepy import datamodel as dm
from cdaweb import get_cdf
from datetime import datetime,timedelta
import dateutil.parser
import numpy as np
from advect_imf import load_dscovr

from cache_decorator import cache_result

from matplotlib import pyplot as plt
from matplotlib.gridspec import GridSpec

@cache_result()
def load_omni(dtstart,dtend, proxy=None):
    return get_cdf('sp_phys','OMNI_HRO_1MIN',dtstart,dtend,['BX_GSE','BY_GSM','BZ_GSM','Vx','Vy','Vz','T','proton_density'], proxy=proxy)

proxy=None #('proxy.example.edu:1406', 'https')

# Fetch OMNI data
omnidata=load_omni(datetime(2017,9,6,20),datetime(2017,9,7,5), proxy=proxy)

l1data=load_dscovr(datetime(2017,9,6,20),datetime(2017,9,7,5), proxy=proxy)

# Read advect1d output
advect1d_data=dm.fromHDF5('advected.h5')

# Convert floating point times to datetime objects
epoch=dateutil.parser.parse(advect1d_data['time'].attrs['epoch'])
advect1d_time=[epoch+timedelta(seconds=t) for t in advect1d_data['time']]

varlist=[
    ('$u_x$ (km/s)','ux','Vx'),
    ('$u_y$ (km/s)','uy','Vy'),
    ('$u_z$ (km/s)','uz','Vz'),
    ('$b_x$ (nT)','bx','BX_GSE'),
    ('$b_y$ (nT)','by','BY_GSM'),
    ('$b_z$ (nT)','bz','BZ_GSM'),
    (r'$\rho$ (cm$^{-3}$)','rho','proton_density'),
    ('T (K)','T','T')
]

gs=GridSpec(len(varlist),1)

fig=plt.figure()

axes=[fig.add_subplot(gs[0,0])]
for i in range(1,len(varlist)):
    axes.append(fig.add_subplot(gs[i,0],sharex=axes[0]))

for i,(ylabel,advect1d_name,omni_name) in enumerate(varlist):
    ax=axes[i]

    # Mask out bad OMNI data
    omni_y=omnidata[omni_name]
    mask=(omnidata[omni_name]<omnidata[omni_name].attrs['VALIDMIN'])|(omnidata[omni_name]>omnidata[omni_name].attrs['VALIDMAX'])
    omni_y=np.ma.array(omni_y,mask=mask)

    # Plot OMNI data and advect1d output for this variable
    ax.plot(omnidata['Epoch'],omni_y,label='OMNI')
    ax.plot(advect1d_time,advect1d_data[advect1d_name],label='advect1d')
    l1_t,l1_y=l1data[advect1d_name]
    ax.plot(l1_t,l1_y,label='DSCOVR')
    
    ax.set_ylabel(ylabel)

axes[-1].legend(loc='best')

plt.show()
