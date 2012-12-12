import unittest
def run(verbosity=2):
    import os
    suite = unittest.TestLoader().discover(os.path.dirname(__file__))
    unittest.TextTestRunner(verbosity=2).run(suite)