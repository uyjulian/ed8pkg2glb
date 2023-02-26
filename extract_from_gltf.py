# Tool to extract meshes and skeleton from glTF for the ED8 COLLADA builder.
# Fairly rudimentary, will not be lossless compared to extracting from .pkg
# due to restrictions of glTF.
#
# GitHub eArmada8/ed8pkg2gltf

import json, numpy, os, io, struct, sys, glob
from pygltflib import GLTF2
from pyquaternion import Quaternion
from lib_fmtibvb import *

def process_nodes (gltf):
    heirarchy = []
    for i in range(len(gltf.nodes)):
        new_node = {}
        new_node['name'] = gltf.nodes[i].name
        if gltf.nodes[i].matrix is not None:
            matrix = numpy.array([gltf.nodes[i].matrix[0:4],\
                gltf.nodes[i].matrix[4:8], gltf.nodes[i].matrix[8:12], gltf.nodes[i].matrix[12:16]])
        else:
            matrix = numpy.array([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])
        if gltf.nodes[i].rotation is not None:
            matrix = Quaternion(w=gltf.nodes[i].rotation[3], x=gltf.nodes[i].rotation[0],\
                y=gltf.nodes[i].rotation[1], z=gltf.nodes[i].rotation[2]).transformation_matrix
        if gltf.nodes[i].translation is not None:
            matrix[0][3], matrix[1][3], matrix[2][3] = gltf.nodes[i].translation
        if gltf.nodes[i].scale is not None:
            scale_matrix = numpy.array([[gltf.nodes[i].scale[0],0,0,0],[0,gltf.nodes[i].scale[1],0,0],\
                [0,0,gltf.nodes[i].scale[2],0],[0,0,0,1]])
            matrix = numpy.dot(matrix, scale_matrix)
        new_node['matrix'] = [x for y in matrix.tolist() for x in y]
        if gltf.nodes[i].children is not None:
            new_node['children'] = gltf.nodes[i].children
        heirarchy.append(new_node)
    return(heirarchy)

def accessor_stride(gltf, accessor_num):
    accessor = gltf.accessors[accessor_num]
    componentSize = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
    componentCount = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT2': 4, 'MAT3': 9, 'MAT4': 16}
    return(componentCount[accessor.type] * componentSize[accessor.componentType])

#Does not support sparse
def read_stream (gltf, accessor_num):
    accessor = gltf.accessors[accessor_num]
    bufferview = gltf.bufferViews[accessor.bufferView]
    buffer = gltf.buffers[bufferview.buffer]
    componentType = {5120: 'b', 5121: 'B', 5122: 'h', 5123: 'H', 5125: 'I', 5126: 'f'}
    componentCount = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT2': 4, 'MAT3': 9, 'MAT4': 16}
    componentFormat = "<{0}{1}".format(componentCount[accessor.type],\
        componentType[accessor.componentType])
    componentStride = accessor_stride(gltf, accessor_num)
    data = []
    with io.BytesIO(gltf.get_data_from_buffer_uri(buffer.uri)) as f:
        f.seek(bufferview.byteOffset + accessor.byteOffset, 0)
        for i in range(accessor.count):
            data.append(list(struct.unpack(componentFormat, f.read(componentStride))))
            if (bufferview.byteStride is not None) and (bufferview.byteStride > componentStride):
                f.seek(bufferview.byteStride - componentStride, 1)
    if accessor.normalized == True:
        for i in range(len(data)):
            if componentType == 'b':
                data[i] = [x / ((2**(8-1))-1) for x in data[i]]
            elif componentType == 'B':
                data[i] = [x / ((2**8)-1) for x in data[i]]
            elif componentType == 'h':
                data[i] = [x / ((2**(16-1))-1) for x in data[i]]
            elif componentType == 'H':
                data[i] = [x / ((2**16)-1) for x in data[i]]
    return(data)

