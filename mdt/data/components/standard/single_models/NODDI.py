from mdt.models.single import DMRISingleModelConfig
from mot.model_building.parameter_functions.dependencies import SimpleAssignment, AbstractParameterDependency

__author__ = 'Robbert Harms'
__date__ = "2015-06-22"
__maintainer__ = "Robbert Harms"
__email__ = "robbert.harms@maastrichtuniversity.nl"


class NODDITortuosityParameterDependency(AbstractParameterDependency):

    def __init__(self, d, w_ec, w_ic, ):
        self._d = d
        self._w_ec = w_ec
        self._w_ic = w_ic

    @property
    def pre_transform_code(self):
        return '''
            mot_float_type _tortuosity_mult_{d} = {w_ec} / ({w_ec} + {w_ic});
            if(!isnormal(_tortuosity_mult_{d})){{
                _tortuosity_mult_{d} = 0.01;
            }}
        '''.format(d=self._d, w_ec=self._w_ec, w_ic=self._w_ic)

    @property
    def assignment_code(self):
        return '{d} * _tortuosity_mult_{d}'.format(d=self._d)

    @property
    def fixed(self):
        return True

    @property
    def has_side_effects(self):
        return False


class NODDI(DMRISingleModelConfig):

    ex_vivo_suitable = False
    description = 'The standard NODDI model'

    model_expression = '''
        S0 * ((Weight(w_csf) * Ball) +
              (Weight(w_ic) * NODDI_IC) +
              (Weight(w_ec) * NODDI_EC)
              )
    '''

    fixes = {'NODDI_IC.d': 1.7e-9,
             'NODDI_IC.R': 0.0,
             'NODDI_EC.d': 1.7e-9,
             'Ball.d': 3.0e-9}

    dependencies = (
        ('NODDI_EC.dperp0', NODDITortuosityParameterDependency('NODDI_EC.d', 'w_ec.w', 'w_ic.w')),
        ('NODDI_EC.kappa', SimpleAssignment('NODDI_IC.kappa')),
        ('NODDI_EC.theta', SimpleAssignment('NODDI_IC.theta')),
        ('NODDI_EC.phi', SimpleAssignment('NODDI_IC.phi'))
    )

    post_optimization_modifiers = [
        ('NDI', lambda d: d['w_ic.w'] / (d['w_ic.w'] + d['w_ec.w'])),
        ('ODI', lambda d: d['NODDI_IC.odi'])
    ]
