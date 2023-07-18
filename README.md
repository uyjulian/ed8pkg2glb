# ed8pkg2glb

Converts model data and texture data contained in ED8 `.pkg` files to GLTF binary format and/or PNG binary format.  

## Modding help and resources

See [Trails Research Group](https://github.com/Trails-Research-Group) for more resources to assist in modding the game.  

## Usage

First, download and extract the [Win32 version](https://github.com/uyjulian/ed8pkg2glb/releases/latest/download/ed8pkg2glb-win32.zip).  
Afterwards, drag and drop a **single** `.pkg` file onto the executable `ed8pkg2glb.exe`.  
`.glb` or `.png` files will be output in the same directory as `.pkg`.  

## Output file information

The `.glb` file can be imported in [Blender](https://www.blender.org/).  
Compatibility with other applications is not guaranteed due to the output file not completely adhering to the GLTF specification.  
Due to the fact that the game uses shaders for manipulating the pixel output, the output result may not look exactly as in the game.  

The `.png` file is always output in compressed RGBA format. It is loadable in [Blender](https://www.blender.org/) without any conversion needed.  

## Compatibility

The following games are known to be compatible with this program:  
* 英雄伝説: 閃の軌跡 / Eiyuu Densetsu: Sen no Kiseki / The Legend of Heroes: Trails of Cold Steel (Vita, PS3, PC, PS4)
* 英雄伝説: 閃の軌跡 II / Eiyuu Densetsu: Sen no Kiseki II / The Legend of Heroes: Trails of Cold Steel II (Vita, PS3, PC, PS4)
* 英雄伝説: 閃の軌跡 III / Eiyuu Densetsu: Sen no Kiseki III / The Legend of Heroes: Trails of Cold Steel III (PC, PS4, Switch)
* 英雄伝説: 閃の軌跡 IV / Eiyuu Densetsu: Sen no Kiseki IV / The Legend of Heroes: Trails of Cold Steel IV (PC, PS4, Switch)
* 英雄伝説: 創の軌跡 / Eiyuu Densetsu: Hajimari no Kiseki (PC, PS4)
* 東亰ザナドゥ / Tokyo Xanadu (Vita, PC, PS4)

## Extracting a .pkg file from an outer archive

### PSARC (PS3/PSVita/PS4)
For PS3 and PSVita, please visit the following page: https://www.psdevwiki.com/ps3/PlayStation_archive_(PSARC)  
For PS4, you will need to use the `orbis-psarc` tool. This utility can be found easily using a search engine.  

### BRA (PC)
The following program can be used for this purpose: https://heroesoflegend.org/forums/viewtopic.php?t=356  

### PKA (PC/Switch)
The following program can be used for this purpose: https://github.com/uyjulian/unpackpka  

### NSP/XCI/ROMFS (Switch)
The following program can be used for this purpose: https://github.com/SciresM/hactool  

### PKG (PS3)
Use RPCS3 to install the game, then look in `dev_hdd0/game/` for the decrypted contents.  

### PKG (PSVita)
The following programs can be used:  
Unpacking the `.pkg` file: https://github.com/mmozeiko/pkg2zip  
Decrypting the unpacked contents: https://github.com/motoharu-gosuto/psvpfstools  

### PKG (PS4)
You will need to use the `orbis-pub-cmd` tool. This utility can be found easily using a search engine.  

## Credits

The PS4, PS3, and Vita image untiling are adapted from here: https://github.com/xdanieldzd/Scarlet/blob/8c56632eb2968e64b6d6fad14af3758e606a127d/Scarlet/Drawing/ImageBinary.cs#L1256  
The PS4 texture information are adapted from here: https://zenhax.com/viewtopic.php?f=7&t=7573  
The LZ4 decompression is adapted from here: https://gist.github.com/weigon/43e217e69418875a55b31b1a5c89662d  
The `nislzss`/LZ77 decompression is adapted from here: https://github.com/Sewer56/Sen-no-Kiseki-PKG-Sharp/blob/3a458e201aa946add705c6ed6aa1dd49dce00223/D/source/decompress.d#L50  
The DXT1/DXT3/DXT5/BC5/BC7 decompression is adapted from here: https://github.com/python-pillow/Pillow/blob/78d258f24d1b6a605754af9f8ac57b665543e8b9/src/libImaging/BcnDecode.c  
This project uses the `python-zstandard` library: https://github.com/indygreg/python-zstandard  
Huge thanks to PMONickpop123 for assisting with debugging and feature completeness. He has created many [VRChat worlds](https://vrchat.com/home/user/usr_f261268d-87ad-4281-94c0-33cb5085195b) using a tool based on ed8pkg2glb.  

## License

The program is licensed under the MIT license. Please check `LICENSE` for more information.
