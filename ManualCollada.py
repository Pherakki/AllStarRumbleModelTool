import os

class ColladaImage:
    def __init__(self, sid, src):
        self.sid = sid
        self.src = src
        
    def write(self, writefunc, indent):
        writefunc(indent + f"""<image id="{self.sid}" name="{self.sid}">""")
        writefunc(indent + f"""  <init_from>{self.src}</init_from>""")
        writefunc(indent + f"""</image>""")
    
class ColladaSurface:
    def __init__(self, sid, collada_image):
        self.sid = sid
        self.image_sid = collada_image.sid
        
    def write(self, writefunc, indent):
        writefunc(indent + f"""<surface type="2D">""")
        writefunc(indent + f"""  <init_from>{self.image_sid}</init_from>""")
        writefunc(indent + f"""</surface>""")

class ColladaSampler:
    def __init__(self, sid, collada_surface):
        self.sid = sid
        self.surface_sid = collada_surface.sid
        
    def write(self, writefunc, indent):
        writefunc(indent + f"""<sampler2D>""")
        writefunc(indent + f"""  <source>{self.surface_sid}</source>""")
        writefunc(indent + f"""</sampler2D>""")
        
class ColladaMap:
    def __init__(self, sid, collada_surface, uvset):
        self.sid = sid
        self.surface_sid = collada_surface.sid
        self.uvset = uvset
        
    def write(self, writefunc, indent):
        writefunc(indent + f"""<texture texture="{self.surface_sid}" texcoord="{self.uvset}"/>""")

class ColladaEffect:
    def __init__(self, sid, params, technique, attributes):
        self.sid = sid
        self.params = params
        self.technique = technique
        self.attributes = attributes
        
    def write(self, writefunc, indent):
        writefunc(indent + f"""<effect id="{self.sid}">""")
        writefunc(indent + f"""  <profile_COMMON>""") 
        self.write_params(writefunc, indent + "    ")
        writefunc(indent + f"""    <technique sid="common">""")
        writefunc(indent + f"""      <{self.technique}>""")
        self.write_attributes(writefunc, indent + "        ")
        writefunc(indent + f"""      </{self.technique}>""")
        writefunc(indent + f"""    </technique>""")
        writefunc(indent + f"""  </profile_COMMON>""") 
        writefunc(indent + f"""</effect>""")
        
    def write_params(self, writefunc, indent):
        for param in self.params:
            writefunc(indent + f"""<newparam sid="{param.sid}">""")
            param.write(writefunc, indent + "  ")
            writefunc(indent + f"""</newparam>""")
        
    def write_attributes(self, writefunc, indent):
        if 'diffuse' not in self.attributes:
            writefunc(indent + f"""<diffuse>""")
            writefunc(indent + f"""  <color sid="diffuse">1 1 1 1</color>""")
            writefunc(indent + f"""</diffuse>""")            
        if 'emission' not in self.attributes:
            writefunc(indent + f"""<emission>""")
            writefunc(indent + f"""  <color sid="emission">0 0 0 1</color>""")
            writefunc(indent + f"""</emission>""")
        if 'index_of_refraction' not in self.attributes:
            writefunc(indent + f"""<index_of_refraction>""")
            writefunc(indent + f"""  <float sid="ior">1.45</float>""")
            writefunc(indent + f"""</index_of_refraction>""")
            
        for attribute, value in self.attributes.items():
            writefunc(indent + f"""<{attribute}>""")
            value.write(writefunc, indent + "  ")
            writefunc(indent + f"""</{attribute}>""")

class ColladaMaterial:
    def __init__(self, sid, name, effect):
        self.sid = sid
        self.name = name
        self.effect = effect
        
    def write(self, writefunc, indent):
        writefunc(indent + f"""<material id="{self.sid}" name="{self.name}">""")
        writefunc(indent + f"""  <instance_effect url="#{self.effect.sid}"/>""")
        writefunc(indent + f"""</material>""")
        
        
class ColladaFloatSource:
    def __init__(self, sid, contents, param_names):
        self.sid = sid
        self.contents = contents
        self.param_names = param_names
        
    def write(self, writefunc, indent):
        flat_contents = [subitem for item in self.contents for subitem in item]
        writefunc(indent + f"""<source id="{self.sid}">""")
        writefunc(indent + f"""  <float_array id="{self.sid}-array" count="{len(flat_contents)}">{" ".join([str(float(item)) for item in flat_contents])}</float_array>""")
        writefunc(indent + f"""  <technique_common>""")
        writefunc(indent + f"""    <accessor source="#{self.sid}-array" count="{len(self.contents)}" stride="{len(self.contents[0])}">""")
        for param_name in self.param_names:
            writefunc(indent + f"""      <param name="{param_name}" type="float"/>""")
        writefunc(indent + f"""    </accessor>""")          
        writefunc(indent + f"""  </technique_common>""")
        writefunc(indent + f"""</source>""")
        
        
