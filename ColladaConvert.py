import os
import struct 
import sys

from ManualCollada import *
from PXBIInterface import PXBIInterface    

"""
Borrowed from https://github.com/ThomIves/MatrixInverse,
following from this answer https://stackoverflow.com/a/62940942
"""
def invert_matrix(AM, IM):
    for fd in range(len(AM)):
        fdScaler = 1.0 / AM[fd][fd]
        for j in range(len(AM)):
            AM[fd][j] *= fdScaler
            IM[fd][j] *= fdScaler
        for i in list(range(len(AM)))[0:fd] + list(range(len(AM)))[fd+1:]:
            crScaler = AM[i][fd]
            for j in range(len(AM)):
                AM[i][j] = AM[i][j] - crScaler * AM[fd][j]
                IM[i][j] = IM[i][j] - crScaler * IM[fd][j]
    return IM

def flatten_list(lst):
    return [subitem for item in lst for subitem in item]


def PXBItoCollada(file, output_directory):
    pi = PXBIInterface.from_file(file)
    model = ColladaDocument()
    
    ####################
    #### START DUMP ####
    ####################
    textures = []
    effect_inputs = []
    images = []
    # Dump the textures
    # First to GTF, in case anybody wants to convert those manually
    for (file_id, texture_name), texture in zip(pi.texture_names, pi.texture_data_raw):
        texture_filepath = os.path.normpath(os.path.join(output_directory, os.path.splitext(texture_name[2:])[0] + '.gtf'))
        os.makedirs(os.path.split(texture_filepath)[0], exist_ok=True)
        with open(texture_filepath, 'wb') as F:
            F.write(texture)
    
    # Next do DDS
    for (file_id, texture_name), texture in zip(pi.texture_names, pi.texture_data):
        texture_filepath = os.path.normpath(os.path.join(output_directory, texture_name[2:]))
        os.makedirs(os.path.split(texture_filepath)[0], exist_ok=True)
        with open(texture_filepath, 'wb') as F:
            F.write(texture)
            
        use_name = os.path.split(texture_name)[-1]
        splitname = os.path.splitext(use_name)
        img_name = "_".join((splitname[0], splitname[1][1:]))
        surf_name = img_name + "-surf"
        sampler_name = img_name + "-sampler"
        map_name = img_name + "-map"
        
        image = ColladaImage(img_name, texture_name)
        surface = ColladaSurface(surf_name, image)
        sampler = ColladaSampler(sampler_name, surface)
        texmap = ColladaMap(map_name, sampler, "UV0")
        
        model.images.append(image)
        effect_inputs.append((surface, sampler))
        textures.append(texmap)
    
    
    materials = []
    mat_nodes = []
    for as_material in pi.materials:
        maps = {}
        local_samplers = []
        for texture_data in as_material.assigned_textures:
            role = texture_data.role
            idx = texture_data.tex_idx
            
            maps[role] = textures[idx]
            local_samplers.extend(effect_inputs[idx])
        
        effect = ColladaEffect(f"{as_material.name}_eff", local_samplers, "lambert", maps)
        mat = ColladaMaterial(f"{as_material.name}_ID", f"{as_material.name}", effect)
        model.effects.append(effect)
        model.materials.append(mat)   
        
        materials.append(mat)
        
        #matnode = scene.MaterialNode(f"{as_material.name}", mat, inputs=[])
        #materials.append(matnode)
    
    pi.bone_data[0][0] = "root"
    armature = ColladaArmatureNode("armature", [[1., 0., 0., 0.],
                                                [0., 1., 0., 0.],
                                                [0., 0., 1., 0.],
                                                [0., 0., 0., 1.]])
    bone_to_joint = {bone_idx: bone_data[1] for bone_idx, bone_data in enumerate(pi.bone_data)}
    joint_to_bone = {bone_data[1]: bone_idx for bone_idx, bone_data in enumerate(pi.bone_data)}
    bone_parents = {bone_idx: joint_to_bone.get(pi.joint_data[idx][3], -1) for bone_idx, idx in bone_to_joint.items()}
    n_accounted = 0
    
    parents = {i: [] for i in range(-1, len(bone_parents))}
    for child, parent in bone_parents.items():
        parents[parent].append(child)
    
    
    bonenodes = []
    for name, joint, transform in pi.bone_data:
        bone_node = ColladaBoneNode(name, armature, invert_matrix([list(item) for item in transform], 
                                                                  [[1., 0., 0., 0.],
                                                                   [0., 1., 0., 0.],
                                                                   [0., 0., 1., 0.],
                                                                   [0., 0., 0., 1.]]))
        bonenodes.append(bone_node)
    
    for idx, children in parents.items():
        if idx == -1:
            continue
        for child in children:
            bonenodes[idx].child_nodes.append(bonenodes[child])
    
    armature.child_nodes.extend([bonenodes[i] for i in parents[-1]])
    
        
    
    
    geom_nodes = []
    for i, mesh in enumerate(pi.meshes):
        input_list = ColladaInputList()
        sources = []
        if 'Position' in mesh.vertices[0]:
            vert_src = ColladaFloatSource(f"{mesh.name}-{i}-Position", [vert['Position'] for vert in mesh.vertices], ('X', 'Y', 'Z'))  
            input_list.add_input(len(input_list.inputs), 'VERTEX', vert_src)
            sources.append(vert_src)
        if 'Normal' in mesh.vertices[0]:
            normal_src = ColladaFloatSource(f"{mesh.name}-{i}-Normal", [vert['Normal'] for vert in mesh.vertices], ('X', 'Y', 'Z'))
            input_list.add_input(len(input_list.inputs), 'NORMAL', normal_src)
            sources.append(normal_src)
        if 'UV' in mesh.vertices[0]:
            uv_src = ColladaFloatSource(f"{mesh.name}-{i}-UV", [vert['UV'] for vert in mesh.vertices], ('S', 'T'))
            input_list.add_input(len(input_list.inputs), 'TEXCOORD', uv_src)
            sources.append(uv_src)
        if 'Tangent' in mesh.vertices[0]:
            tangent_src = ColladaFloatSource(f"{mesh.name}-{i}-Tangent", [vert['Tangent'] for vert in mesh.vertices], ('X', 'Y', 'Z'))
            input_list.add_input(len(input_list.inputs), 'TANGENT', tangent_src)
            sources.append(tangent_src)
        if 'Binormal' in mesh.vertices[0]:
            binormal_src = ColladaFloatSource(f"{mesh.name}-{i}-Binormal", [vert['Binormal'] for vert in mesh.vertices], ('X', 'Y', 'Z'))   
            input_list.add_input(len(input_list.inputs), 'BINORMAL', binormal_src)
            sources.append(binormal_src)
        if 'Color' in mesh.vertices[0]:
            color_src = ColladaFloatSource(f"{mesh.name}-{i}-Color", [vert['Color'] for vert in mesh.vertices], ('X', 'Y', 'Z'))   
            input_list.add_input(len(input_list.inputs), 'COLOR', color_src)
            sources.append(color_src)
        
        
        mat = materials[mesh.material_index]
        indices = flatten_list([[item for _ in input_list.inputs] for item in flatten_list(mesh.triangles)])
        triangle_set = ColladaTriangleSet(indices, input_list, mat)

        geom = ColladaGeometry(f"{mesh.name}-{i}" + "-ID", f"{mesh.name}-{i}" + "-mesh", sources, triangle_set)
        model.geometries.append(geom)
        
        
        skin_controller = ColladaSkinController("armature", geom, [bone[0] for bone in pi.bone_data],
                                                [bone[-1] for bone in pi.bone_data],
                                                [v['Weights'] for v in mesh.vertices],
                                                [v['BoneIndices'] for v in mesh.vertices])
        
        model.controllers.append(skin_controller)
        
        
        geom_nodes.append(ColladaGeometryNode(mesh.name, mesh.name, geom, mat, armature, skin_controller))
        
    
        
    
    
    scene = ColladaSceneNode("Scene", "Scene")
    armature.child_nodes.extend(geom_nodes)
    scene.child_nodes.append(armature)
    model.scenes.append(scene)
    
    base_filename = os.path.splitext(os.path.split(file)[-1])[0]
    
    model.write(f'{os.path.join(output_directory, base_filename)}.dae')
    
