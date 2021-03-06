from mdt.components_config.composite_models import DMRICompositeModelConfig
from mdt.components_loader import component_import


class SSFP_BallStick_r1_ExVivo(DMRICompositeModelConfig):

    name = 'SSFP_BallStick_r1-ExVivo'
    ex_vivo_suitable = True
    in_vivo_suitable = False
    description = 'The SSFP Ball & Stick model'
    model_expression = '''
        S0 * ( (Weight(w_ball) * SSFP_Ball) +
               (Weight(w_stick) * SSFP_Stick) )
    '''
    fixes = {'SSFP_Ball.d': 2.0e-9,
             'SSFP_Stick.d': 0.6e-9}
    dependencies = {# 'SSFP_Ball.d': 'SSFP_Stick.d',
                    }
    post_optimization_modifiers = [('FS', lambda results: 1 - results['w_ball.w'])]


class SSFP_Tensor_ExVivo(DMRICompositeModelConfig):

    name = 'SSFP_Tensor-ExVivo'
    description = 'The SSFP Tensor model with ex vivo defaults.'
    model_expression = '''
        S0 * SSFP_Tensor
    '''
    inits = {'SSFP_Tensor.d': 1e-9,
             'SSFP_Tensor.dperp0': 0.6e-10,
             'SSFP_Tensor.dperp1': 0.6e-10}
    ex_vivo_suitable = True
    in_vivo_suitable = False
    volume_selection = None
