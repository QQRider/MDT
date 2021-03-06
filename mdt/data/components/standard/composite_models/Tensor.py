from mdt.components_config.composite_models import DMRICompositeModelConfig

__author__ = 'Robbert Harms'
__date__ = "2015-06-22"
__maintainer__ = "Robbert Harms"
__email__ = "robbert.harms@maastrichtuniversity.nl"


class Tensor(DMRICompositeModelConfig):

    ex_vivo_suitable = False
    description = 'The standard Tensor model with in vivo defaults.'
    model_expression = '''
        S0 * Tensor
    '''
    inits = {'Tensor.d': 1.7e-9,
             'Tensor.dperp0': 1.7e-10,
             'Tensor.dperp1': 1.7e-10}

    volume_selection = {'unweighted_threshold': 25e6,
                        'use_unweighted': True,
                        'use_weighted': True,
                        'min_bval': 0,
                        'max_bval': 1.5e9 + 0.1e9}


class TensorExVivo(Tensor):

    name = 'Tensor-ExVivo'
    ex_vivo_suitable = True
    in_vivo_suitable = False
    description = 'The standard Tensor model with ex vivo defaults.'
    inits = {'Tensor.d': 1e-9,
             'Tensor.dperp0': 0.6e-10,
             'Tensor.dperp1': 0.6e-10}
    volume_selection = None
