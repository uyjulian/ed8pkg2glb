# ED8 COLLADA builder, needs output from my fork of uyjulian/ed8pkg2glb.  Very broken.
#
# GitHub eArmada8/ed8pkg2gltf

import os, glob, numpy, json, io, xml.dom.minidom
import xml.etree.ElementTree as ET
from lib_fmtibvb import *

# Create the basic COLLADA XML document, with values that do not change from model to model (I think)
# TODO: Are units, gravity and time step constant?
def basic_collada():
    collada = ET.Element('COLLADA')
    collada.set("xmlns", "http://www.collada.org/2005/11/COLLADASchema")
    collada.set("version", "1.4.1")
    asset = ET.SubElement(collada, 'asset')
    asset_unit = ET.SubElement(asset, 'unit')
    asset_unit.set("meter", "0.0099999997764825")
    asset_unit.set("name", "centimeter")
    asset_up_axis = ET.SubElement(asset, 'up_axis')
    asset_up_axis.text = "Y_UP"
    library_physics_scenes = ET.SubElement(collada, 'library_physics_scenes')
    library_physics_scenes_ps = ET.SubElement(library_physics_scenes, 'physics_scene')
    library_physics_scenes_ps.set("id","MayaNativePhysicsScene")
    library_physics_scenes_ps_tc = ET.SubElement(library_physics_scenes_ps, 'technique_common')
    library_physics_scenes_ps_tc_gravity = ET.SubElement(library_physics_scenes_ps_tc, 'gravity')
    library_physics_scenes_ps_tc_gravity.text = "0 -980 0"
    library_physics_scenes_ps_tc_time_step = ET.SubElement(library_physics_scenes_ps_tc, 'time_step')
    library_physics_scenes_ps_tc_time_step.text = "0.0829999968409538"
    library_images = ET.SubElement(collada, 'library_images')
    library_materials = ET.SubElement(collada, 'library_materials')
    library_effects = ET.SubElement(collada, 'library_effects')
    library_geometries = ET.SubElement(collada, 'library_geometries')
    library_controllers = ET.SubElement(collada, 'library_controllers')
    library_visual_scenes = ET.SubElement(collada, 'library_visual_scenes')
    scene = ET.SubElement(collada, 'scene')
    instance_physics_scene = ET.SubElement(scene, 'instance_physics_scene')
    instance_physics_scene.set('url', '#MayaNativePhysicsScene')
    return(collada)

# Add image URIs
def add_images(collada, images):
    library_images = collada.find('library_images')
    for image in images:
        image_name = image.replace('.DDS','.dds').split('.dds')[0]
        image_element = ET.SubElement(library_images, 'image')
        image_element.set("id", os.path.basename(image_name))
        image_element.set("name", os.path.basename(image_name))
        image_element_init_from = ET.SubElement(image_element, 'init_from')
        image_element_init_from.text = '../../../' + image
        image_element_extra = ET.SubElement(image_element, 'extra')
        image_element_extra_technique = ET.SubElement(image_element_extra, 'technique')
        image_element_extra_technique.set("profile", "MAYA")
        image_element_extra_technique_dg = ET.SubElement(image_element_extra_technique, 'dgnode_type')
        image_element_extra_technique_dg.text = "kFile"
        image_element_extra_technique_is = ET.SubElement(image_element_extra_technique, 'image_sequence')
        image_element_extra_technique_is.text = "0"
    return(collada)

