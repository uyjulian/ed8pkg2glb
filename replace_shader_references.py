# ED8 .dae.phyre shader fixer, needs output from my fork of uyjulian/ed8pkg2glb.
# After running build_collada.py, then CSIVAssetImportTool.exe, copy the compiled
# .dae.phyre file into the directory with metadata.json and run this script to
# replace the shader references to the true shaders.
#
# GitHub eArmada8/ed8pkg2gltf

import os, json, shutil

def make_true_shader_dict(metadata):
    true_shader_dict = {}
    true_shader_dict.update({k:b'\x00'+v['shader'].encode() for (k,v) in metadata['materials'].items()})
    true_shader_dict.update({k+'-Skinned':b'\x00'+v['skinned_shader'].encode() for (k,v) in metadata['materials'].items()})
    return(true_shader_dict)

def make_fake_shader_dict():
    if os.path.exists('materials_list.txt'):
        fake_shader_dict = {}
        with open('materials_list.txt', 'r') as f:
            for line in f:
                entry = line.split('#')
                if len(entry) > 2:
                    data = [x.split(" ")[0] for x in entry[1:3]]
                    fake_shader_dict[data[1].strip()] = data[0]
        return(fake_shader_dict)
    else:
        return False

def replace_shader_references(filedata, true_shader_dict, fake_shader_dict):
    if filedata[0:4] == b'RYHP':
        shader_loc = filedata.find(b'\x00shader', 1)
        new_phyre = filedata[0:shader_loc]
        while shader_loc > 0:
            shader_key = filedata[filedata.find(b'.fx#', shader_loc)+4:filedata.find(b'.fx#', shader_loc)+36].decode()
            new_phyre += true_shader_dict[fake_shader_dict[shader_key]]
            end_key = filedata.find(b'\x00', shader_loc + 1)
            shader_loc = filedata.find(b'\x00shader', shader_loc + 1)
        new_phyre += filedata[end_key:]
        return(new_phyre)
    else:
        return False

if __name__ == '__main__':
    # Set current directory
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    if os.path.exists('metadata.json'):
        with open('metadata.json','rb') as f:
            metadata = json.loads(f.read())
        filename = metadata['name'] + '.dae.phyre'
        true_shader_dict = make_true_shader_dict(metadata)
        fake_shader_dict = make_fake_shader_dict()
        
        if os.path.exists(filename):
            shutil.copy2(filename, filename + '.bak')
            with open(filename, 'rb') as f:
                filedata = f.read()
            new_phyre = replace_shader_references(filedata, true_shader_dict, fake_shader_dict)
            with open(filename, 'wb') as f:
                f.write(new_phyre)
        else:
            input("{0} missing, copy to folder with metadata.json, press any key to continue".format(filename))
    else:
        input("metadata.json missing, press any key to continue")