class ColladaInputList:
    def __init__(self):
        self.position_input_idx = None
        self.inputs = []
        
    def add_input(self, idx, semantic, source, **kwargs):
        if semantic == 'VERTEX':
            self.position_input_idx = idx
        self.inputs.insert(idx, [semantic, source.sid, kwargs])
        
    @property
    def position(self):
        return self.inputs[self.position_input_idx]


class ColladaTriangleSet:
    def __init__(self, triangle_indices, input_list, material):
        self.triangle_indices = triangle_indices
        self.input_list = input_list
        self.material = material
        
    def write(self, writefunc, indent):
        writefunc(indent + f"""<vertices id="{self.input_list.position[1]}-vertices">""")
        writefunc(indent + f"""  <input semantic="POSITION" source="#{self.input_list.position[1]}"/>""")
        writefunc(indent + f"""</vertices>""")
        writefunc(indent + f"""<triangles material="{self.material.name}" count="{len(self.triangle_indices)//(3*len(self.input_list.inputs))}">""")
        for i, input_set in enumerate(self.input_list.inputs):
            if input_set[0] == 'VERTEX':
                writefunc(indent + f"""  <input semantic="{input_set[0]}" source="#{input_set[1]}-vertices" offset="{i}"/>""")
            else:
                kwarg_list = " ".join([f"{key}=\"{value}\"" for key, value in input_set[2].items()])
                writefunc(indent + f"""  <input semantic="{input_set[0]}" source="#{input_set[1]}" offset="{i}" {kwarg_list}/>""")
        writefunc(indent + f"""  <p>{" ".join([str(item) for item in self.triangle_indices])}</p>""")  
        writefunc(indent + f"""</triangles>""")  
        
        
class ColladaGeometry:
    def __init__(self, sid, name, source_list, triangle_holder):
        self.sid = sid
        self.name = name
        self.source_list = source_list
        self.triangle_holder = triangle_holder
        
    def write(self, writefunc, indent):   
        writefunc(indent + f"""<geometry id="{self.sid}" name="{self.name}">""")
        writefunc(indent + f"""  <mesh>""")
        self.write_child(self.source_list, writefunc, indent + "    ")
        self.triangle_holder.write(writefunc, indent + "    ")
        writefunc(indent + f"""  </mesh>""")
        writefunc(indent + f"""</geometry>""")
        
    def write_child(self, child, write_func, indent):
        for item in child:
            item.write(write_func, indent)
            

