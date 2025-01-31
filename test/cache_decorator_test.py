from advect1d.cache_decorator import get_cache_filename, cache_result
from unittest.mock import patch
import os
import shutil

@cache_result()
def cached_function():
    mockfunc()
    return None

def test_cache_decorator():

    cachename=get_cache_filename(cached_function,(),{})

    try:
        os.remove(os.path.join('cache',cachename))
    except FileNotFoundError:
        pass

    try:
        os.remove(cachename)
    except FileNotFoundError:
        pass

    with patch('cache_decorator_test.mockfunc', create=True) as mockfunc:
        cached_function()
        mockfunc.assert_called_with()

    with patch('cache_decorator_test.mockfunc', create=True) as mockfunc:
        cached_function()
        mockfunc.assert_not_called()

    with patch('cache_decorator_test.mockfunc', create=True) as mockfunc:
        shutil.move(os.path.join('cache', cachename), '.')
        cached_function()
        mockfunc.assert_not_called()