# Build the materials section
def add_materials(collada, materials):
    # Materials and effects can be done in parallel
    library_materials = collada.find('library_materials')
    library_effects = collada.find('library_effects')
    all_shader_switches = ['SHADER_'+x['m_effectVariant']['m_id'].split('#')[-1][0:4] for x in materials]
    filter_map = ['NEAREST', 'LINEAR', 'NEAREST_MIPMAP_NEAREST', 'LINEAR_MIPMAP_NEAREST', 'NEAREST_MIPMAP_LINEAR', 'LINEAR_MIPMAP_LINEAR']
    wrap_map = ['CLAMP','WRAP','CLAMP','CLAMP','MIRROR']
    # Skip the "Skinned" materials, those are added at time of compile
    for material in [x for x in materials if "-Skinned" not in x['Material']]:
        #Materials
        material_element = ET.SubElement(library_materials, 'material')
        material_element.set("id", material['Material'])
        material_element.set("name", material['Material'])
        instance_effect = ET.SubElement(material_element, 'instance_effect')
        instance_effect.set("url", "#{0}-fx".format(material['Material']))
        technique_hint = ET.SubElement(instance_effect, 'technique_hint')
        technique_hint.set("platform", "PC-DX")
        technique_hint.set("ref", "ForwardRender")
        #Effects
        effect_element = ET.SubElement(library_effects, 'effect')
        effect_element.set("id", material['Material'] + '-fx')
        profile_HLSL = ET.SubElement(effect_element, 'profile_HLSL')
        profile_HLSL.set('platform', 'PC-DX')
        include = ET.SubElement(profile_HLSL, 'include')
        include.set('sid','include')
        include.set('url','../../../shaders/ed8_chr.fx')
        for parameter in material['mu_shaderParameters']:
            # Float parameters - I haven't seen anything that isn't float, so I set everything here to float for now
            if isinstance(material['mu_shaderParameters'][parameter],list):
                #Material
                setparam = ET.SubElement(instance_effect, 'setparam')
                setparam.set("ref", material['Material'] + parameter)
                values = ET.SubElement(setparam, 'float{0}'.format({1:'', 2:2, 3:3, 4:4, 5:5}[len(material['mu_shaderParameters'][parameter])]))
                values.text = " ".join(["{0:g}".format(x) for x in material['mu_shaderParameters'][parameter]])
                #Effect
                newparam = ET.SubElement(profile_HLSL, 'newparam')
                newparam.set('sid', material['Material'] + parameter)
                annotate = ET.SubElement(newparam, 'annotate')
                annotate.set('name', 'UIName')
                string = ET.SubElement(annotate, 'string')
                string.text = parameter
                if len(material['mu_shaderParameters'][parameter]) == 1:
                    annotate = ET.SubElement(newparam, 'annotate')
                    annotate.set('name', 'UIMin')
                    string = ET.SubElement(annotate, 'float')
                    string.text = '0'
                    annotate = ET.SubElement(newparam, 'annotate')
                    annotate.set('name', 'UIMax')
                    string = ET.SubElement(annotate, 'float')
                    string.text = '1'
                else:
                    annotate = ET.SubElement(newparam, 'annotate')
                    annotate.set('name', 'UIType')
                    string = ET.SubElement(annotate, 'string')
                    string.text = 'Color'
                semantic = ET.SubElement(newparam, 'semantic')
                semantic.text = parameter
                values = ET.SubElement(newparam, 'float{0}'.format({1:'', 2:2, 3:3, 4:4, 5:5}[len(material['mu_shaderParameters'][parameter])]))
                values.text = " ".join(["{0:g}".format(x) for x in material['mu_shaderParameters'][parameter]])
            #Sampler definitions, for the effects section
            if isinstance(material['mu_shaderParameters'][parameter],dict):
                #None in Material
                #Effect
                newparam = ET.SubElement(profile_HLSL, 'newparam')
                newparam.set('sid', parameter)
                samplerDX = ET.SubElement(newparam, 'samplerDX')
                wrap_s = ET.SubElement(samplerDX, 'wrap_s')
                wrap_s.text = wrap_map[material['mu_shaderParameters'][parameter]['m_wrapS']]
                wrap_t = ET.SubElement(samplerDX, 'wrap_t')
                wrap_t.text = wrap_map[material['mu_shaderParameters'][parameter]['m_wrapT']]
                wrap_p = ET.SubElement(samplerDX, 'wrap_p')
                wrap_p.text = wrap_map[material['mu_shaderParameters'][parameter]['m_wrapR']]
                dxfilter = ET.SubElement(samplerDX, 'dxfilter')
                dxfilter.text = 'MIN_MAG_MIP_LINEAR' # This is also probably not correct but I don't know the possible codes
                func = ET.SubElement(samplerDX, 'func')
                func.text = 'NEVER' # Again, who knows?
                max_anisotropy = ET.SubElement(samplerDX, 'max_anisotropy')
                max_anisotropy.text = "{0:g}".format(material['mu_shaderParameters'][parameter]['m_maxAnisotropy'])
                lod_min_distance = ET.SubElement(samplerDX, 'lod_min_distance')
                lod_min_distance.text = '-3402823466385289'
                lod_max_distance = ET.SubElement(samplerDX, 'lod_max_distance')
                lod_max_distance.text = '3402823466385289'
                border_color = ET.SubElement(samplerDX, 'border_color')
                border_color.text = '0 0 0 0' # In the example it's always this, and in the phyre file it's a single 0.  I dunno.
            # Texture parameters - only support for 2D currently
            if isinstance(material['mu_shaderParameters'][parameter],str):
                texture_name = material['mu_shaderParameters'][parameter].replace('.DDS','.dds').split('/')[-1].split('.dds')[0]
                sampler_name = parameter + 'Sampler'
                #Material
                setparam = ET.SubElement(instance_effect, 'setparam')
                setparam.set("ref", material['Material'] + parameter)
                sampler = ET.SubElement(setparam, 'sampler2D')
                source = ET.SubElement(sampler, 'source')
                source.text = texture_name + "Surface"
                wrap_s = ET.SubElement(sampler, 'wrap_s')
                wrap_t = ET.SubElement(sampler, 'wrap_t')
                minfilter = ET.SubElement(sampler, 'minfilter')
                magfilter = ET.SubElement(sampler, 'magfilter')
                mipfilter = ET.SubElement(sampler, 'mipfilter')
                mipfilter.text = 'NONE'
                max_anisotropy = ET.SubElement(sampler, 'max_anisotropy')
                if sampler_name in material['mu_shaderParameters']:
                    wrap_s.text = wrap_map[material['mu_shaderParameters'][sampler_name]['m_wrapS']]
                    wrap_t.text = wrap_map[material['mu_shaderParameters'][sampler_name]['m_wrapT']]
                    minfilter.text = filter_map[material['mu_shaderParameters'][sampler_name]['m_minFilter']]
                    magfilter.text = filter_map[material['mu_shaderParameters'][sampler_name]['m_magFilter']]
                    max_anisotropy.text = "{0:g}".format(material['mu_shaderParameters'][sampler_name]['m_maxAnisotropy'])
                else: # CartoonMapSampler and SphereMapSampler
                    wrap_s.text = 'WRAP'
                    wrap_t.text = 'WRAP'
                    minfilter.text = 'NONE'
                    magfilter.text = 'NONE'
                    max_anisotropy.text = '0'
                setparam2 = ET.SubElement(instance_effect, 'setparam')
                setparam2.set("ref", texture_name + "Surface")
                surface = ET.SubElement(setparam2, 'surface')
                surface.set('type', '2D')
                init_from = ET.SubElement(surface, 'init_from')
                init_from.set("mip", "0")
                init_from.set("slice", "0")
                init_from.text = texture_name
                texformat = ET.SubElement(surface, 'format')
                texformat.text = "A8R8G8B8"
                #Effect
                newparam = ET.SubElement(profile_HLSL, 'newparam')
                newparam.set("sid", material['Material'] + parameter)
                annotate = ET.SubElement(newparam, 'annotate')
                annotate.set('name', 'UIName')
                string = ET.SubElement(annotate, 'string')
                string.text = parameter
                semantic = ET.SubElement(newparam, 'semantic')
                semantic.text = parameter
                sampler = ET.SubElement(newparam, 'sampler2D')
                source = ET.SubElement(sampler, 'source')
                source.text = texture_name + "Surface"
                wrap_s = ET.SubElement(sampler, 'wrap_s')
                wrap_s.text = 'WRAP'
                wrap_t = ET.SubElement(sampler, 'wrap_t')
                wrap_t.text = 'WRAP'
                minfilter = ET.SubElement(sampler, 'minfilter')
                minfilter.text = 'NONE'
                magfilter = ET.SubElement(sampler, 'magfilter')
                magfilter.text = 'NONE'
                mipfilter = ET.SubElement(sampler, 'mipfilter')
                mipfilter.text = 'NONE'
                max_anisotropy = ET.SubElement(sampler, 'max_anisotropy')
                max_anisotropy.text = '0'
                newparam2 = ET.SubElement(profile_HLSL, 'newparam')
                newparam2.set("sid", texture_name + "Surface")
                annotate = ET.SubElement(newparam2, 'annotate')
                annotate.set('name', 'UIName')
                string = ET.SubElement(annotate, 'string')
                string.text = texture_name
                surface = ET.SubElement(newparam2, 'surface')
                surface.set('type', '2D')
                init_from = ET.SubElement(surface, 'init_from')
                init_from.set("mip", "0")
                init_from.set("slice", "0")
                init_from.text = texture_name
                texformat = ET.SubElement(surface, 'format')
                texformat.text = "A8R8G8B8"
        extra = ET.SubElement(material_element, 'extra')
        technique = ET.SubElement(extra, 'technique')
        technique.set("profile", "PHYRE")
        material_switches = ET.SubElement(technique, 'material_switches')
        current_shader_switch = 'SHADER_' + material['m_effectVariant']['m_id'].split('#')[-1][0:4]
        # Switches are taken from the shader files themselves
        shader = ET.SubElement(material_switches, current_shader_switch)
        material_switch_list = ET.SubElement(technique, 'material_switch_list')
        #for material_switch in material['m_effectVariant']['material_swiches']:
            #material_switch_entry = ET.SubElement(material_switch_list, 'material_switch')
            #material_switch_entry.set("name", material_switch)
            #material_switch_entry.set("material_switch_value", material['m_effectVariant']['material_swiches'][material_switch])
        for material_switch in ['BLOOM_INTENSITY', 'SAMPLER_TOGGLE', 'VERTEX_COLOR_ENABLED', 'LIGHTING_ENABLED',\
                'DIFFUSE_ENABLED', 'DIFFUSE2_ENABLED', 'DIFFUSE3_ENABLED', 'ALPHA_BLENDING_ENABLED', 'NORMAL_MAPPING_ENABLED',\
                'WRAP_DIFFUSE_LIGHTING', 'SPECULAR_ENABLED', 'CASTS_SHADOWS', 'RECEIVE_SHADOWS', 'DOUBLE_SIDED', 'MOTION_BLUR_ENABLED',\
                'GENERATE_LIGHTS', 'SHININESS', 'RENDER_AS_LOW_RES', 'LIGHTMAP_OCCLUSION', 'SUBDIV', 'SUBDIV_SCALAR_DISPLACEMENT',\
                'SUBDIV_VECTOR_DISPLACEMENT', 'FOR_EFFECT', 'FOR_SHADOW', 'USE_OUTLINE', 'USE_OUTLINE_COLOR', 'ALPHA_TESTING_ENABLED',\
                'ADDITIVE_BLENDING_ENABLED', 'SUBTRACT_BLENDING_ENABLED', 'MULTIPLICATIVE_BLENDING_ENABLED', 'TRANSPARENT_DELAY_ENABLED',\
                'PORTRAIT_GLASS_FIX', 'FOG_ENABLED', 'NO_ALL_LIGHTING_ENABLED', 'NO_MAIN_LIGHT_SHADING_ENABLED',\
                'FORCE_CHAR_LIGHT_DIRECTION_ENABLED', 'PER_MATERIAL_MAIN_LIGHT_CLAMP_ENABLED', 'SHADOW_COLOR_SHIFT_ENABLED',\
                'CARTOON_SHADING_ENABLED', 'SPECULAR_COLOR_ENABLED', 'SPECULAR_MAPPING_ENABLED', 'RIM_LIGHTING_ENABLED',\
                'RIM_TRANSPARENCY_ENABLED', 'NORMAL_MAPP_DXT5_NM_ENABLED', 'EMISSION_MAPPING_ENABLED', 'SPHERE_MAPPING_ENABLED',\
                'SPHERE_RECEIVE_OFFSET_ENABLED', 'SPHERE_MAPPING_HAIRCUTICLE_ENABLED', 'CUBE_MAPPING_ENABLED', 'DUDV_MAPPING_ENABLED',\
                'GLARE_ENABLED', 'MULTI_UV_ENANLED', 'MULTI_UV_PROJTEXCOORD', 'MULTI_UV_ADDITIVE_BLENDING_ENANLED', 'MULTI_UV_DUDV_ENANLED',\
                'MULTI_UV_MULTIPLICATIVE_BLENDING_ENANLED', 'MULTI_UV_MULTIPLICATIVE_BLENDING_EX_ENANLED', 'MULTI_UV_FACE_ENANLED',\
                'MULTI_UV_NORMAL_MAPPING_ENABLED', 'MULTI_UV_SPECULAR_MAPPING_ENABLED', 'MULTI_UV_GLARE_MAPPING_ENABLED',\
                'MULTI_UV_NO_DIFFUSE_MAPPING_ENANLED', 'MULTI_UV2_ENANLED', 'MULTI_UV2_ADDITIVE_BLENDING_ENANLED',\
                'MULTI_UV2_MULTIPLICATIVE_BLENDING_ENANLED', 'MULTI_UV2_MULTIPLICATIVE_BLENDING_EX_ENANLED',\
                'MULTI_UV2_SPECULAR_MAPPING_ENABLED', 'GAME_MATERIAL_ID', 'GAME_MATERIAL_TEXCOORD', 'GLARE_INTENSITY']:
            material_switch_entry = ET.SubElement(material_switch_list, 'material_switch')
            material_switch_entry.set("name", material_switch)
            material_switch_entry.set("material_switch_value", '0')
        for i in range(len(all_shader_switches)):
            material_switch_entry = ET.SubElement(material_switch_list, 'material_switch')
            material_switch_entry.set("name", all_shader_switches[i])
            if all_shader_switches[i] == current_shader_switch:
                material_switch_entry.set("material_switch_value", "1")
            else:
                material_switch_entry.set("material_switch_value", "0")
        forwardrendertechnique = ET.SubElement(profile_HLSL, 'technique')
        forwardrendertechnique.set('sid','ForwardRender')
        renderpass = ET.SubElement(forwardrendertechnique, 'pass')
        shader = ET.SubElement(renderpass, 'shader')
        shader.set('stage','VERTEX')
        for parameter in material['mu_shaderParameters']:
            switch_bind = ET.SubElement(shader, 'bind')
            switch_bind.set('symbol', parameter)
            switch_param = ET.SubElement(switch_bind, 'param')
            switch_param.set('ref', material['Material'] + parameter)
        extra = ET.SubElement(effect_element, 'extra')
        technique = ET.SubElement(extra, 'technique')
        technique.set('profile', 'PHYRE')
        context_switches = ET.SubElement(technique, 'context_switches')
        supported_lights = ET.SubElement(context_switches, 'supported_lights')
        supported_lights.set('max_light_count', '0')
        supported_shadows = ET.SubElement(context_switches, 'supported_shadows')
    return(collada)

