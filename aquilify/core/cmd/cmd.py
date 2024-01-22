import argparse

from .porting import make_porting

def execute_from_cmd_line():
    parser = argparse.ArgumentParser(description='Aquilify Command Line Interface | 2.0')
    make_porting(parser)