import os
import numpy as np
from mindspore.dataset.core.validator_helpers import INT32_MAX
from mindspore.train.callback import Callback
from mindspore import save_checkpoint
from mindspore.nn import Metric


class RMSE(Metric):
    def __init__(self, max_val):
        super(RMSE, self).__init__()
        self.clear()
        self.max_val = max_val
    def clear(self):
        self._squared_error_sum = 0
        self._samples_num = 0
    def update(self, *inputs):
        preds = self._convert_data(inputs[0])
        targets = self._convert_data(inputs[1])
        targets = targets.reshape((-1, targets.shape[2]))
        squared_error_sum = np.power(targets - preds, 2)
        self._squared_error_sum += squared_error_sum.sum()
        self._samples_num += np.size(targets)
    def eval(self):
        if self._samples_num == 0:
            raise RuntimeError('The number of input samples must not be 0.')
        return np.sqrt(self._squared_error_sum / self._samples_num) * self.max_val

class SaveCallback(Callback):
    def __init__(self, eval_model, ds_eval, config):
        super(SaveCallback, self).__init__()
        self.model = eval_model
        self.ds_eval = ds_eval
        self.rmse = INT32_MAX
        self.config = config

    def epoch_end(self, run_context):
        cb_params = run_context.original_args()
        result = self.model.eval(self.ds_eval)
        print('Eval RMSE:', '{:.6f}'.format(result['RMSE']))
        if not os.path.exists('checkpoints'):
            os.mkdir('checkpoints')
        if result['RMSE'] < self.rmse:
            self.rmse = result['RMSE']
            file_name = self.config.dataset + '_' + str(self.config.pre_len) + '.ckpt'
            save_checkpoint(save_obj=cb_params.train_network, ckpt_file_name=os.path.join('checkpoints', file_name))