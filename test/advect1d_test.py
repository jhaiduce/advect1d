from advect1d import cdaweb
from datetime import datetime

def test_get_cdf():
    cdaweb.get_cdf('sp_phys','OMNI2_H0_MRG1HR',datetime(2005,1,1),datetime(2005,1,2),['KP1800'])

def test_fetch_and_advect():
    from advect1d.advect_imf import fetch_and_advect
    fetch_and_advect(datetime(2017, 9, 6, 20),datetime(2017, 9, 6, 21))

def test_omni2swmf():
    from advect1d.omni2swmf import omni2swmf

    omni2swmf(datetime(2010,1,1), datetime(2010,1,1,1), 'omni2swmf_test.dat')
