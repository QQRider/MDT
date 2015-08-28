#!/usr/bin/env python
import argparse
from mdt.gui.tkgui_main import start_single_gui

__author__ = 'Robbert Harms'
__date__ = "2015-08-18"
__maintainer__ = "Robbert Harms"
__email__ = "robbert.harms@maastrichtuniversity.nl"


def get_arg_parser():
    description = "Launches the MDT TK single subject graphical user interface.\n"
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-d', '--dir', metavar='dir', type=str, help='the base directory for the file choosers',
                        default=None)
    return parser

if __name__ == '__main__':
    parser = get_arg_parser()
    args = parser.parse_args()
    start_single_gui(args.dir)