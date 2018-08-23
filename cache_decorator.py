from functools import wraps
import os
import cPickle as pkl

try:
    from functools import lru_cache
except ImportError:
    from backports.functools_lru_cache import lru_cache


def cache_result(clear=False,checkfunc=None,maxsize=10):

    @lru_cache(maxsize=maxsize)
    def load_cache(cachename):

        return pkl.load(open(cachename))
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args,**kwargs):
            import hashlib
            # Pickle the function name and arguments
            key=pkl.dumps((func.__name__,args,frozenset(kwargs.keys()),frozenset(kwargs.values())))

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
                    print 'Error loading result from function '+func.__name__+' with args: '+str(args)
                    print 'and kwargs: '+str(kwargs)
                    print 'from file '+cachename
                    raise
            else:
                result=func(*args,**kwargs)
                pkl.dump(result,open(cachename,'w'))
            return result
        
        return wrapper
    return decorator

if __name__=='__main__':

    @cache_result
    def testFunc():
        pass
    
    testFunc()