class ColladaSkinController:
    def __init__(self, name, collada_geom, bone_names, ibps, weights, weighted_joints):
        self.collada_geom = collada_geom
        self.name = f"{name}_{self.collada_geom.name}_skin"
        self.sid = f"{name}_{self.collada_geom.sid}_skin"
        self.bone_names = bone_names
        self.ibps = ibps
        # Weights and weighted_joints should have the same shapes
        self.weights = weights
        self.weighted_joints = weighted_joints
        
    def write(self, writefunc, indent):
        bind_shape_matrix = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        
        
        writefunc(indent + f"""<controller id="{self.sid}" name="{self.name}">""")
        writefunc(indent + f"""  <skin source="#{self.collada_geom.sid}">""")
        writefunc(indent + f"""    <bind_shape_matrix>{" ".join([str(float(item)) for item in bind_shape_matrix])}</bind_shape_matrix>""")
        
        writefunc(indent + f"""    <source id="{self.sid}-joints">""")
        writefunc(indent + f"""      <Name_array id="{self.sid}-joints-array" count="{len(self.bone_names)}">{" ".join(self.bone_names)}</Name_array>""")
        writefunc(indent + f"""      <technique_common>""")
        writefunc(indent + f"""        <accessor source="#{self.sid}-joints-array" count="{len(self.bone_names)}" stride="1">""")
        writefunc(indent + f"""          <param name="JOINT" type="name"/>""")
        writefunc(indent + f"""        </accessor>""")
        writefunc(indent + f"""      </technique_common>""")
        writefunc(indent + f"""    </source>""")
        
        flat_ibps = [subitem for item in self.ibps for subitem in item]
        flat_ibps = [subitem for item in flat_ibps for subitem in item]
        writefunc(indent + f"""    <source id="{self.sid}-bind_poses">""")
        writefunc(indent + f"""      <float_array id="{self.sid}-bind_poses-array" count="{len(self.ibps*16)}">{" ".join([str(float(item)) for item in flat_ibps])}</float_array>""")
        
        writefunc(indent + f"""      <technique_common>""")
        writefunc(indent + f"""        <accessor source="#{self.sid}-bind_poses-array" count="{len(self.ibps)}" stride="16">""")         
        writefunc(indent + f"""          <param name="TRANSFORM" type="float4x4"/>""")
        writefunc(indent + f"""        </accessor>""")
        writefunc(indent + f"""      </technique_common>""")
        writefunc(indent + f"""    </source>""")
        
        flat_weights = [subitem for item in self.weights for subitem in item]
        writefunc(indent + f"""    <source id="{self.sid}-weights">""")
        writefunc(indent + f"""      <float_array id="{self.sid}-weights-array" count="{len(flat_weights)}">{" ".join([str(float(item)) for item in flat_weights])}</float_array>""")
        writefunc(indent + f"""      <technique_common>""")
        writefunc(indent + f"""        <accessor source="#{self.sid}-weights-array" count="{len(flat_weights)}" stride="1">""")
        writefunc(indent + f"""          <param name="WEIGHT" type="float"/>""")
        writefunc(indent + f"""        </accessor>""")
        writefunc(indent + f"""      </technique_common>""")
        writefunc(indent + f"""    </source>""")
        
        
        writefunc(indent + f"""    <joints>""")
        writefunc(indent + f"""      <input semantic="JOINT" source="#{self.sid}-joints"/>""")
        writefunc(indent + f"""      <input semantic="INV_BIND_MATRIX" source="#{self.sid}-bind_poses"/>""")
        writefunc(indent + f"""    </joints>""")
        
        flat_weighted_joints = [int(subitem) for item in self.weighted_joints for subitem in item]
        writefunc(indent + f"""    <vertex_weights count="{len(self.weights)}">""")
        writefunc(indent + f"""      <input semantic="JOINT" source="#{self.sid}-joints" offset="0"/>""")
        writefunc(indent + f"""      <input semantic="WEIGHT" source="#{self.sid}-weights" offset="1"/>""")
        writefunc(indent + f"""      <vcount>{" ".join([str(len(item)) for item in self.weighted_joints])}</vcount>""")
        writefunc(indent + f"""      <v>{" ".join([str(item) + " " + str(i) for i, item in enumerate(flat_weighted_joints)])}</v>""")
        writefunc(indent + f"""    </vertex_weights>""")
        writefunc(indent + f"""  </skin>""")
        writefunc(indent + f"""</controller>""")

        
            
class ColladaArmatureNode:
    def __init__(self, name, transform):
        self.name = name
        self.transform = transform
        self.child_nodes = []
        
    def write(self, writefunc, indent):
        flat_transform = [subitem for item in self.transform for subitem in item]
        writefunc(indent + f"""<node id="{self.name}" name="{self.name}" type="NODE">""")
        writefunc(indent + f"""  <matrix sid="transform">{' '.join([str(float(item)) for item in flat_transform])}</matrix>""")
        for child_node in self.child_nodes:
            child_node.write(writefunc, indent + "  ")
        writefunc(indent + f"""</node>""")

class ColladaBoneNode:
    def __init__(self, name, armature, transform):
        self.name = name
        self.armature = armature
        self.transform = transform
        self.child_nodes = []
        
    def write(self, writefunc, indent):
        id_name = self.armature.name + "_" + self.name
        flat_transform = [subitem for item in self.transform for subitem in item]
        writefunc(indent + f"""<node id="{id_name}" name="{self.name}" sid="{self.name}" type="JOINT">""")
        writefunc(indent + f"""  <matrix sid="transform">{' '.join([str(float(item)) for item in flat_transform])}</matrix>""")
        for child_node in self.child_nodes:
            child_node.write(writefunc, indent + "  ")
        writefunc(indent + f"""</node>""")    
        
