import numpy as np

def FirstOrderUpwind(sm,sp):
    return np.zeros(sm.shape)

def LaxWendroff(sm,sp):
    return sp

def Minmod(sm,sp):
    return np.maximum(0,np.minimum(sm,sp))*np.sign(sm+sp)

def Harmonic(sm,sp,epsilon=1e-12):
    return (sm*np.abs(sp)+np.abs(sm)*sp)/(np.abs(sm)+np.abs(sp)+epsilon)

def Geometric(sm,sp):
    return np.sqrt((sm*sp+np.abs(sm*sp))/2)*np.sign(sm+sp)

def Superbee(sm,sp):
    return np.maximum(0,np.maximum(
        np.minimum(2*np.abs(sm),np.abs(sp)),np.minimum(np.abs(sm),2*np.abs(sp))))*np.sign(sm+sp)


