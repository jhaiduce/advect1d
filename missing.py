import copy
import random
import numpy as np
import spacepy.toolbox as tb
from scipy.ndimage.filters import gaussian_filter

def fill_gaps(data, fillval=9999999, sigma=5, winsor=0.05, noise=False, constrain=False):
    '''Fill gaps in input data series, using interpolation plus noise

    The noise approach is based on Owens et al. (Space Weather, 2014).

    data - input numpy ndarray-like
    fillval - value marking fill in the time series
    sigma - width of gaussian filter for finding fluctuation CDF
    winsor - winsorization threshold, values above p=1-winsor and below p=winsor are capped
    noise - Boolean, if True add noise to interpolated region, if False use linear interp only
    constrain - Boolean, if True 
    '''
    # identify sequences of fill in data series
    gaps = np.zeros((len(data),2),dtype=int)
    k = 0
    for i in range(1,len(data)-1):
        # Single space gap/fillval
        if (tb.feq(data[i],fillval)) and (~tb.feq(data[i+1],fillval)) and (~tb.feq(data[i-1],fillval)):
            gaps[k][0] = i
            gaps[k][1] = i
            k += 1
        # Start of multispace gap/fillval
        elif (tb.feq(data[i],fillval)) and (~tb.feq(data[i-1],fillval)):
            gaps[k][0] = i
        # End of multispace gap/fillval
        elif (tb.feq(data[i],fillval)) and (~tb.feq(data[i+1],fillval)):
            gaps[k][1] = i
            k += 1
    gaps = gaps[:k]

    #if no gaps detected
    if k==0:
        return data

    # fill gaps with linear interpolation
    for gap in gaps:
        a = data[gap[0]-1]
        b = data[gap[1]+1]
        dx = (b-a)/(gap[1]-gap[0]+2)
        for i in range(gap[1]-gap[0]+1):
            data[gap[0]+i] = a + dx*(i+1)

    if noise:
        # generate CDF from delta var
        series = data.copy()
        smooth = gaussian_filter(series, sigma)
        dx = series-smooth
        dx.sort()
        p = np.linspace(0,1,len(dx))
        # "Winsorize" - all delta-Var above/below threshold at capped at threshold
        dx[:p.searchsorted(0.+winsor)] = dx[p.searchsorted(0.+winsor)+1]
        dx[p.searchsorted(1.-winsor):] = dx[p.searchsorted(1.-winsor)-1]

        # draw fluctuations from CDF and apply to linearly filled gaps
        for gap in gaps:
            for i in range(gap[1]-gap[0]+1):
                data[gap[0]+i] += dx[p.searchsorted(random.random())]

        # cap variable if it should be strictly positive (e.g. number density)
        # use lowest measured value as floor
        if constrain and series.min() > 0.0:
            data[data < series.min()] = series.min()

    return data
