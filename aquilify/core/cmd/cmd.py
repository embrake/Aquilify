import argparse

from .migrations import make_migration

def execute_from_cmd_line():
    parser = argparse.ArgumentParser(description='Aquilify Command Line Interface | 2.0')
    make_migration(parser)