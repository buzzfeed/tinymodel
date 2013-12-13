import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
os.environ['CALIENDO_CACHE_PREFIX'] = os.path.join(PATH, 'caliendo')
os.environ['USE_CALIENDO'] = 'True'
os.environ['PURGE_CALIENDO'] = 'True'
