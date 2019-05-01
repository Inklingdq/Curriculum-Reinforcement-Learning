import numpy as np
import torch
from baselines.common.vec_env import VecEnvWrapper


class ResidualVecEnvWrapper(VecEnvWrapper):
    def __init__(self, venv, initial_policy, ob_rms, device, clipob=10., epsilon=1e-8):
        super(ResidualVecEnvWrapper, self).__init__(venv)
        self.ip = initial_policy
        self.ob_rms = ob_rms
        self.device = device
        self.clipob = clipob
        self.epsilon = epsilon
        self.last_obs = None
        self.rnn_hxs = torch.zeros(venv.num_envs, initial_policy.recurrent_hidden_state_size)
        self.masks = torch.zeros(venv.num_envs, 1)

    def normalize_obs(self, obs):
        if self.ob_rms:
            obs = np.clip((obs - self.ob_rms.mean) / np.sqrt(self.ob_rms.var + self.epsilon), -self.clipob, self.clipob)
        return torch.from_numpy(obs).float().to(self.device)

    def step_wait(self):
        obs, rew, done, info = self.venv.step_wait()
        self.masks = torch.FloatTensor([[0.0] if done_ else [1.0]
                                   for done_ in done])

        self.last_obs = self.normalize_obs(obs)
        return obs, rew, done, info

    def step_async(self, action):
        with torch.no_grad():
            _, ip_action, _, self.rnn_hxs = self.ip.act(self.last_obs, self.rnn_hxs, self.masks,
                                                        deterministic=True)
        ip_action = ip_action.squeeze(1).cpu().numpy()
        whole_action = ip_action + action
        self.venv.step_async(whole_action)

    def reset(self, **kwargs):
        obs = self.venv.reset(**kwargs)
        for ob in obs:
            ob[7] = 0.5000000397364298
            ob[8] = 0.5
            ob[9] = 0.15789473997919184
        self.last_obs = self.normalize_obs(obs)
        return obs