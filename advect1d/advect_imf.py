# stdlib
import os
import sys
from datetime import datetime, timedelta
try:
    # Python 3
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser

# local
from cdaweb import get_cdf
from missing import fill_gaps
from cache_decorator import cache_result

# extras
import numpy as np
from spacepy import datamodel as dm
from spacepy import pybats


@cache_result(clear=False)
def load_acedata(tstart, tend, noise=True, proxy=None):
    """
    Fetch ACE data from CDAWeb

    tstart: Desired start time
    tend: Desired end time
    noise: Adds noise to fill_gaps function

    Returns: A dictionary of tuples, each containing an array of times
             and an array of ACE observations for a particular variable
    """

    # Download SWEPAM and Mag data from CDAWeb
    swepam_data = get_cdf('sp_phys', 'AC_H0_SWE', tstart, tend,
                          ['Np', 'V_GSM', 'Tpr', 'SC_pos_GSM'], proxy=proxy)
    mag_data = get_cdf('sp_phys', 'AC_H0_MFI', tstart, tend,
                       ['BGSM'], proxy=proxy)

    # Dictionary to store all the data from ACE
    acedata = {'T': (swepam_data['Epoch'], swepam_data['Tpr']),
               'rho': (swepam_data['Epoch'], swepam_data['Np']),
               }

    # Store all the vector data in the array
    for i, coord in enumerate('xyz'):
        for dataset, local_name, cdaweb_name in [(mag_data, 'b', 'BGSM'),
                                                 (swepam_data, 'u', 'V_GSM'),
                                                 (swepam_data, '', 'SC_pos_GSM')]:
            t = dataset['Epoch']
            values = fill_gaps(dataset[cdaweb_name][:, i],
                               fillval=dataset[cdaweb_name].attrs['FILLVAL'],
                               noise=noise)

            # Grab the appropriate component from
            # VALIDMIN and VALIDMAX attributes
            values.attrs['VALIDMIN'] = values.attrs['VALIDMIN'][i]
            values.attrs['VALIDMAX'] = values.attrs['VALIDMAX'][i]

            # Store in acedata dict
            acedata[local_name+coord] = t, values

    for var in acedata.keys():
        # Restrict to only valid data
        t_var, varIn = acedata[var]
        goodpoints = (varIn < varIn.attrs['VALIDMAX']) & (varIn > varIn.attrs['VALIDMIN'])
        t_var, varIn = t_var[goodpoints], varIn[goodpoints]

        acedata[var] = (t_var, varIn)

    return acedata


@cache_result(clear=False)
def load_dscovr(tstart, tend, noise=True, proxy=None):
    """
    Fetch DSCOVR data from CDAWeb

    tstart: Desired start time
    tend: Desired end time
    noise: Adds noise to fill_gaps function

    Returns: A dictionary of tuples, each containing an array of times and an
             array of DSCOVR observations for a particular variable
    """

    # Download SWEPAM and Mag data from CDAWeb
    plasma_data = get_cdf('sp_phys', 'DSCOVR_H1_FC', tstart, tend,
                          ['Np', 'V_GSE', 'THERMAL_TEMP'], proxy=proxy)
    mag_data = get_cdf('sp_phys', 'DSCOVR_H0_MAG', tstart, tend, ['B1GSE'], proxy=proxy)
    orbit_data = get_cdf('sp_phys', 'DSCOVR_ORBIT_PRE', tstart, tend, ['GSE_POS'], proxy=proxy)

    # Dictionary to store all the data from DSCOVR
    dscovrdata = {'T': (plasma_data['Epoch'], plasma_data['THERMAL_TEMP']),
                  'rho': (plasma_data['Epoch'], plasma_data['Np']),
                  }

    # Store all the vector data in the array
    for i, coord in enumerate('xyz'):
        for dataset, local_name, cdaweb_name, cdaweb_time_var in [
                (mag_data, 'b', 'B1GSE', 'Epoch1'),
                (plasma_data, 'u', 'V_GSE', 'Epoch'),
                (orbit_data, '', 'GSE_POS', 'Epoch')]:
            t = dataset[cdaweb_time_var]
            values = fill_gaps(dataset[cdaweb_name][:, i],
                               fillval=dataset[cdaweb_name].attrs['FILLVAL'],
                               noise=noise)

            for attr in ('VALIDMIN', 'VALIDMAX'):

                try:
                    len(values.attrs[attr])
                except TypeError:
                    # It's a scalar, leave it as it is
                    pass
                else:
                    # Grab the appropriate component from
                    # VALIDMIN and VALIDMAX attributes
                    values.attrs[attr] = values.attrs[attr][0]

            # Store in data dict
            dscovrdata[local_name+coord] = t, values

    for var in dscovrdata.keys():
        # Restrict to only valid data
        t_var, varIn = dscovrdata[var]
        goodpoints = (varIn > varIn.attrs['VALIDMIN'])
        t_var, varIn = t_var[goodpoints], varIn[goodpoints]

        dscovrdata[var] = (t_var, varIn)

    return dscovrdata


