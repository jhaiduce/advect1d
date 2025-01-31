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


def cache_result(clear=False,checkfunc=None,maxsize=10):

    @lru_cache(maxsize=maxsize)
    def load_cache(cache_path):

        with open(cache_path, 'rb') as cache_file:
            return pkl.load(cache_file)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args,**kwargs):
            import hashlib
            # Pickle the function name and arguments
            key=pkl.dumps((func.__name__,args,frozenset(list(kwargs.keys())),
                           frozenset(list(kwargs.values()))))

            # Convert the pickled data into a (shorter) unique filename
            cachename=hashlib.md5(key).hexdigest()+'.pkl'

            stale=False
            if os.path.exists(cachename) and checkfunc is not None:
                # Check whether cache is stale
                stale=checkfunc(cachename,*args,**kwargs)

            if os.path.exists(cachename) and not clear and not stale:
                try:
                    result=load_cache(cachename)
                except:
                    print('Error loading result from function '+func.__name__+' with args: '+str(args))
                    print('and kwargs: '+str(kwargs))
                    print('from file '+cachename)
                    raise
            else:
                result=func(*args,**kwargs)
                pkl.dump(result,open(cachename,'wb'))
            return result
        
        return wrapper
    return decorator

if __name__=='__main__':

    @cache_result
    def testFunc():
        pass
    
    testFunc()
