from advect1d import cdaweb
from datetime import datetime
from .advect_imf import convert_proxy, detect_pybats_imf_vars
from .missing import fill_gaps
import advect1d

def get_omni(start_time, end_time, proxy):

    import json

    sw_vars=cdaweb.get_dataset_variables('sp_phys','OMNI_HRO_1MIN')
    varlist=['Vx','Vy','Vz','BX_GSE','BY_GSE','BZ_GSE','proton_density','T']
    swdata=cdaweb.get_cdf('sp_phys','OMNI_HRO_1MIN',start_time,end_time,varlist,proxy=proxy)

    return swdata

def parse_args():
    from argparse import ArgumentParser
    import dateutil.parser

    parser = ArgumentParser(
        prog="omni2swmf",
        description="Fetches time-shifted solar wind data from the OMNI database and writes it to a file in the format used by SWMF for solar wind input. Any data gaps are filled using linear interpolation."
    )

    starttime = datetime(2017, 9, 6, 20)
    endtime = datetime(2017, 9, 7, 5)

    parser.add_argument('--start-time',
                        type=dateutil.parser.isoparse,
                        default=starttime,
                        dest='start_time',
                        help='Start time of solar wind observations ' +
                             'in ISO 8601 format')
    parser.add_argument('--end-time',
                        type=dateutil.parser.isoparse,
                        default=endtime,
                        dest='end_time',
                        help='Start time of solar wind observations ' +
                             'in ISO 8601 format')
    parser.add_argument('--proxy', help='Proxy server URL', type=convert_proxy)
    parser.add_argument('--outfile', help='Output filename', default='omnidata.dat')

    return parser.parse_args()

def omni2swmf(start_time, end_time, outfile, proxy=None):

    from spacepy import pybats
    from spacepy import datamodel as dm
    import numpy as np
    import sys

    omnidata=get_omni(start_time, end_time,proxy=proxy)

    for var in omnidata.keys():
        if var=='Epoch': continue
        omnidata[var]=fill_gaps(omnidata[var],
                                fillval=omnidata[var].attrs['FILLVAL'])

    imf = pybats.ImfInput(load=False)

    denvar, tempvar = detect_pybats_imf_vars(imf)

    imf['time']=dm.dmarray(np.array(omnidata['Epoch']))
    imf[denvar]=omnidata['proton_density']
    imf[tempvar]=omnidata['T']
    for dim in 'x','y','z':
        imf['b{:}'.format(dim)]=omnidata['B{:}_GSE'.format(dim.upper())]
        imf['u{:}'.format(dim)]=omnidata['V{:}'.format(dim)]
    imf['v']=-imf['ux']
    imf['pram']=1.67621e-6*imf['n']*imf['ux']**2
    imf.attrs['coor']='GSE'
    imf.attrs['header']='\nCreated using advect1d.omni2swmf {version} using solar wind data from the OMNI database, with gaps filled by linear interpolation.\n\n'.format(version=advect1d.__version__)

    imf.write(outfile)

def omni2swmf_cli():

    args=parse_args()

    omni2swmf(args.start_time, args.end_time, args.outfile, proxy=args.proxy)

if __name__=='__main__':

    omni2swmf_cli()