# Change matrices to numpy arrays, add parent bone ID, world space matrix, inverse bind matrix
def add_bone_info(skeleton):
    for i in range(len(skeleton)):
        if 'children' not in skeleton[i].keys():
            skeleton[i]['children'] = []
    for i in range(len(skeleton)):
        if 'matrix' in skeleton[i]:
            skeleton[i]['matrix'] = numpy.array([skeleton[i]['matrix'][0:4],\
                                                 skeleton[i]['matrix'][4:8],\
                                                 skeleton[i]['matrix'][8:12],\
                                                 skeleton[i]['matrix'][12:16]])
        else:
            skeleton[i]['matrix'] = numpy.array([1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1])
        if i == 0:
            skeleton[i]['parent'] = -1
            skeleton[i]['abs_matrix'] = skeleton[i]['matrix']
        else:
            skeleton[i]['parent'] = [j for j in range(len(skeleton)) if i in skeleton[j]['children']][0]
            skeleton[i]['abs_matrix'] = numpy.dot(skeleton[i]['matrix'], skeleton[skeleton[i]['parent']]['abs_matrix'])
        skeleton[i]['inv_matrix'] = numpy.linalg.inv(skeleton[i]['abs_matrix'])
    return(skeleton)

def get_joint_list(vgmaps, skeleton):
    i = 0
    joint_list = {}
    for bone in skeleton:
        if bone['name'] in vgmaps:
            joint_list[bone['name']] = i
            i += 1
    return(joint_list)

