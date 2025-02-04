from functools import wraps
import os
try:
    import cPickle as pkl
except ImportError: #python 3
    import _pickle as pkl
try:
    from functools import lru_cache
except ImportError:
    from backports.functools_lru_cache import lru_cache

import hashlib
import sys
from functools import partial

if sys.version_info >= (3, 9):
    md5 = partial(hashlib.md5, usedforsecurity=False)
else:
    md5 = hashlib.md5

def get_cache_filename(func, args, kwargs):

    import hashlib

    # Pickle the function name and arguments
    key=pkl.dumps((func.__name__,args,frozenset(list(kwargs.keys())),
                   frozenset(list(kwargs.values()))))

    # Convert the pickled data into a (shorter) unique filename
    cachename=md5(key).hexdigest()+'.pkl'

    return cachename

def cache_result(clear=False,checkfunc=None,maxsize=10, cache_dir='cache'):

    @lru_cache(maxsize=maxsize)
    def load_cache(cache_path):

        with open(cache_path, 'rb') as cache_file:
            return pkl.load(cache_file)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args,**kwargs):

            # Generate a unique name for the function call
            cachename=get_cache_filename(func,args,kwargs)

            if os.path.isfile(os.path.join(cache_dir,cachename)):
                cache_path=os.path.join(cache_dir,cachename)
            elif os.path.isfile(cachename):
                cache_path=cachename
            else:
                cache_path=os.path.join(cache_dir,cachename)

            stale=False
            if os.path.exists(cache_path) and checkfunc is not None:
                # Check whether cache is stale
                stale=checkfunc(cachename,*args,**kwargs)

            if os.path.exists(cache_path) and not clear and not stale:
                try:
                    result=load_cache(cache_path)
                except:
                    print('Error loading result from function '+func.__name__+' with args: '+str(args))
                    print('and kwargs: '+str(kwargs))
                    print('from file '+cachename)
                    raise
            else:
                result=func(*args,**kwargs)
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                pkl.dump(result,open(cache_path,'wb'))
            return result
        
        return wrapper
    return decorator

if __name__=='__main__':

    @cache_result
    def testFunc():
        pass
    
    testFunc()
