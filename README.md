# Advect1d

Advect1d is a 1-D advection code, used for advecting solar wind data from the ACE spacecraft to the bow shock at Earth.

## Getting started

### Prerequisites

- python 2.7 (or greater)
- spacepy
- dateutil

### Running

To run the advection solver, run

```bash
python advect_imf.py
```

This downloads a short period of DSCOVR solar wind data from CDAWeb, and then advects it to the Earth. It will take several minutes. Output will be written to advected.h5.

To plot the results, run

```bash
python plot_imf.py
```

A plot showing solar wind variables from OMNI and from advect1d should display.