def get_bone_dict(skeleton):
    bone_dict = {}
    for i in range(len(skeleton)):
        bone_dict[skeleton[i]['name']] = i
    return(bone_dict)

# Recursive function to fill out the entire node tree; call with the first node and i = 0
def get_children(parent_node, i, metadata):
    node = ET.SubElement(parent_node, 'node')
    node.set('id', metadata['heirarchy'][i]['name'])
    node.set('name', metadata['heirarchy'][i]['name'])
    node.set('sid', metadata['heirarchy'][i]['name'])
    node.set('type', 'NODE')
    if 'matrix' in metadata['heirarchy'][i]:
        matrix = ET.SubElement(node, 'matrix')
        matrix.text = " ".join([str(x) for x in metadata['heirarchy'][i]['matrix'].flatten('F')])
    if 'children' in metadata['heirarchy'][i].keys():
        for j in range(len(metadata['heirarchy'][i]['children'])):
            if metadata['heirarchy'][i]['children'][j] < len(metadata['heirarchy']):
                get_children(node, metadata['heirarchy'][i]['children'][j], metadata)
    extra = ET.SubElement(node, 'extra')
    technique = ET.SubElement(extra, 'technique')
    if metadata['heirarchy'][i]['name'] in metadata['locators']:
        technique.set('profile', 'PHYRE')
        locator = ET.SubElement(technique, 'locator')
        locator.text = '1'
    else:
        technique.set('profile', 'MAYA')
        dynamic_attributes = ET.SubElement(technique, 'dynamic_attributes')
        filmboxTypeID = ET.SubElement(dynamic_attributes, 'filmboxTypeID')
        filmboxTypeID.set('short_name', 'filmboxTypeID')
        filmboxTypeID.set('type', 'int')
        filmboxTypeID.text = '5'
        segment_scale_compensate = ET.SubElement(technique, 'segment_scale_compensate')
        segment_scale_compensate.text = '0'
    return

