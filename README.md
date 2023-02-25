# Trails of Cold Steel III / IV / into Reverie Model Toolset

This a tool set for making mods of character models in Trails of Cold Steel III, IV and into Reverie (Hajimari) for PC (DirectX 11).  It is built on top of uyjulian's ed8pkg2glb tool, which is [here](https://github.com/uyjulian/ed8pkg2glb).  I have not removed the functionality of producing gltf files, although those files are not used in the model compilation process.

## Credits:
The original phyre asset decompiler is written by Julian Uy (github.com/uyjulian), and I have only made modifications.  I wrote the remaining tools, and am very thankful to Arc, My Name, uyjulian, TwnKey and the Kiseki modding discord for their brilliant work and for sharing that work so freely.  I am especially thankful to Arc for sharing expertise in the compilation process and for spending many evenings helping me debug!  I am also very thankful to My Name for sharing models and knowledge as well.

## Requirements:
1. Python 3.9 or newer is required for use of this script.  It is free from the Microsoft Store, for Windows users.  For Linux users, please consult your distro.
2. The zstandard module for python is needed for decompiling zstandard-compressed pkgs.  Install by running the included install_zstandard.bat or by typing "python3 -m pip install  zstandard" in the command line / shell.
3. The output can be imported into Blender using DarkStarSword's amazing plugin: https://github.com/DarkStarSword/3d-fixes/blob/master/blender_3dmigoto.py
4. Compilation is dependent on the phyre Engine tools from [here](https://github.com/Trails-Research-Group/Doc/releases/download/v0.0/WorkFolder.zip), as described on the [tutorial from the Trails-Research-Group](https://github.com/Trails-Research-Group/Doc/wiki/How-to:-Import-custom-models-to-Cold-Steel-IV).  (You do not need the tutorial for basic mods, just the tools.)

## Usage:

### Step 1: Decompilation
Obtain a model pkg file.  In CS3/CS4, the files are stored in assets.pka and must be extracted.  Use [extract_pka.py](https://github.com/eArmada8/unpackpka) in the same folder as assets.pka.

Place ed8pkg2gltf.py and lib_fmtibvb.py into a folder with your character model (.pkg) file.  Double-click ed8pkg2gltf.py.  It will create a folder with the same name as the pkg, and dump in there the model in gltf form, meshes for modding in a folder, textures in their own folder, and a metadata.json file.  (Note: Vertex group mapping behavior can be configured, see below.)

Note: If there is more than one .pkg file in the directory, the script will dump them all.

### Step 2: Modding

- Ignore the glTF file.

- There is a folder with the same name as the package, this is the build folder.  The asset_D3D11.xml file and compiled shaders reside here.  For simple mods, nothing here should be changed.

- Textures can be edited in the program of your choice.  If you add files and/or change file names, both the metadata.json and the asset_D3D11.xml should be updated.  To see what texture formats are supported, run ```CSIVAssetImportTool.exe -?```

- Meshes can be modified by importing them into Blender using DarkStarSword's plugin (see above).  Export when finished and overwrite the original files.  Note that meshes with more than 80 active vertex groups will disable GPU skinning (empty groups are okay as the compiler will cull empty groups from skin index of each individual mesh).  To remove a mesh, just delete the files (.fmt/.ib/.vb).  If adding a mesh, be sure it conforms to the existing skeletal map (.vgmap).  (***Note:*** Meshes dumped with this tool have remapped skeletons by default, so existing 3DMigoto meshes cannot be dumped in as-is.  You can either merge into a dumped mesh, or you can run the decompiler with the partial maps option to get meshes with original mapping.  The latter is probably preferred for converting mods since I have confirmed that otherwise you can literally replace the .fmt/.ib/.vb files {keep the .material and .vgmap files} for rapid mod conversion.)

- Material assignments can be changed by changing the .material file associated with the mesh.  Note that the material defines both the textures and the shader.

- New materials can be defined in the metadata (just be careful with commas - you may want to use a dedicated JSON editor).  We cannot make new shaders from scratch, however, so you will need to copy valid metadata (with matching shader hash etc).  To make a new material, copy the *unskinned* section you want from elsewhere (can be from the same character for example, or you can take from a different character) and give it a name that is unique to this model.  Change the textures to what you need (I am pretty sure that the texture *slots* are defined by the shader though - so for example if the shader you pick needs a normal map, you need to provide a normal map).  Update the .material file.  If this is a new shader to this model (i.e. you copied the metadata from a different model), then copy both the *unskinned* and *skinned* shaders to the build directory and update the asset_D3D11.xml with their names.

### Step 3: Building a COLLADA .dae and compiling

For this step, put build_collada.py, lib_fmtibvb.py, replace_shader_references.py and write_pkg.py in the model directory (the directory with metadata.json).  You will also need to have the contents of WorkFolder.zip in your model directory.  (You need CSIVAssetImportTool.exe, all the PhyreAsset_____ files, PhyreDummyShaderCreator.exe, SQLite.Interop.dll and System.Data.SQLite.dll.  You do not need the shaders directory.)

-Double click build_collada.py.  It will make a .dae file, in the chr/chr/{model name}/ folder.  It will also make a shaders/ed8_chr.fx file for compiling, and a RunMe.bat.

-Double click RunMe.bat.  It will run the asset import tool, then it will use the dummy shader creator to identify all the shaders for replacement, then it will use replace_shader_references.py to fix all the shader pointers, and finally it will clean up, move everything to the build directory, and run write_pkg.py to generate your .pkg file.

## Notes

**Command line arguments for ed8pkg2gltf.py:**
`ed8pkg2gltf.py [-h] [-p] [-o] pkg_filename`

`-h, --help`
Shows help message.

`-p, --partialmaps`
The default behavior of the script is to provide meshes and .vgmap files with the entire skeleton and every bone available to each mesh.  This will result in many empty vertex groups upon import into Blender.  (All empty groups will be removed at the time of compilation.)  This option will preserve the original mapping with the exact original indexing (such that the .vgmaps would correspond to and be compatible with buffers taken out of GPU memory, e.g. when using 3DMigoto).

`-o, --overwrite`
Overwrite existing files without prompting.

**Complete VGMap Setting:**

While most modders prefer that complete VGmaps is the default, you may want partial maps to be the default (for example to use existing 3dmigoto mods as a base).  You can (permanently) change the default behavior by editing the python script itself.  There is a line at the top:
`partial_vgmaps_default = False`
which you can change to 
`partial_vgmaps_default = True`
This will also change the command line argument `-p, --partialmaps` into `-c, --completemaps` which you would call to enable complete group vgmaps instead.

Everything below this line is from uyjulian's original README:

### Credits

The PS4, PS3, and Vita image untiling are adapted from here: https://github.com/xdanieldzd/Scarlet/blob/8c56632eb2968e64b6d6fad14af3758e606a127d/Scarlet/Drawing/ImageBinary.cs#L1256  
The PS4 texture information are adapted from here: https://zenhax.com/viewtopic.php?f=7&t=7573  
The LZ4 decompression is adapted from here: https://gist.github.com/weigon/43e217e69418875a55b31b1a5c89662d  
The `nislzss`/LZ77 decompression is adapted from here: https://github.com/Sewer56/Sen-no-Kiseki-PKG-Sharp/blob/3a458e201aa946add705c6ed6aa1dd49dce00223/D/source/decompress.d#L50  
Huge thanks to @PMONickpop123 for assisting with debugging and feature completeness.

### License

The program is licensed under the MIT license. Please check `LICENSE` for more information.
