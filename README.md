# ed8pkg2glb

Converts model data and texture data contained in ED8 `.pkg` files to GLTF binary format.

# Usage

First, download and extract the [Win32 version](https://github.com/uyjulian/ed8pkg2glb/releases/latest/download/ed8pkg2glb-win32.zip).  
Afterwards, drag and drop a single `.pkg` file onto the executable `ed8pkg2glb.exe`.  
`.glb` and `.dds` files will be output in the same directory as `.pkg`.  

# Output file information

The `.glb` file can be imported in [Blender](https://www.blender.org/).  
Compatibility with other applications is not guaranteed due to the output file not completely adhering to the GLTF specification.  
Due to the fact that the game uses shaders for blending multiple UV layers, the output result may not look exactly as in the game.  

The `.dds` file is output in the native block compression format (e.g. DXT1 or BC7)  
At the time of writing, Blender does not support BC7 textures natively, so you will need to convert them with [TexConv](https://github.com/microsoft/DirectXTex/wiki/Texconv).  

# Compatibility

The following games are known to be compatible with this program:  
* 英雄伝説: 閃の軌跡 / Eiyuu Densetsu: Sen no Kiseki / The Legend of Heroes: Trails of Cold Steel (Vita, PS3, PC, PS4)
* 英雄伝説: 閃の軌跡 II / Eiyuu Densetsu: Sen no Kiseki II / The Legend of Heroes: Trails of Cold Steel II (Vita, PS3, PC, PS4)
* 英雄伝説: 閃の軌跡 III / Eiyuu Densetsu: Sen no Kiseki III / The Legend of Heroes: Trails of Cold Steel III (PC, PS4, Switch)
* 英雄伝説: 閃の軌跡 IV / Eiyuu Densetsu: Sen no Kiseki IV / The Legend of Heroes: Trails of Cold Steel IV (PC, PS4, Switch)
* 英雄伝説: 創の軌跡 / Eiyuu Densetsu: Hajimari no Kiseki (PS4)
* 東亰ザナドゥ / Tokyo Xanadu (Vita, PC, PS4)

# Extracting a .pkg file from an outer archive

## PSARC
For PS3 and PSVita, please visit the following page: https://www.psdevwiki.com/ps3/PlayStation_archive_(PSARC)  
For PS4, you will need to use the `orbis-psarc` tool. This utility can be found easily using a search engine.  

## BRA
The following program can be used for this purpose: https://heroesoflegend.org/forums/viewtopic.php?t=356  

## PKA
The following program can be used for this purpose: https://github.com/uyjulian/unpackpka  

# Credits

The PS4, PS3, and Vita image untiling are adapted from here: https://github.com/xdanieldzd/Scarlet/blob/8c56632eb2968e64b6d6fad14af3758e606a127d/Scarlet/Drawing/ImageBinary.cs#L1256  
The PS4 texture information are adapted from here: https://zenhax.com/viewtopic.php?f=7&t=7573  
The LZ4 decompression is adapted from here: https://gist.github.com/weigon/43e217e69418875a55b31b1a5c89662d  
The `nislzss`/LZ77 decompression is adapted from here: https://github.com/Sewer56/Sen-no-Kiseki-PKG-Sharp/blob/3a458e201aa946add705c6ed6aa1dd49dce00223/D/source/decompress.d#L50  
Huge thanks to @PMONickpop123 for assisting with debugging and feature completeness.

# License

The program is licensed under the MIT license. Please check `LICENSE` for more information.