# Build out the base node tree, run this before building geometries
def add_skeleton(collada, metadata):
    library_visual_scenes = collada.find('library_visual_scenes')
    visual_scene = ET.SubElement(library_visual_scenes, 'visual_scene')
    visual_scene.set('id', 'VisualSceneNode')
    visual_scene.set('name', metadata['name'])
    get_children(visual_scene, 0, metadata)
    extra = ET.SubElement(visual_scene, 'extra')
    technique = ET.SubElement(extra, 'technique')
    technique.set('profile','FCOLLADA')
    start_time = ET.SubElement(technique, 'start_time')
    start_time.text = '0'
    end_time = ET.SubElement(technique, 'end_time')
    end_time.text = '8.333333015441895'
    scene = collada.find('scene')
    instance_visual_scene = ET.SubElement(scene, 'instance_visual_scene')
    instance_visual_scene.set('url', '#VisualSceneNode')
    return(collada)

# Add geometries and skin them.  Needs a base node tree to build links to.
def add_geometries_and_controllers(collada, submeshes, skeleton, joint_list, materials):
    library_geometries = collada.find('library_geometries')
    library_controllers = collada.find('library_controllers')
    bone_dict = get_bone_dict(skeleton)
    for submesh in submeshes:
        semantics_list = [x['SemanticName'] for x in submesh["vb"]]
        geometry = ET.SubElement(library_geometries, 'geometry')
        geometry.set("id", submesh['name'])
        geometry.set("name", submesh['name'])
        mesh = ET.SubElement(geometry, 'mesh')
        semantic_counter = 0
        for vb in submesh["vb"]:
            if vb['SemanticName'] in ['POSITION', 'NORMAL', 'TEXCOORD', 'TANGENT', 'BINORMAL']:
                if vb['SemanticName'] == 'POSITION':
                    source_id = submesh['name'] + '-positions'
                    source_name = 'position'
                    param_names = ['X', 'Y', 'Z', 'W']
                elif vb['SemanticName'] == 'NORMAL':
                    source_id = submesh['name'] + '-normals'
                    source_name = 'normal'
                    param_names = ['X', 'Y', 'Z', 'W']
                elif vb['SemanticName'] == 'TEXCOORD':
                    source_id = submesh['name'] + '-UV' + vb['SemanticIndex']
                    source_name = 'UV' + vb['SemanticIndex']
                    param_names = ['S', 'T', 'R']
                elif vb['SemanticName'] == 'TANGENT':
                    source_id = submesh['name'] + '-UV' + vb['SemanticIndex'] + '-tangents'
                    source_name = 'UV' + vb['SemanticIndex'] + '-tangents'
                    param_names = ['X', 'Y', 'Z', 'W']
                elif vb['SemanticName'] == 'BINORMAL':
                    source_id = submesh['name'] + '-UV' + vb['SemanticIndex'] + '-binormals'
                    source_name = 'UV' + vb['SemanticIndex'] + '-binormals'
                    param_names = ['X', 'Y', 'Z', 'W']
                source = ET.SubElement(mesh, 'source')
                source.set("id", source_id)
                source.set("name", source_name)
                float_array = ET.SubElement(source, 'float_array')
                float_array.set("id", source_id + '-array')
                float_array.set("count", str(len([x for y in vb['Buffer'] for x in y])))
                float_array.text = " ".join(["{0:g}".format(x) for y in vb['Buffer'] for x in y])
                technique_common = ET.SubElement(source, 'technique_common')
                accessor = ET.SubElement(technique_common, 'accessor')
                accessor.set('source', '#' + source_id + '-array')
                accessor.set('count', str(len(vb['Buffer'])))
                accessor.set('stride', str(len(vb['Buffer'][0])))
                for i in range(len(vb['Buffer'][0])):
                    param = ET.SubElement(accessor, 'param')
                    param.set('name', param_names[i])
                    param.set('type', 'float')
        if 'BLENDWEIGHTS' in semantics_list and 'BLENDINDICES' in semantics_list:
            blendweights = [x['Buffer'] for x in submesh["vb"] if x['SemanticName'] == 'BLENDWEIGHTS'][0]
            blendindices = [x['Buffer'] for x in submesh["vb"] if x['SemanticName'] == 'BLENDINDICES'][0]
            blendjoints = joint_list
            new_weights = []
            new_indices = []
            local_to_global_joints = {v:joint_list[k] for (k,v) in submesh['vgmap'].items()}
            for i in range(len(blendweights)):
                new_weight = []
                new_index = []
                for j in range(len(blendweights[i])):
                    if blendweights[i][j] > 0.000001:
                        new_weight.append(blendweights[i][j])
                        new_index.append(local_to_global_joints[blendindices[i][j]])
                new_weights.append(new_weight)
                new_indices.append(new_index)
            #Uncomment the next 3 lines to force local bones instead of global bones
            #new_weights = blendweights
            #new_indices = blendindices
            #blendjoints = submesh['vgmap']
            controller = ET.SubElement(library_controllers, 'controller')
            controller.set('id', submesh['name'] + '-skin')
            controller.set('name', 'skinCluster_' + submesh['name']) #Maya does skinCluster1, skinCluster2... dunno if this matters
            skin = ET.SubElement(controller, 'skin')
            skin.set('source', '#' + submesh['name'])
            bind_shape_matrix = ET.SubElement(skin, 'bind_shape_matrix')
            bind_shape_matrix.text = '1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1'
            vgmap_source = ET.SubElement(skin, 'source')
            vgmap_source.set('id', submesh['name'] + '-skin-joints')
            vgmap_name_array = ET.SubElement(vgmap_source, 'Name_array')
            vgmap_name_array.set('id', submesh['name'] + '-skin-joints-array')
            vgmap_name_array.set('count', str(len(blendjoints)))
            vgmap_name_array.text = " ".join(blendjoints.keys())
            for bone in blendjoints.keys():
                bone_node = [x for x in collada.iter() if 'sid' in x.attrib and x.attrib['sid'] == bone][0]
                bone_node.set('type', 'JOINT')
            technique_common = ET.SubElement(vgmap_source, 'technique_common')
            accessor = ET.SubElement(technique_common, 'accessor')
            accessor.set('source', '#' + submesh['name'] + '-skin-joints-array')
            accessor.set('count', str(len(blendjoints)))
            accessor.set('stride', '1')
            param = ET.SubElement(accessor, 'param')
            param.set('name', 'JOINT')
            param.set('type', 'Name')
            inv_bind_mtx_source = ET.SubElement(skin, 'source')
            inv_bind_mtx_source.set('id', submesh['name'] + '-skin-bind_poses')
            inv_bind_mtx_array = ET.SubElement(inv_bind_mtx_source, 'float_array')
            inv_bind_mtx_array.set('id', submesh['name'] + '-skin-bind_poses-array')
            inv_bind_mtx_array.set('count', str(len(blendjoints) * 16))
            inv_bind_mtx_array.text = " ".join(["{0:g}".format(x) for y in [skeleton[bone_dict[x]]['inv_matrix'].flatten('F')\
                for x in blendjoints.keys()] for x in y])
            technique_common = ET.SubElement(inv_bind_mtx_source, 'technique_common')
            accessor = ET.SubElement(technique_common, 'accessor')
            accessor.set('source', '#' + submesh['name'] + '-skin-bind_poses-array')
            accessor.set('count', str(len(blendjoints)))
            accessor.set('stride', '16')
            param = ET.SubElement(accessor, 'param')
            param.set('name', 'TRANSFORM')
            param.set('type', 'float4x4')
            blendweights_source = ET.SubElement(skin, 'source')
            blendweights_source.set("id", submesh['name'] + '-skin-weights')
            blendweights_source.set("name", 'skin-weights')
            float_array = ET.SubElement(blendweights_source, 'float_array')
            float_array.set("id", submesh['name'] + '-skin-weights-array')
            float_array.set("count", str(len([x for y in new_weights for x in y])))
            float_array.text = " ".join(["{0:g}".format(x) for y in new_weights for x in y])
            technique_common = ET.SubElement(blendweights_source, 'technique_common')
            accessor = ET.SubElement(technique_common, 'accessor')
            accessor.set('source', '#' + submesh['name'] + '-skin-weights-array')
            accessor.set('count', str(len([x for y in new_weights for x in y])))
            accessor.set('stride', '1')
            param = ET.SubElement(accessor, 'param')
            param.set('name', 'WEIGHT')
            param.set('type', 'float')
            joints = ET.SubElement(skin, 'joints')
            vgmap_input = ET.SubElement(joints, 'input')
            vgmap_input.set('semantic', 'JOINT')
            vgmap_input.set('source', '#' + submesh['name'] + '-skin-joints')
            inv_bind_mtx_input = ET.SubElement(joints, 'input')
            inv_bind_mtx_input.set('semantic', 'INV_BIND_MATRIX')
            inv_bind_mtx_input.set('source', '#' + submesh['name'] + '-skin-bind_poses')
            # Create an empty vertex weight group, will be filled as we read in the vertex buffers
            vertex_weights = ET.SubElement(skin, 'vertex_weights')
            vertex_weights.set("count", str(len(new_indices)))
            joint_input = ET.SubElement(vertex_weights, 'input')
            joint_input.set('semantic', 'JOINT')
            joint_input.set('source', '#' + submesh['name'] + '-skin-joints')
            joint_input.set('offset', '0')
            weight_input = ET.SubElement(vertex_weights, 'input')
            weight_input.set('semantic', 'WEIGHT')
            weight_input.set('source', '#' + submesh['name'] + '-skin-weights')
            weight_input.set('offset', '1')
            vcount = ET.SubElement(vertex_weights, 'vcount')
            vcount.text = " ".join([str(len(x)) for x in new_indices])
            v = ET.SubElement(vertex_weights, 'v')
            blend_indices = [x for y in new_indices for x in y]
            v.text = " ".join([str(x) for y in [[blend_indices[i],i] for i in range(len(blend_indices))] for x in y])
        vertices = ET.SubElement(mesh, 'vertices')
        vertices.set('id', submesh['name'] + '-vertices')
        vertices_input = ET.SubElement(vertices, 'input')
        vertices_input.set('semantic', 'POSITION')
        vertices_input.set('source', '#' + submesh['name'] + '-positions')
        triangles = ET.SubElement(mesh, 'triangles')
        triangles.set('material', submesh['name'] + 'SG')
        triangles.set('count', str(len(submesh['ib'])))
        input_count = 0
        for vb in submesh["vb"]:
            if vb['SemanticName'] in ['POSITION', 'NORMAL', 'TEXCOORD', 'TANGENT', 'BINORMAL']:
                triangle_input = ET.SubElement(triangles, 'input')
                if vb['SemanticName'] == 'POSITION':
                    triangle_input.set('semantic', 'VERTEX')
                    triangle_input.set('source', '#' + submesh['name'] + '-vertices')
                elif vb['SemanticName'] == 'NORMAL':
                    triangle_input.set('semantic', 'NORMAL')
                    triangle_input.set('source', '#' + submesh['name'] + '-normals')
                elif vb['SemanticName'] == 'TEXCOORD':
                    triangle_input.set('semantic', 'TEXCOORD')
                    triangle_input.set('source', '#' + submesh['name'] + '-UV' + vb['SemanticIndex'])
                elif vb['SemanticName'] == 'TANGENT':
                    triangle_input.set('semantic', 'TEXTANGENT')
                    triangle_input.set('source', '#' + submesh['name'] + '-UV' + vb['SemanticIndex'] + '-tangents')
                elif vb['SemanticName'] == 'BINORMAL':
                    triangle_input.set('semantic', 'TEXBINORMAL')
                    triangle_input.set('source', '#' + submesh['name'] + '-UV' + vb['SemanticIndex'] + '-binormals')
                triangle_input.set('offset', str(input_count))
                input_count += 1
                if vb['SemanticName'] in ['TEXCOORD', 'TANGENT', 'BINORMAL']:
                    triangle_input.set('set', vb['SemanticIndex'])
        p = ET.SubElement(triangles, 'p')
        p.text = " ".join([str(x) for y in [[x]*input_count for x in [x for y in submesh['ib'] for x in y]] for x in y])
        extra = ET.SubElement(geometry, 'extra')
        technique = ET.SubElement(extra, 'technique')
        technique.set('profile', 'MAYA')
        double_sided = ET.SubElement(technique, 'double_sided')
        double_sided.text = '1'
        # Create geometry node
        meshname = "".join(submesh["name"].split("_")[:-1])
        mesh_node = [x for x in collada.iter() if 'sid' in x.attrib and x.attrib['sid'] == meshname][0]
        instance_controller = ET.SubElement(mesh_node, 'instance_controller')
        instance_controller.set('url', '#' + submesh["name"] + '-skin')
        controller_skeleton = ET.SubElement(instance_controller, 'skeleton')
        controller_skeleton.text = '#' + skeleton[skeleton[0]['children'][0]]['name'] # Should always be 'up_point' or its equivalent!
        bind_material = ET.SubElement(instance_controller, 'bind_material')
        technique_common = ET.SubElement(bind_material, 'technique_common')
        instance_material = ET.SubElement(technique_common, 'instance_material')
        instance_material.set('symbol', submesh['name'] + 'SG')
        instance_material.set('target', '#' + submesh['material']['material'].split("-Skinned")[0])
        material = [x for x in materials if x['Material'] == submesh['material']['material']][0]
        for parameter in material['mu_shaderParameters']:
            # Texture parameters - I think these are constant from texture to texture and model to model, variations are in the effects?
            if isinstance(material['mu_shaderParameters'][parameter],str):
                texture_name = material['mu_shaderParameters'][parameter].replace('.DDS','.dds').split('/')[-1].split('.dds')[0]
                bind = ET.SubElement(instance_material, 'bind')
                bind.set("semantic", parameter)
                bind.set("target", texture_name + '-lib/outColor')
                extra = ET.SubElement(bind, 'extra')
                technique = ET.SubElement(extra, 'technique')
                technique.set('profile', 'PSSG')
                param = ET.SubElement(technique, 'param')
                param.set("name", parameter)
        extra = ET.SubElement(instance_controller, 'extra')
        technique = ET.SubElement(extra, 'technique')
        technique.set('profile', 'PHYRE')
        object_render_properties = ET.SubElement(technique, 'object_render_properties')
        object_render_properties.set('castsShadows', '1')
        object_render_properties.set('receiveShadows', '1')
        object_render_properties.set('visibleInReflections', '1')
        object_render_properties.set('visibleInRefractions', '1')
        object_render_properties.set('motionBlurEnabled', '1')
    return(collada)

