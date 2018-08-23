# Advect1d

Advect1d is a 1-D advection code, used for advecting solar wind data from the ACE spacecraft to the bow shock at Earth.

## Getting started

### Prerequisites

- python 2.7
- spacepy
- dateutil

### Running

To run the advection solver, run

```bash
python advect_imf.py
```

This downloads four days worth of ACE data from CDAWeb, and then advects it to the bow shock. It will take several minutes.

To plot the results, run

```bash
python plot_imf.py
```

A plot showing solar wind variables from OMNI and from advect1d should display.
