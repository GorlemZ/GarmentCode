from pygarment.meshgen.path_config import PathCofig as PathCofig

__all__ = ["PathCofig", "SimConfig"]


class SimConfig:
    def __init__(self, sim_props):
        # ---- Paths ----
        # Sim props sections
        self.props = sim_props
        sim_props_option = sim_props['options']
        sim_props_material = sim_props['material']

        # Basic setup
        self.sim_fps = 60.0
        self.sim_substeps = 10 #increase?
        self.sim_wo_gravity_percentage = 0
        self.zero_gravity_steps = self.get_sim_props_value(sim_props, 'zero_gravity_steps', 5)
        self.resolution_scale = self.get_sim_props_value(sim_props, 'resolution_scale', 1.0)
        self.ground = self.get_sim_props_value(sim_props, 'ground', True)

        # Stopping criteria 
        self.static_threshold = self.get_sim_props_value(sim_props, 'static_threshold', 0.01)
        self.max_sim_steps = self.get_sim_props_value(sim_props, 'max_sim_steps', 1000)
        self.max_frame_time = self.get_sim_props_value(sim_props, 'max_frame_time', None)
        if self.max_frame_time is not None:
            self.max_frame_time = int(self.max_frame_time)
        self.max_sim_time = int(self.get_sim_props_value(sim_props, 'max_sim_time', 25 * 60))
        self.non_static_percent = self.get_sim_props_value(sim_props, 'non_static_percent', 5)
        # Quality filter
        self.max_body_collisions = self.get_sim_props_value(sim_props, 'max_body_collisions', 0)
        self.max_self_collisions = self.get_sim_props_value(sim_props, 'max_self_collisions', 0)

        
        # Self-collision prevention properties
        self.enable_particle_particle_collisions = self.get_sim_props_value(
            sim_props_option,
            'enable_particle_particle_collisions', False)
        self.enable_triangle_particle_collisions = self.get_sim_props_value(
            sim_props_option,
            'enable_triangle_particle_collisions', False)
        self.enable_edge_edge_collisions = self.get_sim_props_value(
            sim_props_option,
            'enable_edge_edge_collisions', False)
        self.enable_body_collision_filters = self.get_sim_props_value(
            sim_props_option, 
            'enable_body_collision_filters', 
            False
        )

        # Attachment constraints
        self.enable_attachment_constraint = self.get_sim_props_value(
            sim_props_option, 
            'enable_attachment_constraint', 
            False
        )
        self.attachment_labels = self.get_sim_props_value(
            sim_props_option, 
            'attachment_label_names', 
            []
        )
        self.attachment_frames = self.get_sim_props_value(
            sim_props_option, 
            'attachment_frames', 
            100
        )
        self.attachment_stiffness = self.get_sim_props_value(
            sim_props_option,
            'attachment_stiffness',
            []
        )
        self.attachment_damping = self.get_sim_props_value(
            sim_props_option,
            'attachment_damping',
            []
        )
        if not self.attachment_frames or not self.attachment_labels:
            self.enable_attachment_constraint = False

        # Global damping properties
        self.global_damping_factor = self.get_sim_props_value(
            sim_props_option,'global_damping_factor', 1.) 
        self.global_damping_effective_velocity = self.get_sim_props_value(
            sim_props_option,
            'global_damping_effective_velocity', 0.0) 
        self.global_max_velocity = self.get_sim_props_value(
            sim_props_option,'global_max_velocity', 50.0)  

        # Cloth global collision resolution (reference drag) options
        self.enable_global_collision_filter = self.get_sim_props_value(
            sim_props_option, 
            'enable_global_collision_filter',
            False
        )
        self.enable_cloth_reference_drag = self.get_sim_props_value(
            sim_props_option,
            'enable_cloth_reference_drag', False)
        self.cloth_reference_margin = self.get_sim_props_value(
            sim_props_option,'cloth_reference_margin', 0.1)
        self.cloth_reference_k = self.get_sim_props_value(
            sim_props_option,'cloth_reference_k', 1.0e7)

        # Body smoothing options
        self.enable_body_smoothing = self.get_sim_props_value(
            sim_props_option,'enable_body_smoothing', True)
        self.smoothing_total_smoothing_factor = self.get_sim_props_value(
            sim_props_option,
            'smoothing_total_smoothing_factor', 1)
        self.smoothing_recover_start_frame = self.get_sim_props_value(
            sim_props_option,
            'smoothing_recover_start_frame', 0)
        self.smoothing_frame_gap_between_steps = self.get_sim_props_value(
            sim_props_option,
            'smoothing_frame_gap_between_steps', 5)
        self.smoothing_num_steps = self.get_sim_props_value(
            sim_props_option, 'smoothing_num_steps', 100)
        self.smoothing_num_steps = max(min(
            self.smoothing_num_steps, self.max_sim_steps - self.smoothing_recover_start_frame),
            0)
        if self.smoothing_num_steps == 0:
            self.enable_body_smoothing = False

        # ----- Fabric material properties ----- 
        # Bending 
        self.garment_edge_ke = self.get_sim_props_value(
            sim_props_material,'garment_edge_ke', 50000.0) #default = 100.0
        self.garment_edge_kd = self.get_sim_props_value(
            sim_props_material,'garment_edge_kd',10.0) #default = 0.0
        
        # Area preservation
        self.garment_tri_ke = self.get_sim_props_value(
            sim_props_material,'garment_tri_ke', 10000.0) #default = 100.0, small number = more elasticity
        self.garment_tri_kd = self.get_sim_props_value(
            sim_props_material,'garment_tri_kd', 1.0) #default = 10.0
        self.garment_tri_ka = self.get_sim_props_value(
            sim_props_material, 'garment_tri_ka', 10000.0)  # default = 100.0
        self.garment_tri_drag = 0.0  # default = 0.0
        self.garment_tri_lift = 0.0 #default = 0.0

        # Thickness
        self.garment_density = self.get_sim_props_value(
            sim_props_material,'fabric_density', 1.0)  
        self.garment_radius = self.get_sim_props_value(
            sim_props_material,'fabric_thickness', 0.1)  

        # Spring properties (Distance constraints)
        self.spring_ke = self.get_sim_props_value(
            sim_props_material,'spring_ke', 50000)
        self.spring_kd = self.get_sim_props_value(
            sim_props_material,'spring_kd', 10.0)

        # Soft contact properties (contact between cloth and body)
        self.soft_contact_margin = 0.2 
        self.soft_contact_ke = 1000.0 
        self.soft_contact_kd = 10.0 
        self.soft_contact_kf = 1000.0 
        self.soft_contact_mu = self.get_sim_props_value(
            sim_props_material, 'fabric_friction', 0.5
        )

        # Body material
        self.body_thickness = self.get_sim_props_value(sim_props_option,'body_collision_thickness', 0.0)
        self.body_friction = self.get_sim_props_value(sim_props_option,'body_friction', 0.5)

        # particle properties  
        # Some default values -- not used in cloth sim
        self.particle_ke = 1.0e3 
        self.particle_kd = 1.0e2 
        self.particle_kf = 100.0  
        self.particle_mu = 0.5 
        self.particle_cohesion = 0.0 
        self.particle_adhesion = 0.0 

        # After the initialization
        self.update_min_steps()

    def update_min_steps(self):
        self.min_sim_steps = 0
        if self.enable_body_smoothing: 
            self.min_sim_steps = self.smoothing_recover_start_frame + self.smoothing_num_steps
        if self.enable_attachment_constraint:
            # NOTE: Adding a small number of frames 
            # to allow clothing movement to restart after attachment is released
            self.min_sim_steps = max(self.min_sim_steps, self.attachment_frames + 5)

    def get_sim_props_value(self, sim_props, name, default_value):
        if name in sim_props:
            return sim_props[name]
        return default_value

