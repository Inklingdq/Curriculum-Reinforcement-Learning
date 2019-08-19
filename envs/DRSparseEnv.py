import os

import numpy as np
from envs.DishRackEnv import DishRackEnv

dir_path = os.getcwd()

max_displacement = 0.015  # 1.5cm
max_dist = np.linalg.norm([max_displacement]*3)
max_rot = 0.1  # ~5.7 deg


class DRSparseEnv(DishRackEnv):

    def step(self, a):
        self.target_velocity = a
        displacement = np.abs(self.get_vector(self.target_handle, self.plate_handle))
        orientation_diff = np.abs(self.get_plate_orientation())

        rew_success = 0.1 if np.all(orientation_diff <= max_rot) and \
                             np.all(displacement <= max_displacement) else 0
        dist = np.linalg.norm(displacement)
        rew = rew_success * (1 - dist / max_dist)

        self.timestep += 1
        if self.vis_mode:
            self.randomise_domain()
        self.update_sim()

        ob = self._get_obs()
        done = (self.timestep == self.ep_len)

        return ob, rew, done, dict(rew_success=rew_success)