def dxgi_format (gltf, accessor_num):
    accessor = gltf.accessors[accessor_num]
    RGBAD = ['R','G','B','A','D']
    bytesize = {5120:'8', 5121: '8', 5122: '16', 5123: '16', 5125: '32', 5126: '32'}
    elementtype = {5120: 'SINT', 5121: 'UINT', 5122: 'SINT', 5123: 'UINT', 5125: 'UINT', 5126: 'FLOAT'}
    normelementtype = {5120: 'SNORM', 5121: 'UNORM', 5122: 'SNORM', 5123: 'UNORM'}
    numelements = {'SCALAR':1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
    dxgi_format = "".join([RGBAD[i]+bytesize[accessor.componentType] \
        for i in range(numelements[accessor.type])]) + '_'
    if accessor.normalized == True:
        dxgi_format += normelementtype[accessor.componentType]
    else:
        dxgi_format += elementtype[accessor.componentType]
    return(dxgi_format)

def dump_meshes (mesh_node, gltf):
    basename = mesh_node.name
    mesh = gltf.meshes[mesh_node.mesh]
    skin = gltf.skins[mesh_node.skin]
    vgmap = {gltf.nodes[skin.joints[i]].name:i for i in range(len(skin.joints))}
    submeshes = []
    for i in range(len(mesh.primitives)):
        submesh = {'name': '{0}_{1:02d}'.format(basename, i)}
        print("Reading mesh {0}...".format(submesh['name']))
        tops = {0: 'pointlist', 4: 'trianglelist', 5: 'trianglestrip'}
        submesh['fmt'] = {'stride': '0', 'topology': tops[mesh.primitives[i].mode],\
            'format': "DXGI_FORMAT_{0}".format(dxgi_format(gltf, mesh.primitives[i].indices)), 'elements': []}
        submesh['ib'] = [x for y in read_stream(gltf, mesh.primitives[i].indices) for x in y]
        submesh['vb'] = []
        elements = []
        AlignedByteOffset = 0
        Semantics = {'POSITION': ['POSITION','0'], 'NORMAL': ['NORMAL','0'], 'TANGENT': ['TANGENT','0'],\
            'TEXCOORD_0': ['TEXCOORD','0'], 'TEXCOORD_1': ['TEXCOORD','1'], 'TEXCOORD_2': ['TEXCOORD','2'],\
            'COLOR_0': ['COLOR','0'], 'COLOR_1': ['COLOR','1'], 'WEIGHTS_0': ['BLENDWEIGHTS','0'],\
            'JOINTS_0': ['BLENDINDICES','0']}
        for semantic in Semantics:
            if hasattr(mesh.primitives[i].attributes, semantic):
                accessor = getattr(mesh.primitives[i].attributes, semantic)
                if accessor is not None:
                    submesh['vb'].append({'SemanticName': Semantics[semantic][0], 'SemanticIndex': Semantics[semantic][1],\
                        'Buffer': read_stream(gltf, accessor)})
                    element = {'id': str(len(elements)), 'SemanticName': Semantics[semantic][0],\
                                'SemanticIndex': Semantics[semantic][1], 'Format': dxgi_format (gltf, accessor),\
                                'InputSlot': '0', 'AlignedByteOffset': str(AlignedByteOffset),\
                                'InputSlotClass': 'per-vertex', 'InstanceDataStepRate': '0'}
                    elements.append(element)
                    AlignedByteOffset += accessor_stride(gltf, accessor)
        submesh['fmt']['stride'] = str(AlignedByteOffset)
        submesh['fmt']['elements'] = elements
        submesh['vgmap'] = dict(vgmap)
        if mesh.primitives[i].material is not None:
            submesh['material'] = gltf.materials[mesh.primitives[i].material].name.split('-Skinned')[0]
        else:
            submesh['material'] = 'None'
        submeshes.append(submesh)
    return(submeshes)

def get_texture_details (gltf, texture_num):
    filter_codes = {9728: 'NEAREST', 9729: 'LINEAR', 9984: 'NEAREST_MIPMAP_NEAREST',\
        9985: 'LINEAR_MIPMAP_NEAREST', 9986: 'NEAREST_MIPMAP_LINEAR', 9987: 'LINEAR_MIPMAP_LINEAR'}
    wrap_codes = {33071: 'CLAMP', 33648: 'MIRROR', 10497: 'WRAP'}
    texture = {'uri': '', 'sampler_settings': ''}
    if gltf.textures[texture_num].source is not None:
        if gltf.images[gltf.textures[texture_num].source].uri is not None:
            texture['uri'] = gltf.images[gltf.textures[texture_num].source].uri
    if gltf.textures[texture_num].sampler is not None:
        sampler = gltf.samplers[gltf.textures[texture_num].sampler]
        if sampler.magFilter is not None:
            texture['sampler_settings'] += 'magFilter: {0}, '.format(filter_codes[sampler.magFilter])
        if sampler.minFilter is not None:
            texture['sampler_settings'] += 'minFilter: {0}, '.format(filter_codes[sampler.minFilter])
        if sampler.wrapS is not None:
            texture['sampler_settings'] += 'wrapS: {0}, '.format(wrap_codes[sampler.wrapS])
        if sampler.wrapT is not None:
            texture['sampler_settings'] += 'wrapT: {0}, '.format(wrap_codes[sampler.wrapT])
    texture['sampler_settings'] = ', '.join(texture['sampler_settings'].split(', ')[:-1])
    return(texture)

def build_materials (gltf):
    materials = [x for x in gltf.materials if 'Skinned' not in x.name]
    material_struct = {}
    for material in materials:
        name = material.name
        texture_list = {}
        if material.pbrMetallicRoughness is not None and material.pbrMetallicRoughness.baseColorTexture is not None:
            texture_list['baseColorTexture'] = get_texture_details(gltf, material.pbrMetallicRoughness.baseColorTexture.index)
        if material.normalTexture is not None:
            texture_list['normalTexture'] = get_texture_details(gltf, material.normalTexture.index)
        if material.occlusionTexture is not None:
            texture_list['occlusionTexture'] = get_texture_details(gltf, material.occlusionTexture.index)
        if material.emissiveTexture is not None:
            texture_list['emissiveTexture'] = get_texture_details(gltf, material.emissiveTexture.index)
        material_struct[name] = {'basic_texture_info_replace_me': texture_list}
    return(material_struct)

def image_list (material_struct):
    image_list = []
    material_tex_list = [v['basic_texture_info_replace_me'] for (k,v) in material_struct.items()]
    for texture in material_tex_list:
        image_list.extend([v['uri'] for (k,v) in texture.items()])
    return([{'uri': x} for x in list(set(image_list))])

def process_gltf(filename, overwrite = False):
    print("Processing {0}...".format(filename))
    gltf = GLTF2().load(filename)
    model_name = filename.split('.gltf')[0]
    if os.path.exists(model_name) and (os.path.isdir(model_name)) and (overwrite == False):
        if str(input(model_name + " folder exists! Overwrite? (y/N) ")).lower()[0:1] == 'y':
            overwrite = True
    if (overwrite == True) or not os.path.exists(model_name):
        if not os.path.exists(model_name):
            os.mkdir(model_name)
        if not os.path.exists(model_name + '/meshes'):
            os.mkdir(model_name + '/meshes')
        heirarchy = process_nodes(gltf)
        joint_nodes = [gltf.nodes[i].name for i in list(set([x for y in [x.joints for x in gltf.skins] for x in y]))]
        locators = [x.name for x in gltf.nodes if x.mesh is None and x.skin is None and x.name not in joint_nodes]
        mesh_nodes = [x for x in gltf.nodes if x.mesh is not None]
        material_struct = build_materials(gltf)
        for mesh_node in mesh_nodes:
            submeshes = dump_meshes(mesh_node, gltf)
            for i in range(len(submeshes)):
                write_fmt(submeshes[i]['fmt'], '{0}/meshes/{1}.fmt'.format(model_name, submeshes[i]['name']))
                write_ib(submeshes[i]['ib'], '{0}/meshes/{1}.ib'.format(model_name, submeshes[i]['name']), submeshes[i]['fmt'])
                write_vb(submeshes[i]['vb'], '{0}/meshes/{1}.vb'.format(model_name, submeshes[i]['name']), submeshes[i]['fmt'])
                with open('{0}/meshes/{1}.vgmap'.format(model_name, submeshes[i]['name']), 'wb') as f:
                    f.write(json.dumps(submeshes[i]['vgmap'], indent=4).encode("utf-8"))
                with open('{0}/meshes/{1}.material'.format(model_name, submeshes[i]['name']), 'wb') as f:
                    f.write(json.dumps({'material': submeshes[i]['material']}, indent=4).encode("utf-8"))
        metadata = {'name': model_name, 'pkg_name': model_name.upper(),\
            'images': image_list(material_struct),\
            'materials': material_struct, 'heirarchy': heirarchy, 'locators': locators}
        with open("{0}/metadata.json".format(model_name), 'wb') as f:
            f.write(json.dumps(metadata, indent=4).encode("utf-8"))
    
if __name__ == '__main__':
    # Set current directory
    os.chdir(os.path.abspath(os.path.dirname(__file__)))

    # If argument given, attempt to export from file in argument
    if len(sys.argv) > 1:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('-o', '--overwrite', help="Overwrite existing files", action="store_true")
        parser.add_argument('gltf_filename', help="Name of gltf file to process.")
        args = parser.parse_args()
        if os.path.exists(args.gltf_filename) and args.gltf_filename[-5:].lower() == '.gltf':
            process_gltf(args.gltf_filename, overwrite = args.overwrite)
    else:
        gltf_files = glob.glob('*.gltf')
        for i in range(len(gltf_files)):
            process_gltf(gltf_files[i])
