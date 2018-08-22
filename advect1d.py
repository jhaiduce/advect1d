import limiters
import numpy as np

def flux(u,a,dx,dt,limiter):
    S=getattr(limiters,limiter)
    sm=(u[1:-2]-u[:-3])/dx
    sp=(u[2:-1]-u[1:-2])/dx
    ap=np.maximum(a,0)
    am=np.minimum(a,0)
    spm=sp
    smm=(u[3:]-u[2:-1])/dx
    fp=ap[1:-2]*(u[1:-2]+dx/2*(1-a[1:-2]*dt/dx)*S(sm,sp))
    fm=am[2:-1]*(u[2:-1]+dx/2*(1-a[2:-1]*dt/dx)*S(smm,spm))
    return fp+fm

def step(u,a,dx,dt,limiter):
    f=flux(u,a,float(dx),float(dt),limiter)
    u[2:-2]=u[2:-2]+dt/dx*(f[:-1]-f[1:])

def updateboundary(u,a,t,x_grid,x_bound,t_x,u_bound,u_t,a_bound,a_t):
    from scipy.interpolate import interp1d
    x=interp1d(t_x,x_bound)(t)
    ind=np.searchsorted(x_grid,x)
    u[ind:ind+1]=interp1d(u_t,u_bound)(t)
    a[ind:ind+1]=interp1d(a_t,a_bound)(t)
