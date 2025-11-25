# -*- coding: utf-8 -*-
import unittest
import os

def run():
    # verbosity=2 for more detailed output
    verbosity = 2 

    #root = os.path.join(os.path.dirname(__file__), 'tests') 
    root = os.path.dirname(__file__)
    
    

    # Discover tests using the loader
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=root, 
        top_level_dir=root,
        pattern='test_*.py')
    
    # Run the discovered test suite
    runner = unittest.TextTestRunner(verbosity=verbosity) 
    runner.run(suite)

if __name__ == '__main__':
    run()