def write_shader(materials):
    if not os.path.exists("shaders"):
        os.mkdir("shaders")
    filename = 'shaders/ed8_chr.fx'
    shaderfx = '/*This dummy shader is used to add the correct shader parameters to the .dae.phyre*/\r\n\r\n'
    #shaderfx += ", ".join(['"SHADER_{0}"'.format(x['m_effectVariant']['m_id'].split('#')[1][0:4]) for x in materials]) + '\r\n'
    #shaderfx += ", ".join(['"ed8_chr.fx#{0}"'.format(x['m_effectVariant']['m_id'].split('#')[1][0:6]) for x in materials]) + '\r\n'
    for material in materials:
        shaderfx += '#ifdef SHADER_{0}\r\n'.format(material['m_effectVariant']['m_id'].split('#')[1][0:4])
        for parameter in material['mu_shaderParameters']:
            if isinstance(material['mu_shaderParameters'][parameter],list):
                if len(material['mu_shaderParameters'][parameter]) == 1:
                    valuetype = 'half'
                    value = "{0:.3f}".format(material['mu_shaderParameters'][parameter][0])
                else:
                    valuetype = 'half{0}'.format(len(material['mu_shaderParameters'][parameter]))
                    value = "float{0}({1})".format(len(material['mu_shaderParameters'][parameter]),\
                        ", ".join(["{0:.3f}".format(x) for x in material['mu_shaderParameters'][parameter]]))
                shaderfx += '{0} {1} : {1} = {2};'.format(valuetype, parameter, value)
            if isinstance(material['mu_shaderParameters'][parameter],dict):
                shaderfx += 'sampler {0} : {0};'.format(parameter)
            if isinstance(material['mu_shaderParameters'][parameter],str):
                shaderfx += 'Texture2D {0} : {0};'.format(parameter)
            shaderfx += '\r\n'
        shaderfx  += '#endif //! SHADER_{0}\r\n\r\n\r\n'.format(material['m_effectVariant']['m_id'].split('#')[1][0:4])
    shaderfx += '#ifdef SUBDIV\r\n#undef SKINNING_ENABLED\r\n#undef INSTANCING_ENABLED\r\n#endif // SUBDIV\r\n\r\n'
    shaderfx += '#ifdef SUBDIV_SCALAR_DISPLACEMENT\r\nTexture2D<half> DisplacementScalar;\r\n#endif // SUBDIV_SCALAR_DISPLACEMENT\r\n\r\n'
    shaderfx += '#ifdef SUBDIV_VECTOR_DISPLACEMENT\r\nTexture2D<half4> DisplacementVector;\r\n#define USE_TANGENTS\r\n#endif // SUBDIV_VECTOR_DISPLACEMENT\r\n\r\n'
    shaderfx += '#if defined(SUBDIV_SCALAR_DISPLACEMENT) || defined(SUBDIV_VECTOR_DISPLACEMENT)\r\nhalf DisplacementScale = 1.0f;\r\n'
    shaderfx += '#define USE_UVS\r\n#endif // defined(SUBDIV_SCALAR_DISPLACEMENT) || defined(SUBDIV_VECTOR_DISPLACEMENT)'
    with open(filename, 'wb') as f:
        f.write(shaderfx.encode('utf-8'))