def initialize(sw_data, advect_vars=['ux', 'uy', 'uz', 'bx', 'by', 'bz', 'rho', 'T'],
               ncells=1000, l1_x=1.6e6, output_x=0):
    """
    Initialize advection simulation

    sw_data: Dictionary of L1 solar wind data, structured in the form returned from
             load_acedata or load_dscovr
    advect_vars: Keys in the sw_data dictionary for variables that should be advected
    ncells: Number of cells in the computational grid
    l1_x: Maximum coordinate (in GSM/GSE x, units of km) of the upstream solar wind data
    output_x: Minimum coordinate (in GSM/GSE x, km) where output will be needed
    """

    l1data = {}

    xextent = l1_x-output_x
    max_x = l1_x+xextent*(2./ncells)
    min_x = output_x-xextent*(2./ncells)

    # Make the grid
    x = np.linspace(min_x, max_x, ncells)

    # ux must be advected regardless
    if 'ux' not in advect_vars:
        advect_vars = list(advect_vars)+['ux']

    # Start time of simulation is first point for which all variables have valid data
    t0 = np.max([t[0] for var, (t, values) in sw_data.items()])

    for var in sw_data.keys():

        t_var, values = sw_data[var]

        # Subtract epoch time from time arrays and convert them to seconds
        t_var = np.array([(t-t0).total_seconds() for t in t_var])

        l1data[var] = t_var, values

    # Initialize simulation state vectors
    state = {var: np.ones([ncells])*values[0] for var, [t, values] in sw_data.items()
             if var in advect_vars}
    state['x'] = x

    # Dictionary to hold output variables
    outdata = {var: [] for var in advect_vars}
    outdata['time'] = []

    return state, outdata, t0, l1data


def iterate(state, t, outdata, sw_data, nuMax=0.5, output_x=0, limiter='Minmod'):
    """
    Advect L1 observations to Earth

    state: dictionary of state variables, as generated by initialize()
    t: Current time associated with state
    outdata: Dictionary to store the output data
    sw_data: Dictionary of L1 solar wind data, structured in the form returned from
             load_acedata or load_dscovr
    nuMax: Maximum allowed CFL
    output_x: x coordinate (in the GSM/GSE coordinate system with units of km) where
              output values should be provided
    """

    from advect1d import step, step_burgers, updateboundary

    u = state['ux']
    x = state['x']
    dx = x[1]-x[0]

    # Variables to be advected include everything in state except 'x'
    advect_vars = list(state.keys())
    advect_vars.remove('x')

    # Put ux on the end of advect_vars since it requires special treatment
    advect_vars.remove('ux')
    advect_vars.append('ux')

    # Update boundary conditions with values at new time step
    for var in advect_vars:
        a = state[var]
        var_t, values = sw_data[var]
        x_sat_t, x_sat = sw_data['x']
        updateboundary(a, t, x, x_sat, x_sat_t, values, var_t)

    # Find the time step
    dt = nuMax/np.abs(np.min(u))*dx

    # Step variables forward in time
    for var in advect_vars[:-1]:
        a = state[var]
        step(a, u, dx, dt, limiter)

    # ux handled separately since it has a different governing equation
    step_burgers(u, dx, dt, limiter)
    state['ux'][:] = u

    # Store output state
    for var in advect_vars:
        from scipy.interpolate import interp1d

        # Interpolate state variable to point where output is requested
        outdata[var].append(interp1d(x, state[var])(output_x))

    # Append time to output state
    outdata['time'].append(t+dt)

    return dt


