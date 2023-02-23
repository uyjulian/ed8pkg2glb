# ED8 .dae.phyre shader fixer, needs output from my fork of uyjulian/ed8pkg2glb.
# After running build_collada.py, then CSIVAssetImportTool.exe, copy the compiled
# .dae.phyre file into the directory with metadata.json and run this script to
# replace the shader references to the true shaders.
#
# GitHub eArmada8/ed8pkg2gltf

import os, json, shutil

if __name__ == '__main__':
    # Set current directory
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    if os.path.exists('metadata.json'):
        with open('metadata.json','rb') as f:
            metadata = json.loads(f.read())
        true_shaders = [x['m_effectVariant']['m_id'] for x in metadata['materials']]
        true_shaders_dict = {x[-32:-25]:b'\x00'+x.encode() for x in true_shaders}
        filename = metadata['name'] + '.dae.phyre'
        if os.path.exists(filename):
            shutil.copy2(filename, filename + '.bak')
            with open(filename, 'rb') as f:
                filedata = f.read()
            if filedata[0:4] == b'RYHP':
                shader_loc = filedata.find(b'\x00shader', 1)
                new_phyre = filedata[0:shader_loc]
                while shader_loc > 0:
                    shader_key = filedata.find(b'.fx#', shader_loc) - 7 
                    true_shader = filedata[shader_key:shader_key+7].decode()
                    new_phyre += true_shaders_dict[true_shader]
                    end_key = filedata.find(b'\x00', shader_loc + 1)
                    shader_loc = filedata.find(b'\x00shader', shader_loc + 1)
                new_phyre += filedata[end_key:]
            with open(filename, 'wb') as f:
                f.write(new_phyre)
        else:
            input("{0} missing, copy to folder with metadata.json, press any key to continue".format(filename))
    else:
        input("metadata.json missing, press any key to continue")
