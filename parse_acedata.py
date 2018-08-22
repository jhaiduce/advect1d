from datetime import datetime, timedelta

def parse_from_web(filename):

    data={
        'time':[],
        'bx':[],
        'by':[],
        'bz':[],
        'x':[],
        'y':[],
        'z':[],
    }

    with open(filename) as fh:
        while True:
            line=fh.readline()
            if line.startswith('BEGIN DATA'):
                break

        while True:
            line=fh.readline()
            if line=='':
                break
            
            tokens=line.split()

            year,doy,h,m=[int(tok) for tok in tokens[:4]]

            s,bx,by,bz,fraction_good=[float(tok) for tok in tokens[4:9]]
            n_vectors,quality=[int(tok) for tok in tokens[9:11]]
            x,y,z=[float(tok) for tok in tokens[11:]]

            time=datetime(year,1,1)+timedelta(doy-1)+timedelta(seconds=h*3600+m*60+s)
            data['time'].append(time)
            data['bx'].append(bx)
            data['by'].append(by)
            data['bz'].append(bz)
            data['x'].append(x)
            data['y'].append(y)
            data['z'].append(z)

    return data

def parse_from_ruth(filename):

    data={
        'time':[],
        'rho':[],
        'T':[],
        'ux':[],
        'uy':[],
        'uz':[],
    }
    with open(filename) as fh:

        while True:
            line=fh.readline()

            if line=='': break

            tokens=line.split()
            try:
                int(tokens[0])
            except (ValueError,IndexError):
                continue

            year=int(tokens[0])
            doy=int(tokens[1])

            dayfrac,rho,T,speed,ux,uy,uz=[float(s) for s in tokens[2:]]

            time=datetime(year,1,1)+timedelta(doy-1)+timedelta(seconds=dayfrac*3600*24)


            data['time'].append(time)
            data['rho'].append(rho)
            data['T'].append(T)
            data['ux'].append(ux)
            data['uy'].append(uy)
            data['uz'].append(uz)

        return data
