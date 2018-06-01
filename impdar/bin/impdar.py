#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2018 dlilien <dlilien@berens>
#
# Distributed under terms of the GNU GPL3.0 license.
#
# Legacy header:
#	Created: B. Welch - 10/15/01
#	Modification History:
#       1)  Added ability to load processed in Stodeep - S. Harris 6/5/02
# 		2)	Converted to new structure-based flagging format - J. Olson 7/10/08
#       3)  Added call for new batchdeep.m shell - B. Youngblood 7/12/08

import argparse
from impdar import load, process


def dummy(args):
    print(args)
    print('Not yet implemented')


def _get_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help')
    parser.add_argument('-o', type=str, help='Write to this filename')

    parser_load = subparsers.add_parser('load', help='Load data')
    parser_load.set_defaults(func=load.load_and_exit)
    parser_load.add_argument('filetype', type=str, help='Type of file', choices=['gssi', 'pe', 'mat'])
    parser_load.add_argument('fn', type=str, nargs='+', help='File(s) to load')

    parser_proc = subparsers.add_parser('proc', help='Process data')
    parser_proc.set_defaults(func=process.process_and_exit)
    parser_proc.add_argument('-gssi', action='store_true', help='Indicates that the file(s) are gssi output')
    parser_proc.add_argument('-pe', action='store_true', help='Indicates that the file(s) are pulse ekko output')
    parser_proc.add_argument('-vbp', nargs=2, type=float, help='Bandpass the data vertically at low (MHz) and high (MHz)')
    parser_proc.add_argument('-hbp', nargs=2, help='Bandpass the data horizontally at low (MHz) and high (MHz)')
    parser_proc.add_argument('fn', type=str, nargs='+', help='File(s) to load')

    parser_plot = subparsers.add_parser('plot', help='Plot data')
    parser_plot.set_defaults(func=dummy)
    return parser


def main():
    parser = _get_args()
    args = parser.parse_args()
    if not hasattr(args, 'func'):
        parser.parse_args(['-h'])
        return
    return args.func(**vars(args))


if __name__ == '__main__':
    main()