def parse_args(starttime=None, endtime=None):
    from argparse import ArgumentParser

    parser = ArgumentParser()

    starttime = starttime or datetime(2017, 9, 6, 20)
    endtime = endtime or datetime(2017, 9, 7, 5)

    parser.add_argument('--start-time',
                        type=lambda s: datetime.strptime(s, '%Y-%m-%dT%H:%M:%S'),
                        default=starttime,
                        dest='start_time',
                        help='Start time of solar wind observations, ' +
                             'universal time in YYYY-MM-DDTHH:MM:SS')
    parser.add_argument('--end-time',
                        type=lambda s: datetime.strptime(s, '%Y-%m-%dT%H:%M:%S'),
                        default=endtime,
                        dest='end_time',
                        help='Start time of solar wind observations, ' +
                             'universal time in YYYY-MM-DDTHH:MM:SS')
    parser.add_argument('--output-x',
                        default=203872,
                        type=int,
                        dest='output_x',
                        help='Location used for output, given in km upstream ' +
                             'of Earth. Defaults to 203872 (32 Earth radii).')
    parser.add_argument('--ncells',
                        default=1000,
                        type=int,
                        dest='ncells',
                        help='Number of cells, between L1 and Earth, used by advection ' +
                             'code. Defaults to 1000.')
    parser.add_argument('--source', default='DSCOVR',
                        help='Solar wind data source ("ACE" or "DSCOVR")')
    parser.add_argument('--proxy', help='Proxy server URL')
    parser.add_argument('--disable-noise', action='store_true',
                        help='By default, data gaps in the upstream solar ' +
                             'wind data will be filled with a noisy ' +
                             'interpolation algorithm developed by M. Engel ' +
                             'and S. Morley. With this argument, the noisy ' +
                             'interpolation is disabled and a linear ' +
                             'interpolation used instead')
    parser.add_argument('-c', '--config', dest='configFile', default=None,
                        help='Name of configuration file to use (optional)')
    args = parser.parse_args()

    # handle config file if present
    # variables set in the config file take precedence
    if args.configFile is not None:
        config = ConfigParser()
        with open(args.configFile, 'r') as fh:
            if sys.version_info.major >= 3:
                config.read_file(fh)
            else:
                config.readfp(fh)  # legacy Python 2 support
        for ckey in config.options('Settings'):
            try:
                setting = config.get('Settings', ckey)
                if ckey.endswith('time'):
                    setting = datetime.strptime(setting, '%Y-%m-%dT%H:%M:%S')
                elif ckey.lower() in ['ncells', 'output_x']:
                    setting = int(setting)
                args.__dict__[ckey] = setting
            except:
                pass

    proxy = args.proxy or os.environ.get('http_proxy')

    if proxy:
        # Convert proxy URL into a tuple to be passed to
        # urllib2.Request.set_proxy
        import re
        m = re.match('((?P<scheme>[a-z]+)://)?(?P<host>\w+)/?', proxy)
        scheme = m.group('scheme') or 'http'
        host = m.group('host')
        args.proxy = (host, scheme)

    return args


def fetch_solarwind(starttime, endtime, source='DSCOVR', proxy=None, noise=True):
    if source == 'DSCOVR':
        sw_data = load_dscovr(starttime, endtime, proxy=proxy, noise=noise)
    elif source == 'ACE':
        sw_data = load_acedata(starttime, endtime, proxy=proxy, noise=noise)
    else:
        raise ValueError('Invalid source ''{}'''.format(source))

    return sw_data


if __name__ == '__main__':

    args = parse_args()

    noise = not args.disable_noise

    starttime = args.start_time
    endtime = args.end_time
    source = args.source
    proxy = args.proxy
    output_x = args.output_x
    ncells = args.ncells

    # Fetch solar wind data
    sw_data = fetch_solarwind(starttime, endtime, source=source, proxy=proxy, noise=noise)

    # Initialize the simulation state
    state, outdata, t0, l1data_tnum = initialize(sw_data, ncells=ncells, output_x=output_x)

    # Stop time of simulation is last point for which all variables have valid data
    tmax = np.min([t[-1] for var, (t, values) in l1data_tnum.items()])

    # Step forward in time
    t = 0
    i = 0
    while t < tmax:
        dt = iterate(state, t, outdata, l1data_tnum, output_x=output_x)
        t += dt
        i += 1

    # Convert timesteps to datetimes
    outdata['time'] = [starttime + timedelta(seconds=n)
                       for n in outdata['time']]

    # Set up pram and temp keys
    outdata['pram_1'] = np.multiply(outdata['ux'], outdata['ux'])
    outdata['pram_2'] = np.multiply(outdata['pram_1'], outdata['rho'])
    outdata['pram'] = 1.67621e-6*outdata['pram_2']

    outdata['temp'] = outdata['T']

    # Set up dictionary
    imf = pybats.ImfInput(load=False)
    for key in imf.keys():
        imf[key] = dm.dmarray(outdata[key])

    # Write the IMF data to .dat file
    imf.write('IMF_data.dat')

    # Write the IMF data to .h5 file
    outhdf = dm.SpaceData()
    for key in outdata.keys():
        outhdf[key] = dm.dmarray(outdata[key])
    outhdf['time'].attrs['epoch'] = t0.isoformat()
    outhdf.toHDF5('advected.h5')