def write_processing_batch_file(metadata):
    batch_file = '''@ECHO OFF
set "SCE_PHYRE=%cd%"
CSIVAssetImportTool.exe -fi="chr\chr\{0}\{0}.dae" -platform="D3D11" -write=all
PhyreDummyShaderCreator.exe D3D11\chr\chr\{0}\{0}.dae.phyre
del *.fx
del *.cgfx
copy D3D11\chr\chr\{0}\{0}.dae.phyre .
python replace_shader_references.py
del {0}.dae.phyre.bak
move {0}.dae.phyre {1}
'''.format(metadata['name'], metadata['pkg_name'])
    image_folders = list(set([os.path.dirname(x['uri']).replace('/','\\') for x in metadata['images']]))
    if len(image_folders) > 0:
        for folder in image_folders:
            batch_file += '\r\ncopy D3D11\{0}\*.* {1}'.format(folder, metadata['pkg_name'])
    batch_file += '\r\npython write_pkg.py {0}'.format(metadata['pkg_name'])
    with open('RunMe.bat', 'wb') as f:
        f.write(batch_file.encode('utf-8'))
    return

def build_collada():
    if os.path.exists('metadata.json'):
        metadata = read_struct_from_json('metadata.json')
        print("Processing {0}...".format(metadata['pkg_name']))
        submeshes = []
        meshes = [x.split('meshes\\')[1].split('.fmt')[0] for x in glob.glob('meshes/*.fmt')]
        for filename in meshes:
            try:
                print("Reading submesh {0}...".format(filename))
                submesh = {'name': filename}
                submesh['fmt'] = read_fmt('meshes/'+filename+'.fmt')
                submesh['ib'] = read_ib('meshes/'+filename+'.ib', submesh['fmt'])
                submesh['vb'] = read_vb('meshes/'+filename+'.vb', submesh['fmt'])
                submesh['vgmap'] = read_struct_from_json('meshes/'+filename+'.vgmap')
                submesh['material'] = read_struct_from_json('meshes/'+filename+'.material')
                submeshes.append(submesh)
            except FileNotFoundError:
                print("Submesh {0} not found or corrupt, skipping...".format(filename))
        collada = basic_collada()
        images_data = [x['uri'] for x in metadata['images']]
        collada = add_images(collada, images_data)
        print("Adding materials...")
        collada = add_materials(collada, metadata['materials'])
        print("Adding skeleton...")
        skeleton = add_bone_info(metadata['heirarchy'])
        joint_list = get_joint_list([x for y in [x['vgmap'].keys() for x in submeshes] for x in y]+[skeleton[1]['name']], skeleton)
        collada = add_skeleton(collada, metadata)
        print("Adding geometry...")
        collada = add_geometries_and_controllers(collada, submeshes, skeleton, joint_list, metadata['materials'])
        print("Writing COLLADA file...")
        with io.BytesIO() as f:
            f.write(ET.tostring(collada, encoding='utf-8', xml_declaration=True))
            f.seek(0)
            dom = xml.dom.minidom.parse(f)
            pretty_xml_as_string = dom.toprettyxml(indent='  ')
            pathname = 'chr/chr/{0}/'.format(metadata['name'])
            if not os.path.exists(pathname):
                os.makedirs(pathname)
            with open(pathname + metadata['name'] + ".dae", 'w') as f2:
                f2.write(pretty_xml_as_string)
        print("Writing shader file...")
        write_shader(metadata['materials'])
        print("Writing RunMe.bat.")
        write_processing_batch_file(metadata)
    return

if __name__ == '__main__':
    # Set current directory
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    build_collada()