import limiters
import numpy as np

def flux(u,a,dx,dt,limiter):
    """
    Compute fluxes between cells

    u: Quantity to be passively advected
    a: Velocity of flow
    dx: Cell size
    dt: Time step
    limiter: String containing the name of one the flux limiter functions in limiters.py
    """

    # Get the function to call for the flux limiter
    S=getattr(limiters,limiter)

    # Gradient across cell at left side of each face
    sm=(u[1:-2]-u[:-3])/dx
    
    # Gradient across cell at right side of each face
    sp=(u[2:-1]-u[1:-2])/dx

    # Separate the velocity into strictly positive and strictly negative vectors, for implementing the upwind scheme
    ap=np.maximum(a,0)
    am=np.minimum(a,0)

    # Compute positive and negative fluxes across each face
    fp=ap[1:-2]*(u[1:-2]+dx/2*(1-a[1:-2]*dt/dx)*S(sm,sp))
    fm=am[2:-1]*(u[2:-1]-dx/2*(1-abs(a[2:-1])*dt/dx)*S(sm,sp))

    # Add positive and negative fluxes together and return
    return fp+fm



def flux_burgers(u,dx,dt,limiter):
    """
    Compute fluxes between cells

    u: Quantity to be passively advected
    a: Velocity of flow
    dx: Cell size
    dt: Time step
    limiter: String containing the name of one the flux limiter functions in limiters.py
    """

    # Get the function to call for the flux limiter
    S=getattr(limiters,limiter)

    # Gradient across cell at left side of each face
    sm=(u[1:-2]-u[:-3])/dx
    
    # Gradient across cell at right side of each face
    sp=(u[2:-1]-u[1:-2])/dx

    # Separate the velocity into strictly positive and strictly negative vectors, for implementing the upwind scheme
    ap=np.maximum(u,0)
    am=np.minimum(u,0)

    # Compute positive and negative fluxes across each face
    fp=ap[1:-2]*(u[1:-2]/2+dx/2*(1-u[1:-2]*dt/dx)*S(sm,sp))
    fm=am[2:-1]*(u[2:-1]/2-dx/2*(1-abs(u[2:-1])*dt/dx)*S(sm,sp))

    # Add positive and negative fluxes together and return
    return fp+fm

def step(u,a,dx,dt,limiter):
    """
    Step forward in time using an explicit Euler scheme

    u: Quantity to be passively advected
    a: Velocity of flow
    dx: Cell size
    dt: Time step
    limiter: String containing the name of one the flux limiter functions in limiters.py
    """
    f=flux(u,a,float(dx),float(dt),limiter)
    u[2:-2]=u[2:-2]+dt/dx*(f[:-1]-f[1:])

def step_burgers(u,dx,dt,limiter):
    """
    Step forward in time using an explicit Euler scheme

    u: Quantity to be passively advected
    a: Velocity of flow
    dx: Cell size
    dt: Time step
    limiter: String containing the name of one the flux limiter functions in limiters.py
    """
    f=flux_burgers(u,float(dx),float(dt),limiter)
    u[2:-2]=u[2:-2]+dt/dx*(f[:-1]-f[1:])

def updateboundary(a,t,x_grid,x_bound,t_x,a_bound,t_a):

    """
    Insert time-series solar wind data into the grid at the satellite location

    a: Quantity to be passively advected
    t: Simulation time
    x_grid: Positions of cell edges
    x_bound: Satellite location in the same coordinates as x_grid
    t_x: Times for satellite positions
    a_bound: Values of a to insert into grid
    t_a: Times for a values
    """
    
    from scipy.interpolate import interp1d

    # Interpolate satellite position to simulation time
    x=interp1d(t_x,x_bound)(t)

    # Find which grid cell to update
    ind=np.searchsorted(x_grid,x)

    # Update a
    a[ind:ind+1]=interp1d(t_a,a_bound)(t)
