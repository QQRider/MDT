#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
import argparse
import logging
import os
import mdt
from argcomplete.completers import FilesCompleter
from mdt.shell_utils import BasicShellApplication
from mot import cl_environments
from mot import runtime_configuration
from mot.load_balance_strategies import EvenDistribution
import textwrap

__author__ = 'Robbert Harms'
__date__ = "2015-08-18"
__maintainer__ = "Robbert Harms"
__email__ = "robbert.harms@maastrichtuniversity.nl"


class GenerateMask(BasicShellApplication):

    def __init__(self):
        self.available_devices = {ind: env for ind, env in
                                  enumerate(cl_environments.CLEnvironmentFactory.all_devices())}

    def _get_arg_parser(self):
        description = textwrap.dedent("""
            Create a (brain) mask for the given DWI. This uses the median-otsu algorithm.
        """)
        description += mdt.shell_utils.get_citation_message()

        epilog = textwrap.dedent("""
            Examples of use:
                mdt-generate-mask data.nii.gz data.prtcl
                mdt-generate-mask data.nii.gz data.prtcl -o data_mask.nii.gz
                mdt-generate-mask data.nii.gz data.prtcl -o data_mask.nii.gz --median-radius 2
        """)

        parser = argparse.ArgumentParser(description=description, epilog=epilog,
                                         formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('dwi',
                            action=mdt.shell_utils.get_argparse_extension_checker(['.nii', '.nii.gz', '.hdr', '.img']),
                            help='the diffusion weighted image').completer = FilesCompleter(['nii', 'gz', 'hdr', 'img'],
                                                                                            directories=False)
        parser.add_argument('protocol',
                            action=mdt.shell_utils.get_argparse_extension_checker(['.prtcl']),
                            help='the protocol file, see mdt-generate-protocol').\
            completer = FilesCompleter(['prtcl'], directories=False)
        parser.add_argument('-o', '--output-name',
                            action=mdt.shell_utils.get_argparse_extension_checker(['.nii', '.nii.gz', '.hdr', '.img']),
                            help='the filename of the output file. Default is <dwi_name>_mask.nii.gz').completer = \
            FilesCompleter(['nii', 'gz', 'hdr', 'img'], directories=False)

        parser.add_argument('--median-radius', type=int, default=4,
                            help="Radius (in voxels) of the applied median filter (default 4).")

        parser.add_argument('--numpass', type=int, default=4,
                            help="Number of pass of the median filter (default 4).")

        parser.add_argument('--dilate', type=int, default=1,
                            help="Number of iterations for binary dilation (default 1).")

        parser.add_argument('--cl-device-ind', type=int, nargs='*', choices=self.available_devices.keys(),
                            help="The index of the device we would like to use. This follows the indices "
                                 "in mdt-list-devices and defaults to the first GPU.")

        parser.add_argument('--double', dest='double_precision', action='store_true',
                            help="Calculate in double precision.")
        parser.add_argument('--float', dest='double_precision', action='store_false',
                            help="Calculate in single precision. Default.")
        parser.set_defaults(double_precision=False)

        return parser

    def run(self, args):
        dwi_name = os.path.splitext(os.path.realpath(args.dwi))[0]
        dwi_name = dwi_name.replace('.nii', '')
        output_name = os.path.realpath(args.output_name) or dwi_name + '_mask.nii.gz'

        if args.cl_device_ind:
            if isinstance(args.cl_device_ind, int):
                runtime_configuration.runtime_config['cl_environments'] = [self.available_devices[args.cl_device_ind]]
            else:
                runtime_configuration.runtime_config['cl_environments'] = [self.available_devices[ind]
                                                                           for ind in args.cl_device_ind]
            runtime_configuration.runtime_config['load_balancer'] = EvenDistribution()

        mdt.create_median_otsu_brain_mask(os.path.realpath(args.dwi), os.path.realpath(args.protocol),
                                          output_name, median_radius=args.median_radius,
                                          numpass=args.numpass, dilate=args.dilate)

        logger = logging.getLogger(__name__)
        logger.info('Saved the mask to: {}'.format(output_name))


if __name__ == '__main__':
    GenerateMask().start()