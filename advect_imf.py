from matplotlib import pyplot as plt
from spacepy import datamodel as dm
from cdaweb import get_cdf

from cache_decorator import cache_result

from datetime import datetime, timedelta
import numpy as np

@cache_result(clear=False)
def load_acedata(tstart,tend):
    """
    Fetch ACE data from CDAWeb

    tstart: Desired start time
    tend: Desired end time

    Returns: A dictionary of tuples, each containing an array of times and an array of ACE observations for a particular variable
    """

    # Download SWEPAM and Mag data from CDAWeb
    swepam_data=get_cdf('sp_phys','AC_H0_SWE',tstart,tend,['Np','V_GSM','Tpr','SC_pos_GSM'])
    mag_data=get_cdf('sp_phys','AC_H0_MFI',tstart,tend,['BGSM'])

    # Dictionary to store all the data from ACE
    acedata={
        'T':(swepam_data['Epoch'],swepam_data['Tpr']),
        'rho':(swepam_data['Epoch'],swepam_data['Np']),
    }

    # Store all the vector data in the array
    for i,coord in enumerate('xyz'):
        for dataset,local_name,cdaweb_name in [(mag_data,'b','BGSM'),
                                 (swepam_data,'u','V_GSM'),
                                 (swepam_data,'','SC_pos_GSM')]:
            t,values=dataset['Epoch'],dataset[cdaweb_name][:,i]
            
            # Grab the appropriate component from
            # VALIDMIN and VALIDMAX attributes
            values.attrs['VALIDMIN']=values.attrs['VALIDMIN'][i]
            values.attrs['VALIDMAX']=values.attrs['VALIDMAX'][i]

            # Store in acedata dict
            acedata[local_name+coord]=t,values

    for var in acedata.keys():
        
        # Restrict to only valid data
        t_var,varIn=acedata[var]
        goodpoints=(varIn<varIn.attrs['VALIDMAX']) & (varIn>varIn.attrs['VALIDMIN'])
        t_var,varIn=t_var[goodpoints],varIn[goodpoints]

        acedata[var]=(t_var,varIn)
        
    return acedata
        

def initialize(acedata,advect_vars=['ux','uy','uz','bx','by','bz','rho','T'],ncells=1000):
    """
    Advect ACE observations to the bow shock

    acedata: Dictionary of ACE data, structured in the form returned from load_acedata
    advect_vars: Keys in the ACE data dictionary for variables that should be advected
    ncells: Number of cells in the computational grid
    """

    # Make the grid
    x=np.linspace(0,1.5e6,ncells)

    # ux must be advected regardless
    if 'ux' not in advect_vars:
        advect_vars=list(advect_vars)+['ux']

    # Start time of simulation is first point for which all variables have valid data
    t0=np.max([t[0] for var,(t,values) in acedata.iteritems()])

    for var in acedata.keys():

        t_var,values=acedata[var]

        # Subtract epoch time from time arrays and convert them to seconds
        t_var=np.array([(t-t0).total_seconds() for t in t_var])

        acedata[var]=t_var,values

    # Initialize simulation state vectors
    state={var:np.ones([ncells])*values[0] for var,[t,values] in acedata.iteritems() if var in advect_vars}
    state['x']=x

    # Dictionary to hold output variables
    outdata={var:[] for var in advect_vars}
    outdata['time']=[]

    return state,outdata,t0

def iterate(state,t,outdata,acedata,nuMax=0.5):
    """
    nuMax: Maximum allowed CFL
    """

    from advect1d import step, updateboundary

    u=state['ux']
    x=state['x']
    dx=x[1]-x[0]

    # Variables to be advected include everything in state except 'x'
    advect_vars=state.keys()
    advect_vars.remove('x')

    # Make sure ux is at end of list (ux must be advected list to get consistent results for the other variables)
    advect_vars.remove('ux')
    advect_vars.append('ux')
    
    # Update boundary conditions with values at new time step
    for var in advect_vars:
        
        a=state[var]
        var_t,values=acedata[var]
        x_ace_t,x_ace=acedata['x']
        updateboundary(a,t,x,x_ace,x_ace_t,values,var_t)
        
    # Find the time step
    dt=nuMax/np.abs(np.min(u))*dx
        
    # Step each variable forward in time
    for var in advect_vars:
        a=state[var]
        step(a,u,dx,dt,'Minmod')

        # Store output state
        outdata[var].append(a[2])

    # Append time to output state
    outdata['time'].append(t+dt)

    return dt

if __name__=='__main__':

    # Fetch ACE data
    acedata=load_acedata(datetime(2018,1,1),datetime(2018,1,4))

    # Initialize the simulation state
    state,outdata,t0=initialize(acedata)

    # Stop time of simulation is last point for which all variables have valid data
    tmax=np.min([t[-1] for var,(t,values) in acedata.iteritems()])

    # Step forward in time
    t=0
    i=0
    while t<tmax:
        if i%100==0: print t/tmax
        dt=iterate(state,t,outdata,acedata)
        t+=dt
        i+=1

    # Write output to disk
    import spacepy.datamodel as dm
    outhdf=dm.SpaceData()
    for key in outdata.keys():
        outhdf[key]=dm.dmarray(outdata[key])
    outhdf['time'].attrs['epoch']=t0.isoformat()
    outhdf.toHDF5('advected.h5')