class ColladaSceneNode:
    def __init__(self, sid, name):
        self.sid = sid
        self.name = name
        self.child_nodes = []
        
    def write(self, writefunc, indent):
        writefunc(indent + f"""<visual_scene id="{self.sid}" name="{self.name}">""")
        for child_node in self.child_nodes:
            child_node.write(writefunc, indent + "  ")
        writefunc(indent + f"""</visual_scene>""")

class ColladaMaterialNode:
    pass

class ColladaSkinnedGeometryNode:
    def __init__(self, sid, name, geometry, material, armature_node, skin):
        self.sid = sid
        self.name = name
        self.geometry = geometry
        self.material = material
        self.armature = armature_node
        self.skin = skin
    
    def write(self, writefunc, indent):
        writefunc(indent + f"""<node id="{self.sid}" name="{self.name}" type="NODE">""")
        writefunc(indent + f"""  <matrix sid="transform">1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1</matrix>""")
        writefunc(indent + f"""  <instance_controller url="#{self.skin.sid}">""")
        writefunc(indent + f"""    <skeleton>#{self.armature.name}</skeleton>""")
        writefunc(indent + f"""    <bind_material>""")
        writefunc(indent + f"""      <technique_common>""")
        writefunc(indent + f"""        <instance_material symbol="{self.material.name}" target="#{self.material.sid}">""")
        writefunc(indent + f"""          <bind_vertex_input semantic="UV0" input_semantic="TEXCOORD" input_set="0"/>""")
        writefunc(indent + f"""        </instance_material>""")
        writefunc(indent + f"""      </technique_common>""")
        writefunc(indent + f"""    </bind_material>""")
        writefunc(indent + f"""  </instance_controller>""")
        writefunc(indent + f"""</node>""")
        
        
class ColladaUnskinnedGeometryNode:
    def __init__(self, sid, name, geometry, material):
        self.sid = sid
        self.name = name
        self.geometry = geometry
        self.material = material
    
    def write(self, writefunc, indent):
        writefunc(indent + f"""<node id="{self.sid}" name="{self.name}" type="NODE">""")
        writefunc(indent + f"""  <matrix sid="transform">1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1</matrix>""")
        writefunc(indent + f"""  <instance_geometry url="#{self.geometry.sid}">""")
        writefunc(indent + f"""    <bind_material>""")
        writefunc(indent + f"""      <technique_common>""")
        writefunc(indent + f"""        <instance_material symbol="{self.material.name}" target="#{self.material.sid}">""")
        writefunc(indent + f"""          <bind_vertex_input semantic="UV0" input_semantic="TEXCOORD" input_set="0"/>""")
        writefunc(indent + f"""        </instance_material>""")
        writefunc(indent + f"""      </technique_common>""")
        writefunc(indent + f"""    </bind_material>""")
        writefunc(indent + f"""  </instance_geometry>""")
        writefunc(indent + f"""</node>""")

class ColladaDocument:
    def __init__(self):
        self.effects = []
        self.images = []
        self.materials = []
        self.geometries = []
        self.controllers = []
        
        self.scenes = []
        
    def write(self, path):
        with open(path, 'w') as F:
            def write_func(line):
                F.write(line + '\n')
        
            write_func(r"""<?xml version="1.0" encoding="utf-8"?>""")
            write_func(r"""<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">""")
            write_func(r"""  <asset>""")
            write_func(r"""    <up_axis>Y_UP</up_axis>""")
            write_func(r"""  </asset>""")
            
            write_func(r"""  <library_effects>""")
            self.write_child(self.effects, write_func, indent="    ")
            write_func(r"""  </library_effects>""")
            
            write_func(r"""  <library_images>""")
            self.write_child(self.images, write_func, indent="    ")
            write_func(r"""  </library_images>""")
            
            write_func(r"""  <library_materials>""")
            self.write_child(self.materials, write_func, indent="    ")
            write_func(r"""  </library_materials>""")
            
            write_func(r"""  <library_geometries>""")
            self.write_child(self.geometries, write_func, indent="    ")
            write_func(r"""  </library_geometries>""")
            
            write_func(r"""  <library_controllers>""")
            self.write_child(self.controllers, write_func, indent="    ")
            write_func(r"""  </library_controllers>""")
            
            write_func(r"""  <library_visual_scenes>""")
            self.write_child(self.scenes, write_func, indent="    ")
            write_func(r"""  </library_visual_scenes>""")
            
            write_func(r"""</COLLADA>""")
        
    def write_child(self, child, write_func, indent):
        for item in child:
            item.write(write_func, indent)
        