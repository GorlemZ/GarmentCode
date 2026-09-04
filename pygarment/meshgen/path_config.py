from datetime import datetime
from pathlib import Path

import yaml

from pygarment.data_config import Properties


class PathCofig:
    """Routines for getting paths to various relevant objects with standard names"""

    def __init__(
        self,
        in_element_path,
        out_path,
        in_name,
        out_name=None,
        body_name='',
        samples_name='',
        default_body=True,
        smpl_body=False,
        add_timestamp=False,
    ):
        """Specify
            * in_element_path
            * our_path -- dataset level output path
            * body_name -- specify to indicate use of default bodies
            * samples_name -- specify to indicate use of body sampling (reading body name from measurments file)
        """

        self._system = Properties('./system.json')  # TODOlOW More stable path?
        self._body_name = body_name
        self._samples_folder_name = samples_name
        self._use_default_body = default_body
        self.use_smpl_seg = smpl_body

        # Tags
        if out_name is None:
            out_name = in_name
        self.in_tag = in_name
        self.out_folder_tag = f'{out_name}_{datetime.now().strftime("%y%m%d-%H-%M-%S")}' if add_timestamp else out_name
        self.sim_tag = out_name
        self.boxmesh_tag = out_name

        # Base paths
        self.input = Path(in_element_path)
        self.out = out_path
        self.out_el = Path(out_path) / self.out_folder_tag
        self.out_el.mkdir(parents=True, exist_ok=True)

        # Individual file paths
        self._update_in_paths()
        self._update_boxmesh_paths()
        self.update_in_copies_paths()
        self.update_sim_paths()

    def _update_in_paths(self):

        # Base path
        if not self._samples_folder_name or self._use_default_body:
            self.bodies_path = Path(self._system['bodies_default_path'])
        else:
            self.bodies_path = Path(self._system['body_samples_path']) / self._samples_folder_name / 'meshes'

        # Body measurements
        if not self._samples_folder_name:
            self.in_body_mes = self.bodies_path / f'{self._body_name}.yaml'
        else:
            self.in_body_mes = self.input / 'body_measurements.yaml'

        with open(self.in_body_mes, 'r') as file:
            body_dict = yaml.load(file, Loader=yaml.SafeLoader)
        if 'body_sample' in body_dict['body']:  # Not present in default measurements
            self._body_name = body_dict['body']['body_sample']

        self.in_body_obj = self.bodies_path / f'{self._body_name}.obj'
        self.in_g_spec = self.input / f'{self.in_tag}_specification.json'
        self.body_seg = Path(self._system['bodies_default_path']) / (
            'ggg_body_segmentation.json' if not self.use_smpl_seg else 'smpl_vert_segmentation.json'
        )
        self.in_design_params = self.input / 'design_params.yaml'

    def _update_boxmesh_paths(self):

        self.g_box_mesh = self.out_el / f'{self.boxmesh_tag}_boxmesh.obj'
        self.g_box_mesh_compressed = self.out_el / f'{self.boxmesh_tag}_boxmesh.ply'
        self.g_mesh_segmentation = self.out_el / f'{self.boxmesh_tag}_sim_segmentation.txt'
        self.g_orig_edge_len = self.out_el / f'{self.boxmesh_tag}_orig_lens.pickle'
        self.g_vert_labels = self.out_el / f'{self.boxmesh_tag}_vertex_labels.yaml'
        self.g_texture_fabric = self.out_el / f'{self.boxmesh_tag}_texture_fabric.png'
        self.g_texture = self.out_el / f'{self.boxmesh_tag}_texture.png'
        self.g_mtl = self.out_el / f'{self.boxmesh_tag}_material.mtl'

    def update_in_copies_paths(self):
        self.g_specs = self.out_el / f'{self.in_tag}_specification.json'
        self.element_sim_props = self.out_el / 'sim_props.yaml'
        self.body_mes = self.out_el / f'{self.in_tag}_body_measurements.yaml'
        self.design_params = self.out_el / f'{self.in_tag}_design_params.yaml'

    def update_sim_paths(self):
        self.g_sim = self.out_el / f'{self.sim_tag}_sim.obj'
        self.g_sim_glb = self.out_el / f'{self.sim_tag}_sim.glb'
        self.g_sim_compressed = self.out_el / f'{self.sim_tag}_sim.ply'
        self.usd = self.out_el / f'{self.sim_tag}_simulation.usd'

    def render_path(self, camera_name=''):

        fname = f'{self.sim_tag}_render_{camera_name}.png' if camera_name else f'{self.sim_tag}_render.png'
        return self.out_el / fname
