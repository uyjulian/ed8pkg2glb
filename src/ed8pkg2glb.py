import os
import gc
import sys
import io
import struct
import array
try:
    import zstandard
except:
    pass

def read_null_ending_string(f):
    import itertools
    import functools
    toeof = iter(functools.partial(f.read, 1), b'')
    return sys.intern(b''.join(itertools.takewhile(b'\x00'.__ne__, toeof)).decode('ASCII'))

def bytearray_byteswap(p, itemsize):
    if itemsize == 1:
        pass
    elif itemsize == 2:
        for i in range(0, len(p), itemsize):
            p0 = p[i + 0]
            p[i + 0] = p[i + 1]
            p[i + 1] = p0
    elif itemsize == 4:
        for i in range(0, len(p), itemsize):
            p0 = p[i + 0]
            p1 = p[i + 1]
            p[i + 0] = p[i + 3]
            p[i + 1] = p[i + 2]
            p[i + 2] = p1
            p[i + 3] = p0
    elif itemsize == 8:
        for i in range(0, len(p), itemsize):
            p0 = p[i + 0]
            p1 = p[i + 1]
            p2 = p[i + 2]
            p3 = p[i + 3]
            p[i + 0] = p[i + 7]
            p[i + 1] = p[i + 6]
            p[i + 2] = p[i + 5]
            p[i + 3] = p[i + 4]
            p[i + 4] = p3
            p[i + 5] = p2
            p[i + 6] = p1
            p[i + 7] = p0
    else:
        raise Exception("don't know how to byteswap this array type")

def cast_memoryview(mv, t):
    return mv.cast(t)

def read_integer(f, size, unsigned, endian='<'):
    typemap = {1: 'b', 2: 'h', 4: 'i', 8: 'q'}
    inttype = typemap[size]
    if unsigned == True:
        inttype = inttype.upper()
    ba = bytearray(f.read(size))
    if endian == '>':
        bytearray_byteswap(ba, size)
    return cast_memoryview(memoryview(ba), inttype)[0]

def imageUntilePS4(buffer, width, height, bpb, pitch=0):
    Tile = (0, 1, 8, 9, 2, 3, 10, 11, 16, 17, 24, 25, 18, 19, 26, 27, 4, 5, 12, 13, 6, 7, 14, 15, 20, 21, 28, 29, 22, 23, 30, 31, 32, 33, 40, 41, 34, 35, 42, 43, 48, 49, 56, 57, 50, 51, 58, 59, 36, 37, 44, 45, 38, 39, 46, 47, 52, 53, 60, 61, 54, 55, 62, 63)
    tileWidth = 8
    tileHeight = 8
    out = bytearray(len(buffer))
    usingPitch = False
    if pitch > 0 and pitch != width:
        width_bak = width
        width = pitch
        usingPitch = True
    if width % tileWidth or height % tileHeight:
        width_show = width
        height_show = height
        width = width_real = (width + (tileWidth - 1)) // tileWidth * tileWidth
        height = height_real = (height + (tileHeight - 1)) // tileHeight * tileHeight
    else:
        width_show = width_real = width
        height_show = height_real = height
    for InY in range(height):
        for InX in range(width):
            Z = InY * width + InX
            globalX = Z // (tileWidth * tileHeight) * tileWidth
            globalY = globalX // width * tileHeight
            globalX %= width
            inTileX = Z % tileWidth
            inTileY = Z // tileWidth % tileHeight
            inTile = inTileY * tileHeight + inTileX
            inTile = Tile[inTile]
            inTileX = inTile % tileWidth
            inTileY = inTile // tileHeight
            OutX = globalX + inTileX
            OutY = globalY + inTileY
            OffsetIn = InX * bpb + InY * bpb * width
            OffsetOut = OutX * bpb + OutY * bpb * width
            out[OffsetOut:OffsetOut + bpb] = buffer[OffsetIn:OffsetIn + bpb]
    if usingPitch:
        width_show = width_bak
    if width_show != width_real or height_show != height_real:
        crop = bytearray(width_show * height_show * bpb)
        for Y in range(height_show):
            OffsetIn = Y * width_real * bpb
            OffsetOut = Y * width_show * bpb
            crop[OffsetOut:OffsetOut + width_show * bpb] = out[OffsetIn:OffsetIn + width_show * bpb]
        out = crop
    return out

def imageUntileMorton(buffer, width, height, bpb, pitch=0):
    Tile = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63)
    tileWidth = 8
    tileHeight = 8
    out = bytearray(len(buffer))
    usingPitch = False
    if pitch > 0 and pitch != width:
        width_bak = width
        width = pitch
        usingPitch = True
    if width % tileWidth or height % tileHeight:
        width_show = width
        height_show = height
        width = width_real = (width + (tileWidth - 1)) // tileWidth * tileWidth
        height = height_real = (height + (tileHeight - 1)) // tileHeight * tileHeight
    else:
        width_show = width_real = width
        height_show = height_real = height
    for InY in range(height):
        for InX in range(width):
            Z = InY * width + InX
            globalX = Z // (tileWidth * tileHeight) * tileWidth
            globalY = globalX // width * tileHeight
            globalX %= width
            inTileX = Z % tileWidth
            inTileY = Z // tileWidth % tileHeight
            inTile = inTileY * tileHeight + inTileX
            inTile = Tile[inTile]
            inTileX = inTile % tileWidth
            inTileY = inTile // tileHeight
            OutX = globalX + inTileX
            OutY = globalY + inTileY
            OffsetIn = InX * bpb + InY * bpb * width
            OffsetOut = OutX * bpb + OutY * bpb * width
            out[OffsetOut:OffsetOut + bpb] = buffer[OffsetIn:OffsetIn + bpb]
    if usingPitch:
        width_show = width_bak
    if width_show != width_real or height_show != height_real:
        crop = bytearray(width_show * height_show * bpb)
        for Y in range(height_show):
            OffsetIn = Y * width_real * bpb
            OffsetOut = Y * width_show * bpb
            crop[OffsetOut:OffsetOut + width_show * bpb] = out[OffsetIn:OffsetIn + width_show * bpb]
        out = crop
    return out

def Compact1By1(x):
    x &= 1431655765
    x = (x ^ x >> 1) & 858993459
    x = (x ^ x >> 2) & 252645135
    x = (x ^ x >> 4) & 16711935
    x = (x ^ x >> 8) & 65535
    return x

def DecodeMorton2X(code):
    return Compact1By1(code >> 0)

def DecodeMorton2Y(code):
    return Compact1By1(code >> 1)

def imageUntileVita(buffer, width, height, bpb, pitch=0):
    import math
    tileWidth = 8
    tileHeight = 8
    out = bytearray(len(buffer))
    usingPitch = False
    if pitch > 0 and pitch != width:
        width_bak = width
        width = pitch
        usingPitch = True
    if width % tileWidth or height % tileHeight:
        width_show = width
        height_show = height
        width = width_real = (width + (tileWidth - 1)) // tileWidth * tileWidth
        height = height_real = (height + (tileHeight - 1)) // tileHeight * tileHeight
    else:
        width_show = width_real = width
        height_show = height_real = height
    for InY in range(height):
        for InX in range(width):
            Z = InY * width + InX
            mmin = width if width < height else height
            k = int(math.log(mmin, 2))
            if height < width:
                j = Z >> 2 * k << 2 * k | (DecodeMorton2Y(Z) & mmin - 1) << k | (DecodeMorton2X(Z) & mmin - 1) << 0
                OutX = j // height
                OutY = j % height
            else:
                j = Z >> 2 * k << 2 * k | (DecodeMorton2X(Z) & mmin - 1) << k | (DecodeMorton2Y(Z) & mmin - 1) << 0
                OutX = j % width
                OutY = j // width
            OffsetIn = InX * bpb + InY * bpb * width
            OffsetOut = OutX * bpb + OutY * bpb * width
            out[OffsetOut:OffsetOut + bpb] = buffer[OffsetIn:OffsetIn + bpb]
    if usingPitch:
        width_show = width_bak
    if width_show != width_real or height_show != height_real:
        crop = bytearray(width_show * height_show * bpb)
        for Y in range(height_show):
            OffsetIn = Y * width_real * bpb
            OffsetOut = Y * width_show * bpb
            crop[OffsetOut:OffsetOut + width_show * bpb] = out[OffsetIn:OffsetIn + width_show * bpb]
        out = crop
    return out

def Unswizzle(data, width, height, imgFmt, cb, pitch=0):
    TexParams = (('DXT1', 1, 8), ('DXT3', 1, 16), ('DXT5', 1, 16), ('BC5', 1, 16), ('BC7', 1, 16), ('RGBA8', 0, 4), ('ARGB8', 0, 4), ('L8', 0, 1), ('A8', 0, 1), ('LA88', 0, 2), ('RGBA16F', 0, 8), ('ARGB1555', 0, 2), ('ARGB4444', 0, 2), ('RGB565', 0, 2), ('ARGB8_SRGB', 0, 4))
    TexParams = tuple((tuple((TexParams[j][i] for j in range(len(TexParams)))) for i in range(len(TexParams[0]))))
    IsBlockCompressed = TexParams[1][TexParams[0].index(imgFmt)]
    BytesPerBlock = TexParams[2][TexParams[0].index(imgFmt)]
    if IsBlockCompressed:
        width >>= 2
        height >>= 2
        pitch >>= 2
    if imgFmt == 'DXT5' and cb == imageUntileVita:
        BytesPerBlock = 8
    data = cb(data, width, height, BytesPerBlock, pitch)
    return data

def GetInfo(val, sh1, sh2):
    val &= 4294967295
    val <<= 31 - sh1
    val &= 4294967295
    val >>= 31 - sh1 + sh2
    val &= 4294967295
    return val

def decode_bc7_block(src):

    def get_bits(src, bit, count):
        v = 0
        x = 0
        by = bit >> 3
        bit &= 7
        if count == 0:
            return 0
        if bit + count <= 8:
            v = src[by] >> bit & (1 << count) - 1
        else:
            x = src[by] | src[by + 1] << 8
            v = x >> bit & (1 << count) - 1
        return v & 255
    bc7_modes = [[3, 4, 0, 0, 4, 0, 1, 0, 3, 0], [2, 6, 0, 0, 6, 0, 0, 1, 3, 0], [3, 6, 0, 0, 5, 0, 0, 0, 2, 0], [2, 6, 0, 0, 7, 0, 1, 0, 2, 0], [1, 0, 2, 1, 5, 6, 0, 0, 2, 3], [1, 0, 2, 0, 7, 8, 0, 0, 2, 2], [1, 0, 0, 0, 7, 7, 1, 0, 4, 0], [2, 6, 0, 0, 5, 5, 1, 0, 2, 0]]

    def bc7_mode_to_dict(mode_arr):
        return {'ns': mode_arr[0], 'pb': mode_arr[1], 'rb': mode_arr[2], 'isb': mode_arr[3], 'cb': mode_arr[4], 'ab': mode_arr[5], 'epb': mode_arr[6], 'spb': mode_arr[7], 'ib': mode_arr[8], 'ib2': mode_arr[9]}
    bc7_modes[:] = [bc7_mode_to_dict(mode) for mode in bc7_modes]
    bc7_si2 = [52428, 34952, 61166, 60616, 51328, 65260, 65224, 60544, 51200, 65516, 65152, 59392, 65512, 65280, 65520, 61440, 63248, 142, 28928, 2254, 140, 29456, 12544, 36046, 2188, 12560, 26214, 13932, 6120, 4080, 29070, 14748, 43690, 61680, 23130, 13260, 15420, 21930, 38550, 42330, 29646, 5064, 12876, 15324, 27030, 49980, 39270, 1632, 626, 1252, 20032, 10016, 51510, 37740, 14790, 25500, 37686, 40134, 33150, 59160, 52464, 4044, 30532, 60962]
    bc7_si3 = [2858963024, 1784303680, 1515864576, 1414570152, 2779054080, 2694860880, 1431675040, 1515868240, 2857697280, 2857719040, 2863289600, 2425393296, 2492765332, 2762253476, 2846200912, 705315408, 2777960512, 172118100, 2779096320, 1436590240, 2829603924, 1785348160, 2762231808, 437912832, 5285028, 2862977168, 342452500, 1768494080, 2693105056, 2860651540, 1352967248, 1784283648, 2846195712, 1351655592, 2829094992, 606348324, 11162880, 613566756, 608801316, 1352993360, 1342874960, 2863285316, 1717960704, 2778768800, 1352683680, 1764256040, 1152035396, 1717986816, 2856600644, 1420317864, 2508232064, 2526451200, 2824098984, 2157286784, 2853442580, 2526412800, 2863272980, 2689618080, 2695210400, 2516582400, 1082146944, 2846402984, 2863311428, 709513812]
    bc7_ai0 = [15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 2, 8, 2, 2, 8, 8, 15, 2, 8, 2, 2, 8, 8, 2, 2, 15, 15, 6, 8, 2, 8, 15, 15, 2, 8, 2, 2, 2, 15, 15, 6, 6, 2, 6, 8, 15, 15, 2, 2, 15, 15, 15, 15, 15, 2, 2, 15]
    bc7_ai1 = [3, 3, 15, 15, 8, 3, 15, 15, 8, 8, 6, 6, 6, 5, 3, 3, 3, 3, 8, 15, 3, 3, 6, 10, 5, 8, 8, 6, 8, 5, 15, 15, 8, 15, 3, 5, 6, 10, 8, 15, 15, 3, 15, 5, 15, 15, 15, 15, 3, 15, 5, 5, 5, 8, 5, 10, 5, 10, 8, 13, 15, 12, 3, 3]
    bc7_ai2 = [15, 8, 8, 3, 15, 15, 3, 8, 15, 15, 15, 15, 15, 15, 15, 8, 15, 8, 15, 3, 15, 8, 15, 8, 3, 15, 6, 10, 15, 15, 10, 8, 15, 3, 15, 10, 10, 8, 9, 10, 6, 15, 8, 15, 3, 6, 6, 8, 15, 3, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 3, 15, 15, 8]
    bc7_weights2 = [0, 21, 43, 64]
    bc7_weights3 = [0, 9, 18, 27, 37, 46, 55, 64]
    bc7_weights4 = [0, 4, 9, 13, 17, 21, 26, 30, 34, 38, 43, 47, 51, 55, 60, 64]

    def bc7_get_weights(n):
        if n == 2:
            return bc7_weights2
        if n == 3:
            return bc7_weights3
        return bc7_weights4

    def bc7_get_subset(ns, partition, n):
        if ns == 2:
            return 1 & bc7_si2[partition] >> n
        if ns == 3:
            return 3 & bc7_si3[partition] >> 2 * n
        return 0

    def expand_quantized(v, bits):
        v = v << 8 - bits
        return (v | v >> bits) & 255

    def bc7_lerp(dst, dst_offset, e, e_offset, s0, s1):
        t0 = 64 - s0
        t1 = 64 - s1
        dst_write_offset = dst_offset * 4
        e_read_offset_0 = (e_offset + 0) * 4
        e_read_offset_1 = (e_offset + 1) * 4
        dst[dst_write_offset + 0] = t0 * e[e_read_offset_0 + 0] + s0 * e[e_read_offset_1 + 0] + 32 >> 6 & 255
        dst[dst_write_offset + 1] = t0 * e[e_read_offset_0 + 1] + s0 * e[e_read_offset_1 + 1] + 32 >> 6 & 255
        dst[dst_write_offset + 2] = t0 * e[e_read_offset_0 + 2] + s0 * e[e_read_offset_1 + 2] + 32 >> 6 & 255
        dst[dst_write_offset + 3] = t1 * e[e_read_offset_0 + 3] + s1 * e[e_read_offset_1 + 3] + 32 >> 6 & 255
    col = bytearray(4 * 4 * 4)
    endpoints = bytearray(6 * 4)
    bit = 0
    mode = src[0]
    if mode == 0:
        for i in range(16):
            col[i * 4 + 0] = 0
            col[i * 4 + 1] = 0
            col[i * 4 + 2] = 0
            col[i * 4 + 3] = 255
        return col
    while True:
        cond = mode & 1 << bit != 0
        bit += 1
        if cond:
            break
    mode = bit - 1
    info = bc7_modes[mode]
    cb = info['cb']
    ab = info['ab']
    cw = bc7_get_weights(info['ib'])
    aw = bc7_get_weights(info['ib2'] if ab != 0 and info['ib2'] != 0 else info['ib'])
    partition = get_bits(src, bit, info['pb'])
    bit += info['pb']
    rotation = get_bits(src, bit, info['rb'])
    bit += info['rb']
    index_sel = get_bits(src, bit, info['isb'])
    bit += info['isb']
    numep = info['ns'] << 1
    for i in range(numep):
        val = get_bits(src, bit, cb)
        bit += cb
        endpoints[i * 4 + 0] = val
    for i in range(numep):
        val = get_bits(src, bit, cb)
        bit += cb
        endpoints[i * 4 + 1] = val
    for i in range(numep):
        val = get_bits(src, bit, cb)
        bit += cb
        endpoints[i * 4 + 2] = val
    for i in range(numep):
        val = 255
        if ab != 0:
            val = get_bits(src, bit, ab)
            bit += ab
        endpoints[i * 4 + 3] = val
    if info['epb'] != 0:
        cb += 1
        if ab != 0:
            ab += 1
        for i in range(numep):
            endpoint_write_offset = i * 4
            val = get_bits(src, bit, 1)
            bit += 1
            endpoints[endpoint_write_offset + 0] = endpoints[endpoint_write_offset + 0] << 1 | val
            endpoints[endpoint_write_offset + 1] = endpoints[endpoint_write_offset + 1] << 1 | val
            endpoints[endpoint_write_offset + 2] = endpoints[endpoint_write_offset + 2] << 1 | val
            if ab != 0:
                endpoints[endpoint_write_offset + 3] = endpoints[endpoint_write_offset + 3] << 1 | val
    if info['spb'] != 0:
        cb += 1
        if ab != 0:
            ab += 1
        for i in range(0, numep, 2):
            val = get_bits(src, bit, 1)
            bit += 1
            for j in range(2):
                endpoint_write_offset = (i + j) * 4
                endpoints[endpoint_write_offset + 0] = endpoints[endpoint_write_offset + 0] << 1 | val
                endpoints[endpoint_write_offset + 1] = endpoints[endpoint_write_offset + 1] << 1 | val
                endpoints[endpoint_write_offset + 2] = endpoints[endpoint_write_offset + 2] << 1 | val
                if ab != 0:
                    endpoints[endpoint_write_offset + 3] = endpoints[endpoint_write_offset + 3] << 1 | val
    for i in range(numep):
        endpoint_write_offset = i * 4
        endpoints[endpoint_write_offset + 0] = expand_quantized(endpoints[endpoint_write_offset + 0], cb)
        endpoints[endpoint_write_offset + 1] = expand_quantized(endpoints[endpoint_write_offset + 1], cb)
        endpoints[endpoint_write_offset + 2] = expand_quantized(endpoints[endpoint_write_offset + 2], cb)
        if ab != 0:
            endpoints[endpoint_write_offset + 3] = expand_quantized(endpoints[endpoint_write_offset + 3], ab)
    cibit = bit
    aibit = cibit + 16 * info['ib'] - info['ns']
    for i in range(16):
        s = bc7_get_subset(info['ns'], partition, i) << 1
        ib = info['ib']
        if i == 0:
            ib -= 1
        elif info['ns'] == 2:
            if i == bc7_ai0[partition]:
                ib -= 1
        elif info['ns'] == 3:
            if i == bc7_ai1[partition]:
                ib -= 1
            elif i == bc7_ai2[partition]:
                ib -= 1
        i0 = get_bits(src, cibit, ib)
        cibit += ib
        if ab != 0 and info['ib2'] != 0:
            ib2 = info['ib2']
            if ib2 != 0 and i == 0:
                ib2 -= 1
            i1 = get_bits(src, aibit, ib2)
            aibit += ib2
            if index_sel != 0:
                bc7_lerp(col, i, endpoints, s, aw[i1], cw[i0])
            else:
                bc7_lerp(col, i, endpoints, s, cw[i0], aw[i1])
        else:
            bc7_lerp(col, i, endpoints, s, cw[i0], cw[i0])
        if rotation == 1:
            val = col[i * 4 + 0]
            col[i * 4 + 0] = col[i * 4 + 3]
            col[i * 4 + 3] = val
        elif rotation == 2:
            val = col[i * 4 + 1]
            col[i * 4 + 1] = col[i * 4 + 3]
            col[i * 4 + 3] = val
        elif rotation == 3:
            val = col[i * 4 + 2]
            col[i * 4 + 2] = col[i * 4 + 3]
            col[i * 4 + 3] = val
    return col

def decode_bc5(data):

    def decode_bc3_alpha(dst, dst_offset, src, src_offset, stride, o, sign):
        a0 = 0
        a1 = 0
        a = bytearray(8)
        lut1 = 0
        lut2 = 0
        if sign == 1:
            raise Exception('Signed bc5 not implemented!')
        else:
            a0 = src[src_offset + 0]
            a1 = src[src_offset + 1]
        src_lut_offset = src_offset + 2
        lut1 = src[src_lut_offset + 0] | src[src_lut_offset + 1] << 8 | src[src_lut_offset + 2] << 16
        lut2 = src[src_lut_offset + 3] | src[src_lut_offset + 4] << 8 | src[src_lut_offset + 5] << 16
        a[0] = a0 & 255
        a[1] = a1 & 255
        if a0 > a1:
            a[2] = (6 * a0 + 1 * a1) // 7
            a[3] = (5 * a0 + 2 * a1) // 7
            a[4] = (4 * a0 + 3 * a1) // 7
            a[5] = (3 * a0 + 4 * a1) // 7
            a[6] = (2 * a0 + 5 * a1) // 7
            a[7] = (1 * a0 + 6 * a1) // 7
        else:
            a[2] = (4 * a0 + 1 * a1) // 5
            a[3] = (3 * a0 + 2 * a1) // 5
            a[4] = (2 * a0 + 3 * a1) // 5
            a[5] = (1 * a0 + 4 * a1) // 5
            a[6] = 0
            a[7] = 255
        for n in range(8):
            aw = 7 & lut1 >> 3 * n
            dst[dst_offset + (stride * n + o)] = a[aw]
        for n in range(8):
            aw = 7 & lut2 >> 3 * n
            dst[dst_offset + (stride * (8 + n) + o)] = a[aw]
    finalColor = bytearray(4 * 4 * 4)
    block = data[:16]
    decode_bc3_alpha(finalColor, 0, block, 0, 4, 0, 0)
    decode_bc3_alpha(finalColor, 0, block, 8, 4, 1, 0)
    return finalColor
import struct

def decode_dxt1(data):
    finalColor = bytearray(4 * 4 * 4)
    color0, color1, bits = struct.unpack('<HHI', data[:8])
    r0 = (color0 >> 11 & 31) << 3
    g0 = (color0 >> 5 & 63) << 2
    b0 = (color0 & 31) << 3
    r1 = (color1 >> 11 & 31) << 3
    g1 = (color1 >> 5 & 63) << 2
    b1 = (color1 & 31) << 3
    for j in range(4):
        j_offset = j * 4 * 4
        for i in range(4):
            i_offset = i * 4
            control = bits & 3
            bits = bits >> 2
            if control == 0:
                finalColor[j_offset + i_offset + 0] = r0
                finalColor[j_offset + i_offset + 1] = g0
                finalColor[j_offset + i_offset + 2] = b0
                finalColor[j_offset + i_offset + 3] = 255
            elif control == 1:
                finalColor[j_offset + i_offset + 0] = r1
                finalColor[j_offset + i_offset + 1] = g1
                finalColor[j_offset + i_offset + 2] = b1
                finalColor[j_offset + i_offset + 3] = 255
            elif control == 2:
                if color0 > color1:
                    finalColor[j_offset + i_offset + 0] = (2 * r0 + r1) // 3
                    finalColor[j_offset + i_offset + 1] = (2 * g0 + g1) // 3
                    finalColor[j_offset + i_offset + 2] = (2 * b0 + b1) // 3
                    finalColor[j_offset + i_offset + 3] = 255
                else:
                    finalColor[j_offset + i_offset + 0] = (r0 + r1) // 2
                    finalColor[j_offset + i_offset + 1] = (g0 + g1) // 2
                    finalColor[j_offset + i_offset + 2] = (b0 + b1) // 2
                    finalColor[j_offset + i_offset + 3] = 255
            elif control == 3:
                if color0 > color1:
                    finalColor[j_offset + i_offset + 0] = (2 * r1 + r0) // 3
                    finalColor[j_offset + i_offset + 1] = (2 * g1 + g0) // 3
                    finalColor[j_offset + i_offset + 2] = (2 * b1 + b0) // 3
                    finalColor[j_offset + i_offset + 3] = 255
                else:
                    finalColor[j_offset + i_offset + 0] = 0
                    finalColor[j_offset + i_offset + 1] = 0
                    finalColor[j_offset + i_offset + 2] = 0
                    finalColor[j_offset + i_offset + 3] = 0
    return bytes(finalColor)

def decode_dxt3(data):
    finalColor = bytearray(4 * 4 * 4)
    block = data[:16]
    bits = struct.unpack(b'<8B', block[:8])
    color0, color1 = struct.unpack(b'<HH', block[8:12])
    code, = struct.unpack(b'<I', block[12:])
    r0 = (color0 >> 11 & 31) << 3
    g0 = (color0 >> 5 & 63) << 2
    b0 = (color0 & 31) << 3
    r1 = (color1 >> 11 & 31) << 3
    g1 = (color1 >> 5 & 63) << 2
    b1 = (color1 & 31) << 3
    for j in range(4):
        j_offset = j * 4 * 4
        high = False
        for i in range(4):
            i_offset = i * 4
            if high:
                high = False
            else:
                high = True
            alphaCodeIndex = (4 * j + i) // 2
            finalAlpha = bits[alphaCodeIndex]
            if high:
                finalAlpha &= 15
            else:
                finalAlpha >>= 4
            finalAlpha *= 17
            colorCode = code >> 2 * (4 * j + i) & 3
            if colorCode == 0:
                finalColor[j_offset + i_offset + 0] = r0
                finalColor[j_offset + i_offset + 1] = g0
                finalColor[j_offset + i_offset + 2] = b0
            elif colorCode == 1:
                finalColor[j_offset + i_offset + 0] = r1
                finalColor[j_offset + i_offset + 1] = g1
                finalColor[j_offset + i_offset + 2] = b1
            elif colorCode == 2:
                finalColor[j_offset + i_offset + 0] = (2 * r0 + r1) // 3
                finalColor[j_offset + i_offset + 1] = (2 * g0 + g1) // 3
                finalColor[j_offset + i_offset + 2] = (2 * b0 + b1) // 3
            elif colorCode == 3:
                finalColor[j_offset + i_offset + 0] = (r0 + 2 * r1) // 3
                finalColor[j_offset + i_offset + 1] = (g0 + 2 * g1) // 3
                finalColor[j_offset + i_offset + 2] = (b0 + 2 * b1) // 3
            finalColor[j_offset + i_offset + 3] = finalAlpha
    return bytes(finalColor)

def decode_dxt5(data):
    finalColor = bytearray(4 * 4 * 4)
    block = data[:16]
    alpha0, alpha1 = struct.unpack(b'<BB', block[:2])
    bits = struct.unpack(b'<6B', block[2:8])
    alphaCode1 = bits[2] | bits[3] << 8 | bits[4] << 16 | bits[5] << 24
    alphaCode2 = bits[0] | bits[1] << 8
    color0, color1 = struct.unpack(b'<HH', block[8:12])
    code, = struct.unpack(b'<I', block[12:])
    r0 = (color0 >> 11 & 31) << 3
    g0 = (color0 >> 5 & 63) << 2
    b0 = (color0 & 31) << 3
    r1 = (color1 >> 11 & 31) << 3
    g1 = (color1 >> 5 & 63) << 2
    b1 = (color1 & 31) << 3
    for j in range(4):
        j_offset = j * 4 * 4
        for i in range(4):
            i_offset = i * 4
            alphaCodeIndex = 3 * (4 * j + i)
            if alphaCodeIndex <= 12:
                alphaCode = alphaCode2 >> alphaCodeIndex & 7
            elif alphaCodeIndex == 15:
                alphaCode = alphaCode2 >> 15 | alphaCode1 << 1 & 6
            else:
                alphaCode = alphaCode1 >> alphaCodeIndex - 16 & 7
            if alphaCode == 0:
                finalAlpha = alpha0
            elif alphaCode == 1:
                finalAlpha = alpha1
            elif alpha0 > alpha1:
                finalAlpha = ((8 - alphaCode) * alpha0 + (alphaCode - 1) * alpha1) // 7
            elif alphaCode == 6:
                finalAlpha = 0
            elif alphaCode == 7:
                finalAlpha = 255
            else:
                finalAlpha = ((6 - alphaCode) * alpha0 + (alphaCode - 1) * alpha1) // 5
            colorCode = code >> 2 * (4 * j + i) & 3
            if colorCode == 0:
                finalColor[j_offset + i_offset + 0] = r0
                finalColor[j_offset + i_offset + 1] = g0
                finalColor[j_offset + i_offset + 2] = b0
            elif colorCode == 1:
                finalColor[j_offset + i_offset + 0] = r1
                finalColor[j_offset + i_offset + 1] = g1
                finalColor[j_offset + i_offset + 2] = b1
            elif colorCode == 2:
                finalColor[j_offset + i_offset + 0] = (2 * r0 + r1) // 3
                finalColor[j_offset + i_offset + 1] = (2 * g0 + g1) // 3
                finalColor[j_offset + i_offset + 2] = (2 * b0 + b1) // 3
            elif colorCode == 3:
                finalColor[j_offset + i_offset + 0] = (r0 + 2 * r1) // 3
                finalColor[j_offset + i_offset + 1] = (g0 + 2 * g1) // 3
                finalColor[j_offset + i_offset + 2] = (b0 + 2 * b1) // 3
            finalColor[j_offset + i_offset + 3] = finalAlpha
    return bytes(finalColor)

def decode_block_into_abgr8(f, dwWidth, dwHeight, dxgiFormat):
    rounded_height = (dwHeight + 3) // 4 * 4
    rounded_width = (dwWidth + 3) // 4 * 4
    block_size = 8 if dxgiFormat == 71 else 16
    blocks_height = rounded_height // 4
    blocks_width = rounded_width // 4
    line_pitch = blocks_width * block_size
    size_in_bytes = line_pitch * blocks_height
    in_data = f.read(size_in_bytes)
    if len(in_data) != size_in_bytes:
        raise Exception('Data read incomplete')
    decode_callback = None
    if dxgiFormat == 71:
        decode_callback = decode_dxt1
    elif dxgiFormat == 74:
        decode_callback = decode_dxt3
    elif dxgiFormat == 77:
        decode_callback = decode_dxt5
    elif dxgiFormat == 83:
        decode_callback = decode_bc5
    elif dxgiFormat == 98:
        decode_callback = decode_bc7_block
    else:
        raise Exception('Not supported format ' + str(dxgiFormat))
    pixel_size_in_bytes = 4
    block_width_size_in_bytes = 4 * pixel_size_in_bytes
    single_row_size_in_bytes = blocks_width * block_width_size_in_bytes
    out_data = bytearray(single_row_size_in_bytes * rounded_height)
    for row in range(0, rounded_height, 4):
        offs = row // 4 * line_pitch
        block_line_data = in_data[offs:offs + line_pitch]
        blocks = len(block_line_data) // block_size
        blocks_line_width = blocks * block_size
        for block_offset in range(0, blocks_line_width, block_size):
            block = block_line_data[block_offset:block_offset + block_size]
            decoded = decode_callback(block)
            for i in range(4):
                start_write_offset = block_offset // block_size * block_width_size_in_bytes + (row + i) * single_row_size_in_bytes
                start_read_offset = 4 * 4 * i
                out_data[start_write_offset:start_write_offset + block_width_size_in_bytes] = decoded[start_read_offset:start_read_offset + block_width_size_in_bytes]
    if rounded_height != dwHeight or rounded_width != dwWidth:
        single_row_size_in_bytes_cropped = pixel_size_in_bytes * dwWidth
        out_data_cropped = bytearray(single_row_size_in_bytes_cropped * dwHeight)
        for row in range(dwHeight):
            out_data_cropped[single_row_size_in_bytes_cropped * row:single_row_size_in_bytes_cropped * (row + 1)] = out_data[single_row_size_in_bytes * row:single_row_size_in_bytes * (row + 1)]
        out_data = out_data_cropped
    return bytes(out_data)

def decode_l8_into_abgr8(f, dwWidth, dwHeight, dxgiFormat):
    size_in_bytes = dwWidth * dwHeight * 1
    in_data = f.read(size_in_bytes)
    if len(in_data) != size_in_bytes:
        raise Exception('Data read incomplete')
    out_data = bytearray(dwWidth * dwHeight * 4)
    for row in range(dwHeight):
        for col in range(dwWidth):
            out_offset = (row * dwWidth + col) * 4
            in_offset = (row * dwWidth + col) * 1
            color, = struct.unpack(b'<B', in_data[in_offset:in_offset + 1])
            out_data[out_offset + 0] = color & 255
            out_data[out_offset + 1] = color & 255
            out_data[out_offset + 2] = color & 255
            out_data[out_offset + 3] = 255
    return bytes(out_data)

def decode_la8_into_abgr8(f, dwWidth, dwHeight, dxgiFormat):
    size_in_bytes = dwWidth * dwHeight * 2
    in_data = f.read(size_in_bytes)
    if len(in_data) != size_in_bytes:
        raise Exception('Data read incomplete')
    out_data = bytearray(dwWidth * dwHeight * 4)
    for row in range(dwHeight):
        for col in range(dwWidth):
            out_offset = (row * dwWidth + col) * 4
            in_offset = (row * dwWidth + col) * 2
            color, = struct.unpack(b'<H', in_data[in_offset:in_offset + 2])
            out_data[out_offset + 0] = color >> 8 & 255
            out_data[out_offset + 1] = color >> 8 & 255
            out_data[out_offset + 2] = color >> 8 & 255
            out_data[out_offset + 3] = color >> 0 & 255
    return bytes(out_data)

def decode_rgb565_into_abgr8(f, dwWidth, dwHeight, dxgiFormat):
    size_in_bytes = dwWidth * dwHeight * 2
    in_data = f.read(size_in_bytes)
    if len(in_data) != size_in_bytes:
        raise Exception('Data read incomplete')
    out_data = bytearray(dwWidth * dwHeight * 4)
    for row in range(dwHeight):
        for col in range(dwWidth):
            out_offset = (row * dwWidth + col) * 4
            in_offset = (row * dwWidth + col) * 2
            color, = struct.unpack(b'<H', in_data[in_offset:in_offset + 2])
            out_data[out_offset + 0] = (color >> 11 & 31) << 3
            out_data[out_offset + 1] = (color >> 5 & 63) << 2
            out_data[out_offset + 2] = (color & 31) << 3
            out_data[out_offset + 3] = 255
    return bytes(out_data)

def decode_argb4444_into_abgr8(f, dwWidth, dwHeight, dxgiFormat):
    size_in_bytes = dwWidth * dwHeight * 2
    in_data = f.read(size_in_bytes)
    if len(in_data) != size_in_bytes:
        raise Exception('Data read incomplete')
    out_data = bytearray(dwWidth * dwHeight * 4)
    for row in range(dwHeight):
        for col in range(dwWidth):
            out_offset = (row * dwWidth + col) * 4
            in_offset = (row * dwWidth + col) * 2
            color, = struct.unpack(b'<H', in_data[in_offset:in_offset + 2])
            out_data[out_offset + 0] = (color >> 8 & 15) * 17
            out_data[out_offset + 1] = (color >> 4 & 15) * 17
            out_data[out_offset + 2] = (color >> 0 & 15) * 17
            out_data[out_offset + 3] = (color >> 12 & 15) * 17
    return bytes(out_data)

def decode_rgba8_into_abgr8(f, dwWidth, dwHeight, dxgiFormat):
    size_in_bytes = dwWidth * dwHeight * 4
    in_data = f.read(size_in_bytes)
    if len(in_data) != size_in_bytes:
        raise Exception('Data read incomplete')
    out_data = bytearray(dwWidth * dwHeight * 4)
    for row in range(dwHeight):
        for col in range(dwWidth):
            out_offset = (row * dwWidth + col) * 4
            in_offset = out_offset
            color, = struct.unpack(b'<I', in_data[in_offset:in_offset + 4])
            out_data[out_offset + 0] = color >> 0 & 255
            out_data[out_offset + 1] = color >> 8 & 255
            out_data[out_offset + 2] = color >> 16 & 255
            out_data[out_offset + 3] = color >> 24 & 255
    return bytes(out_data)

def decode_argb8_into_agbr8(f, dwWidth, dwHeight, dxgiFormat):
    size_in_bytes = dwWidth * dwHeight * 4
    in_data = f.read(size_in_bytes)
    if len(in_data) != size_in_bytes:
        raise Exception('Data read incomplete')
    out_data = bytearray(dwWidth * dwHeight * 4)
    for row in range(dwHeight):
        for col in range(dwWidth):
            out_offset = (row * dwWidth + col) * 4
            in_offset = out_offset
            color, = struct.unpack(b'<I', in_data[in_offset:in_offset + 4])
            out_data[out_offset + 0] = color >> 16 & 255
            out_data[out_offset + 1] = color >> 8 & 255
            out_data[out_offset + 2] = color >> 0 & 255
            out_data[out_offset + 3] = color >> 24 & 255
    return bytes(out_data)

def get_dds_header(fmt, width, height, mipmap_levels, is_cube_map):
    dwMagic = b'DDS '
    dwSize = 124
    dwFlags = 1 | 2 | 4 | 4096
    dwHeight = height
    dwWidth = width
    dwPitchOrLinearSize = 0
    dwDepth = 0
    dwMipMapCount = 0
    ddspf_dwSize = 32
    ddspf_dwFlags = 0
    ddspf_dwFourCC = b''
    ddspf_dwRGBBitCount = 0
    ddspf_dwRBitMask = 0
    ddspf_dwGBitMask = 0
    ddspf_dwBBitMask = 0
    ddspf_dwABitMask = 0
    dwCaps = 4096
    dwCaps2 = 0
    dwCaps3 = 0
    dwCaps4 = 0
    dxgiFormat = 0
    resourceDimension = 3
    miscFlag = 0
    arraySize = 1
    miscFlags2 = 0
    if True:
        if fmt == 'LA8':
            ddspf_dwRBitMask, ddspf_dwGBitMask, ddspf_dwBBitMask, ddspf_dwABitMask = (255, 255, 255, 65280)
            dwFlags |= 8
        elif fmt == 'L8':
            ddspf_dwRBitMask, ddspf_dwGBitMask, ddspf_dwBBitMask, ddspf_dwABitMask = (255, 255, 255, 0)
            dwFlags |= 8
        elif fmt == 'ARGB8' or fmt == 'ARGB8_SRGB':
            ddspf_dwRBitMask, ddspf_dwGBitMask, ddspf_dwBBitMask, ddspf_dwABitMask = (65280, 16711680, 4278190080, 255)
            dwFlags |= 8
        elif fmt == 'RGBA8':
            ddspf_dwRBitMask, ddspf_dwGBitMask, ddspf_dwBBitMask, ddspf_dwABitMask = (255, 65280, 16711680, 4278190080)
            dwFlags |= 8
        elif fmt == 'RGB565':
            ddspf_dwRBitMask, ddspf_dwGBitMask, ddspf_dwBBitMask, ddspf_dwABitMask = (63488, 2016, 31, 0)
            dwFlags |= 8
        elif fmt == 'ARGB4444':
            ddspf_dwRBitMask, ddspf_dwGBitMask, ddspf_dwBBitMask, ddspf_dwABitMask = (3840, 240, 15, 61440)
            dwFlags |= 8
        elif fmt == 'BC5':
            dwFlags |= 524288
            dxgiFormat = 83
        elif fmt == 'BC7':
            dwFlags |= 524288
            dxgiFormat = 98
        elif fmt == 'DXT1':
            dwFlags |= 524288
        elif fmt == 'DXT3':
            dwFlags |= 524288
        elif fmt == 'DXT5':
            dwFlags |= 524288
    if dwFlags & 8 != 0:
        ddspf_dwFlags = 64
        if ddspf_dwABitMask != 0:
            ddspf_dwFlags |= 1
        all_bit_mask = ddspf_dwRBitMask | ddspf_dwGBitMask | ddspf_dwBBitMask | ddspf_dwABitMask
        if all_bit_mask & 4278190080 != 0:
            ddspf_dwRGBBitCount = 32
        elif all_bit_mask & 16711680 != 0:
            ddspf_dwRGBBitCount = 24
        elif all_bit_mask & 65280 != 0:
            ddspf_dwRGBBitCount = 16
        elif all_bit_mask & 255 != 0:
            ddspf_dwRGBBitCount = 8
        dwPitchOrLinearSize = (width * ddspf_dwRGBBitCount + 7) // 8
    if dwFlags & 524288 != 0:
        ddspf_dwFlags = 4
        if dxgiFormat != 0:
            ddspf_dwFourCC = b'DX10'
        else:
            ddspf_dwFourCC = fmt.encode('ASCII')
        dwPitchOrLinearSize = (width + 3) // 4 * (8 if fmt == 'DXT1' else 16)
    if mipmap_levels != None:
        dwFlags |= 131072
        dwMipMapCount = mipmap_levels
        dwCaps |= 4194304
    if mipmap_levels != None or is_cube_map:
        dwCaps |= 8
    if is_cube_map:
        dwCaps2 = 512 | 1024 | 2048 | 4096 | 8192 | 16384 | 32768
    if ddspf_dwFourCC == b'DX10':
        return struct.pack('<4s20I4s10I5I', dwMagic, dwSize, dwFlags, dwHeight, dwWidth, dwPitchOrLinearSize, dwDepth, dwMipMapCount, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ddspf_dwSize, ddspf_dwFlags, ddspf_dwFourCC, ddspf_dwRGBBitCount, ddspf_dwRBitMask, ddspf_dwGBitMask, ddspf_dwBBitMask, ddspf_dwABitMask, dwCaps, dwCaps2, dwCaps3, dwCaps4, 0, dxgiFormat, resourceDimension, miscFlag, arraySize, miscFlags2)
    else:
        return struct.pack('<4s20I4s10I', dwMagic, dwSize, dwFlags, dwHeight, dwWidth, dwPitchOrLinearSize, dwDepth, dwMipMapCount, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ddspf_dwSize, ddspf_dwFlags, ddspf_dwFourCC, ddspf_dwRGBBitCount, ddspf_dwRBitMask, ddspf_dwGBitMask, ddspf_dwBBitMask, ddspf_dwABitMask, dwCaps, dwCaps2, dwCaps3, dwCaps4, 0)

def uncompress_nislzss(src, decompressed_size, compressed_size):
    des = int.from_bytes(src.read(4), byteorder='little')
    if des != decompressed_size:
        des = des if des > decompressed_size else decompressed_size
    cms = int.from_bytes(src.read(4), byteorder='little')
    if cms != compressed_size and compressed_size - cms != 4:
        raise Exception("compression size in header and stream don't match")
    num3 = int.from_bytes(src.read(4), byteorder='little')
    fin = src.tell() + cms - 13
    cd = bytearray(des)
    num4 = 0
    while src.tell() <= fin:
        b = src.read(1)[0]
        if b == num3:
            b2 = src.read(1)[0]
            if b2 != num3:
                if b2 >= num3:
                    b2 -= 1
                b3 = src.read(1)[0]
                if b2 < b3:
                    for _ in range(b3):
                        cd[num4] = cd[num4 - b2]
                        num4 += 1
                else:
                    sliding_window_pos = num4 - b2
                    cd[num4:num4 + b3] = cd[sliding_window_pos:sliding_window_pos + b3]
                    num4 += b3
            else:
                cd[num4] = b2
                num4 += 1
        else:
            cd[num4] = b
            num4 += 1
    return cd

def uncompress_lz4(src, decompressed_size, compressed_size):
    dst = bytearray(decompressed_size)
    min_match_len = 4
    num4 = 0
    fin = src.tell() + compressed_size

    def get_length(src, length):
        if length != 15:
            return length
        while True:
            read_buf = src.read(1)
            if len(read_buf) != 1:
                raise Exception('EOF at length read')
            len_part = read_buf[0]
            length += len_part
            if len_part != 255:
                break
        return length
    while src.tell() <= fin:
        read_buf = src.read(1)
        if not read_buf:
            raise Exception('EOF at reading literal-len')
        token = read_buf[0]
        literal_len = get_length(src, token >> 4 & 15)
        read_buf = src.read(literal_len)
        if len(read_buf) != literal_len:
            raise Exception('not literal data')
        dst[num4:num4 + literal_len] = read_buf[:literal_len]
        num4 += literal_len
        read_buf = src.read(2)
        if not read_buf or src.tell() > fin:
            if token & 15 != 0:
                raise Exception('EOF, but match-len > 0: %u' % (token % 15,))
            break
        if len(read_buf) != 2:
            raise Exception('premature EOF')
        offset = read_buf[0] | read_buf[1] << 8
        if offset == 0:
            raise Exception("offset can't be 0")
        match_len = get_length(src, token >> 0 & 15)
        match_len += min_match_len
        if offset < match_len:
            for _ in range(match_len):
                dst[num4] = dst[num4 - offset]
                num4 += 1
        else:
            sliding_window_pos = num4 - offset
            dst[num4:num4 + match_len] = dst[sliding_window_pos:sliding_window_pos + match_len]
            num4 += match_len
    return dst

def uncompress_zstd(src, decompressed_size, compressed_size):
    dctx = zstandard.ZstdDecompressor()
    uncompressed = dctx.decompress(src.read(compressed_size), max_output_size=decompressed_size)
    return uncompressed
NOEPY_HEADER_BE = 1381582928
NOEPY_HEADER_LE = 1346918738

def get_type(id_, type_strings, class_descriptors):
    total_types = len(type_strings) + 1
    if id_ < total_types:
        return type_strings[id_]
    else:
        id_ -= total_types
        return class_descriptors[id_].name

def get_class_from_type(id_, type_strings):
    total_types = len(type_strings) + 1
    if id_ < total_types:
        return None
    else:
        return id_ - total_types + 1

def get_reference_from_class_descriptor_index(cluster_type_info, class_name, index):
    if class_name in cluster_type_info.list_for_class_descriptors and len(cluster_type_info.list_for_class_descriptors[class_name]) > index:
        return cluster_type_info.list_for_class_descriptors[class_name][index].split('#', 1)
    return None

def get_class_name(cluster_type_info, id_):
    return cluster_type_info.class_descriptors[id_ - 1].name

def get_class_size(cluster_type_info, id_):
    return cluster_type_info.class_descriptors[id_ - 1].get_size_in_bytes()

def get_member_id_to_pointer_fixup_list(g, class_descriptor, cluster_type_info, cluster_list_fixup_info, pointer_fixup_count, class_element):
    member_id_to_pointer_fixup_list = {}
    for m in range(class_descriptor.class_data_member_count):
        member_id = class_descriptor.member_offset + m
        data_member = cluster_type_info.data_members[member_id]
        value_offset = data_member.value_offset
        member_id_to_pointer_fixup_list[member_id] = []
        for b in range(pointer_fixup_count):
            pointer_fixup = cluster_list_fixup_info.pointer_fixups[b + cluster_list_fixup_info.pointer_fixup_offset]
            if pointer_fixup.source_object_id == class_element:
                if (pointer_fixup.som == value_offset + 4 or pointer_fixup.som + 4 == value_offset or pointer_fixup.som == value_offset) and (not pointer_fixup.is_class_data_member()) or (pointer_fixup.som == member_id and pointer_fixup.is_class_data_member()):
                    member_id_to_pointer_fixup_list[member_id].append(pointer_fixup)
    return member_id_to_pointer_fixup_list

def map_object_member_from_value_offset_recursive(cluster_type_info, class_id, offset_from_parent, object_value_offset_to_member_id, object_member_to_fixup_map):
    class_descriptor = cluster_type_info.class_descriptors[class_id - 1]
    for m in range(class_descriptor.class_data_member_count):
        member_id = class_descriptor.member_offset + m
        data_member = cluster_type_info.data_members[member_id]
        value_offset = offset_from_parent + data_member.value_offset
        object_value_offset_to_member_id[value_offset] = member_id
        for i in object_member_to_fixup_map:
            if member_id not in object_member_to_fixup_map[i]:
                object_member_to_fixup_map[i][member_id] = []
    if class_descriptor.super_class_id > 0:
        map_object_member_from_value_offset_recursive(cluster_type_info, class_descriptor.super_class_id, offset_from_parent, object_value_offset_to_member_id, object_member_to_fixup_map)

def get_object_member_pointer_fixup_list_map(cluster_type_info, cluster_list_fixup_info, cluster_instance_list_header):
    if cluster_instance_list_header['m_classID'] <= 0:
        return {}
    object_member_to_fixup_map = {}
    for i in range(cluster_instance_list_header['m_count']):
        object_member_to_fixup_map[i] = {}
    object_value_offset_to_member_id = {}
    map_object_member_from_value_offset_recursive(cluster_type_info, cluster_instance_list_header['m_classID'], 0, object_value_offset_to_member_id, object_member_to_fixup_map)
    object_value_offset_to_member_id_sorted_keys = sorted(object_value_offset_to_member_id.keys())
    class_size_one = get_class_size(cluster_type_info, cluster_instance_list_header['m_classID'])
    class_size_total = class_size_one * cluster_instance_list_header['m_count']
    for b in range(cluster_instance_list_header['m_pointerFixupCount']):
        pointer_fixup = cluster_list_fixup_info.pointer_fixups[b + cluster_list_fixup_info.pointer_fixup_offset]
        if not pointer_fixup.source_object_id in object_member_to_fixup_map:
            object_member_to_fixup_map[pointer_fixup.source_object_id] = {}
        obj_source_object_id = object_member_to_fixup_map[pointer_fixup.source_object_id]
        member_id = None
        if pointer_fixup.is_class_data_member():
            member_id = pointer_fixup.som
        elif not pointer_fixup.is_class_data_member():
            for key in object_value_offset_to_member_id_sorted_keys:
                if key > pointer_fixup.som:
                    break
                member_id = object_value_offset_to_member_id[key]
        if member_id != None:
            if not member_id in obj_source_object_id:
                obj_source_object_id[member_id] = []
            obj_source_object_id[member_id].append(pointer_fixup)
    return object_member_to_fixup_map

def get_object_member_array_fixup_list_map(cluster_type_info, cluster_list_fixup_info, cluster_instance_list_header):
    if cluster_instance_list_header['m_classID'] <= 0:
        return {}
    object_member_to_fixup_map = {}
    for i in range(cluster_instance_list_header['m_count']):
        object_member_to_fixup_map[i] = {}
    object_value_offset_to_member_id = {}
    map_object_member_from_value_offset_recursive(cluster_type_info, cluster_instance_list_header['m_classID'], 0, object_value_offset_to_member_id, object_member_to_fixup_map)
    object_value_offset_to_member_id_sorted_keys = sorted(object_value_offset_to_member_id.keys())
    class_size_one = get_class_size(cluster_type_info, cluster_instance_list_header['m_classID'])
    class_size_total = class_size_one * cluster_instance_list_header['m_count']
    for b in range(cluster_instance_list_header['m_arrayFixupCount']):
        array_fixup = cluster_list_fixup_info.array_fixups[b + cluster_list_fixup_info.array_fixup_offset]
        if not array_fixup.source_object_id in object_member_to_fixup_map:
            object_member_to_fixup_map[array_fixup.source_object_id] = {}
        obj_source_object_id = object_member_to_fixup_map[array_fixup.source_object_id]
        member_id = None
        if array_fixup.is_class_data_member():
            member_id = array_fixup.som
        elif not array_fixup.is_class_data_member():
            for key in object_value_offset_to_member_id_sorted_keys:
                if key > array_fixup.som:
                    break
                member_id = object_value_offset_to_member_id[key]
        if member_id != None:
            if not member_id in obj_source_object_id:
                obj_source_object_id[member_id] = []
            if array_fixup not in obj_source_object_id[member_id]:
                obj_source_object_id[member_id].append(array_fixup)
        if array_fixup.is_class_data_member():
            member_id = array_fixup.som
        elif not array_fixup.is_class_data_member():
            for key in object_value_offset_to_member_id_sorted_keys:
                if key > array_fixup.som + 4:
                    break
                member_id = object_value_offset_to_member_id[key]
        if member_id != None:
            if not member_id in obj_source_object_id:
                obj_source_object_id[member_id] = []
            if array_fixup not in obj_source_object_id[member_id]:
                obj_source_object_id[member_id].append(array_fixup)
    return object_member_to_fixup_map
clusterPrimitiveToPythonStructTypeMapping = {'PUInt8': 'B', 'PInt8': 'b', 'PUInt16': 'H', 'PInt16': 'h', 'PUInt32': 'I', 'PInt32': 'i', 'PUInt64': 'Q', 'PInt64': 'q', 'float': 'f'}

def process_data_members(g, cluster_type_info, cluster_list_fixup_info, id_, member_location, array_location, class_element, cluster_mesh_info, class_name, should_print_class, dict_data, cluster_header, data_instances_by_class, offset_from_parent, array_fixup_count, pointer_fixup_count, object_member_pointer_fixup_list_map, object_member_array_fixup_list_map, root_member_id, is_class_data_member):
    if id_ > 0:

        def process_data_members_recursive(id_=id_, member_location=member_location, class_name=class_name, dict_data=dict_data, offset_from_parent=offset_from_parent, root_member_id=root_member_id):
            process_data_members(g, cluster_type_info, cluster_list_fixup_info, id_, member_location, array_location, class_element, cluster_mesh_info, class_name, should_print_class, dict_data, cluster_header, data_instances_by_class, offset_from_parent, array_fixup_count, pointer_fixup_count, object_member_pointer_fixup_list_map, object_member_array_fixup_list_map, root_member_id, is_class_data_member)
        class_id = id_ - 1
        class_descriptor = cluster_type_info.class_descriptors[class_id]
        member_id_to_pointer_fixup_list = {}
        if cluster_list_fixup_info != None:
            if object_member_pointer_fixup_list_map != None and class_element in object_member_pointer_fixup_list_map:
                member_id_to_pointer_fixup_list = object_member_pointer_fixup_list_map[class_element]
            else:
                member_id_to_pointer_fixup_list = get_member_id_to_pointer_fixup_list(g, class_descriptor, cluster_type_info, cluster_list_fixup_info, pointer_fixup_count, class_element)
        member_id_to_array_fixup_list = {}
        if object_member_array_fixup_list_map != None and class_element in object_member_array_fixup_list_map:
            member_id_to_array_fixup_list = object_member_array_fixup_list_map[class_element]
        for m in range(class_descriptor.class_data_member_count):
            member_id = class_descriptor.member_offset + m
            data_member = cluster_type_info.data_members[member_id]
            info_for_id = member_id
            if root_member_id != None:
                info_for_id = root_member_id
            pointer_fixup_list = []
            if info_for_id in member_id_to_pointer_fixup_list:
                pointer_fixup_list = member_id_to_pointer_fixup_list[info_for_id]
            array_fixup_list = []
            if info_for_id in member_id_to_array_fixup_list:
                array_fixup_list = member_id_to_array_fixup_list[info_for_id]
            type_id = data_member.type_id
            variable_text = data_member.name
            type_text = get_type(type_id, cluster_type_info.type_strings, cluster_type_info.class_descriptors)
            class_type_id = get_class_from_type(type_id, cluster_type_info.type_strings)
            class_type_descriptor = None
            if class_type_id != None:
                class_type_descriptor = cluster_type_info.class_descriptors[class_type_id - 1]
            val = None
            value_offset = data_member.value_offset
            data_offset = member_location + value_offset
            expected_offset = data_member.fixed_array_size
            if expected_offset == 0:
                expected_offset = 1
            expected_size = data_member.size_in_bytes * expected_offset
            g.seek(data_offset)
            if data_instances_by_class != None:
                if type_text in clusterPrimitiveToPythonStructTypeMapping and (class_name.startswith('PArray<') or class_name.startswith('PSharray<')) and (variable_text in ['m_els', 'm_u']):
                    datatype_pystructtype = clusterPrimitiveToPythonStructTypeMapping[type_text]
                    datatype_size_single = struct.calcsize(datatype_pystructtype)
                    val = []
                    if 'm_count' in dict_data:
                        array_count = dict_data['m_count']
                        for array_fixup in array_fixup_list:
                            if array_fixup.som == offset_from_parent + value_offset or array_fixup.som == offset_from_parent + value_offset + 4:
                                old_position = g.tell()
                                if array_fixup.count != array_count and array_count >= 65535:
                                    array_count = 0
                                g.seek(array_location + array_fixup.offset)
                                val = bytearray(g.read(array_count * datatype_size_single))
                                if cluster_header.cluster_marker == NOEPY_HEADER_BE:
                                    bytearray_byteswap(val, datatype_size_single)
                                val = cast_memoryview(memoryview(val), datatype_pystructtype)
                                g.seek(old_position)
                                break
                elif class_name[0:7] == 'PArray<' and class_name[-1:] == '>' and (variable_text in ['m_els']):
                    array_count = dict_data['m_count']
                    current_count = 0
                    type_value = class_name[7:-1]
                    is_pointer = False
                    if not type_value in data_instances_by_class:
                        if type_value[0:10] == 'PDataBlock':
                            type_value = type_value[0:10]
                        if type_value[-2:] == ' *':
                            type_value = type_value[:-2]
                            is_pointer = True
                    val = None
                    if array_count == 0:
                        val = []
                    elif type_value in data_instances_by_class:
                        for pointer_fixup in pointer_fixup_list:
                            if (is_pointer == True or (is_pointer == False and pointer_fixup.som == offset_from_parent + value_offset)) and (not pointer_fixup.is_class_data_member()) and (len(cluster_type_info.classes_strings) > pointer_fixup.destination_object.object_list) and (cluster_type_info.classes_strings[pointer_fixup.destination_object.object_list] == type_value) and (pointer_fixup.destination_object.object_list in data_instances_by_class):
                                data_instances_by_class_this = data_instances_by_class[pointer_fixup.destination_object.object_list]
                                if is_pointer == True:
                                    if current_count == 0:
                                        val = [None] * array_count
                                    offset_calculation = pointer_fixup.destination_object.object_id
                                    if len(data_instances_by_class_this) > offset_calculation:
                                        val[pointer_fixup.array_index] = data_instances_by_class_this[offset_calculation]
                                    current_count += 1
                                else:
                                    val = [data_instances_by_class_this[pointer_fixup.destination_object.object_id + i] for i in range(pointer_fixup.array_index)]
                    else:
                        for pointer_fixup in pointer_fixup_list:
                            if pointer_fixup.som == offset_from_parent + value_offset and (not pointer_fixup.is_class_data_member()):
                                user_fix_id = pointer_fixup.user_fixup_id
                                if user_fix_id != None and user_fix_id < len(cluster_list_fixup_info.user_fixup_results) and (type(cluster_list_fixup_info.user_fixup_results[user_fix_id].data) == str):
                                    if current_count == 0:
                                        val = [None] * array_count
                                    val[pointer_fixup.array_index] = cluster_list_fixup_info.user_fixup_results[user_fix_id].data
                                    current_count += 1
                    if type_value in ['PShaderParameterDefinition'] and val != None:
                        shader_object_dict = {}
                        for pointer_fixup in pointer_fixup_list:
                            if not pointer_fixup.is_class_data_member():
                                for arr_index in range(len(val)):
                                    value_this = val[arr_index]
                                    pointer_fixup_list_offset_needed = pointer_fixup.som
                                    if value_this['m_parameterType'] == 71:
                                        pointer_fixup_list_offset_needed -= 8
                                        if value_this['m_bufferLoc']['m_offset'] == pointer_fixup_list_offset_needed:
                                            if len(cluster_type_info.classes_strings) > pointer_fixup.destination_object.object_list and pointer_fixup.destination_object.object_list in data_instances_by_class:
                                                shader_object_dict[value_this['m_name']['m_buffer']] = data_instances_by_class[pointer_fixup.destination_object.object_list][pointer_fixup.destination_object.object_id]
                                    elif value_this['m_parameterType'] == 66 or value_this['m_parameterType'] == 68:
                                        if value_this['m_bufferLoc']['m_size'] == 24:
                                            pointer_fixup_list_offset_needed -= 16
                                        else:
                                            pointer_fixup_list_offset_needed -= 12
                                        if value_this['m_bufferLoc']['m_offset'] == pointer_fixup_list_offset_needed:
                                            user_fix_id = pointer_fixup.user_fixup_id
                                            if user_fix_id != None and user_fix_id < len(cluster_list_fixup_info.user_fixup_results) and ('PAssetReferenceImport' in data_instances_by_class) and (type(cluster_list_fixup_info.user_fixup_results[user_fix_id].data) == int) and (cluster_list_fixup_info.user_fixup_results[user_fix_id].data < len(data_instances_by_class['PAssetReferenceImport'])):
                                                shader_object_dict[value_this['m_name']['m_buffer']] = data_instances_by_class['PAssetReferenceImport'][cluster_list_fixup_info.user_fixup_results[user_fix_id].data]
                        dict_data['mu_object_references'] = shader_object_dict
                elif (class_name[0:9] == 'PSharray<' and class_name[-1:] == '>') and variable_text in ['m_u']:
                    array_count = dict_data['m_count']
                    current_count = 0
                    val = [None] * array_count
                    for b in range(pointer_fixup_count):
                        if current_count >= array_count:
                            break
                        pointer_fixup = cluster_list_fixup_info.pointer_fixups[b + cluster_list_fixup_info.pointer_fixup_offset]
                        if pointer_fixup.source_object_id == class_element and pointer_fixup.som == offset_from_parent + value_offset and (not pointer_fixup.is_class_data_member()) and (pointer_fixup.destination_object.object_list in data_instances_by_class):
                            offset_calculation = pointer_fixup.destination_object.object_id
                            data_instances_by_class_this = data_instances_by_class[pointer_fixup.destination_object.object_list]
                            if len(data_instances_by_class_this) > offset_calculation:
                                val[pointer_fixup.array_index] = data_instances_by_class_this[offset_calculation]
                            current_count += 1
                    if array_count > 0 and current_count == 0:
                        val[0] = dict_data[variable_text]
                        process_data_members_recursive(id_=class_type_id, member_location=data_offset, class_name=type_text, dict_data=val[0], offset_from_parent=offset_from_parent + value_offset, root_member_id=member_id)
                elif type_text in data_instances_by_class or type_text in ['PBase']:
                    for pointer_fixup in pointer_fixup_list:
                        pointer_fixup_is_class_data_member = pointer_fixup.is_class_data_member()
                        if pointer_fixup_is_class_data_member and is_class_data_member or (not pointer_fixup_is_class_data_member and (not is_class_data_member) and (pointer_fixup.som == offset_from_parent + value_offset)):
                            user_fix_id = pointer_fixup.user_fixup_id
                            if pointer_fixup.destination_object != None:
                                object_id = pointer_fixup.destination_object.object_id
                                object_list = pointer_fixup.destination_object.object_list
                                if object_list in data_instances_by_class:
                                    data_instances_by_class_this = data_instances_by_class[object_list]
                                    if len(data_instances_by_class_this) > object_id:
                                        val = data_instances_by_class_this[object_id]
                                        break
                elif type_text in cluster_type_info.import_classes_strings:
                    for pointer_fixup in pointer_fixup_list:
                        pointer_fixup_is_class_data_member = pointer_fixup.is_class_data_member()
                        if pointer_fixup_is_class_data_member and is_class_data_member or (not pointer_fixup_is_class_data_member and (not is_class_data_member) and (pointer_fixup.som == offset_from_parent + value_offset)):
                            user_fix_id = pointer_fixup.user_fixup_id
                            if user_fix_id != None and user_fix_id < len(cluster_list_fixup_info.user_fixup_results) and ('PAssetReferenceImport' in data_instances_by_class) and (type(cluster_list_fixup_info.user_fixup_results[user_fix_id].data) == int) and (cluster_list_fixup_info.user_fixup_results[user_fix_id].data < len(data_instances_by_class['PAssetReferenceImport'])):
                                val = data_instances_by_class['PAssetReferenceImport'][cluster_list_fixup_info.user_fixup_results[user_fix_id].data]
                                break
                elif class_type_descriptor != None and (type(dict_data[variable_text]) == dict and class_type_descriptor.get_size_in_bytes() * (1 if data_member.fixed_array_size == 0 else data_member.fixed_array_size) == expected_size or (type_text[0:7] == 'PArray<' and type_text[-1:] == '>') or (type_text[0:9] == 'PSharray<' and type_text[-1:] == '>')):
                    if data_member.fixed_array_size > 0:
                        val = dict_data[variable_text]
                        structsize = class_type_descriptor.get_size_in_bytes()
                        for i in range(data_member.fixed_array_size):
                            val2 = val[i]
                            process_data_members_recursive(id_=class_type_id, member_location=data_offset + structsize * i, class_name=type_text, dict_data=val2, offset_from_parent=offset_from_parent + value_offset + structsize * i, root_member_id=member_id)
                    else:
                        val = dict_data[variable_text]
                        process_data_members_recursive(id_=class_type_id, member_location=data_offset, class_name=type_text, dict_data=val, offset_from_parent=offset_from_parent + value_offset, root_member_id=member_id)
            elif type_text in clusterPrimitiveToPythonStructTypeMapping:
                datatype_pystructtype = clusterPrimitiveToPythonStructTypeMapping[type_text]
                datatype_size_single = struct.calcsize(datatype_pystructtype)
                if (class_name.startswith('PArray<') or class_name.startswith('PSharray<')) and variable_text in ['m_els', 'm_u']:
                    val = []
                elif data_member.fixed_array_size != 0:
                    val = bytearray(g.read(data_member.fixed_array_size * datatype_size_single))
                    if cluster_header.cluster_marker == NOEPY_HEADER_BE:
                        bytearray_byteswap(val, datatype_size_single)
                    val = cast_memoryview(memoryview(val), datatype_pystructtype)
                elif type_text in ['float']:
                    ba = bytearray(g.read(datatype_size_single))
                    if cluster_header.cluster_marker == NOEPY_HEADER_BE:
                        bytearray_byteswap(ba, datatype_size_single)
                    val = cast_memoryview(memoryview(ba), datatype_pystructtype)[0]
                else:
                    val = read_integer(g, datatype_size_single, type_text.startswith('PU'), '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
            elif type_text in ['bool']:
                val = read_integer(g, 1, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<') > 0
            elif type_text in ['PChar']:
                val = ''
                for array_fixup in array_fixup_list:
                    if array_fixup.som == offset_from_parent + value_offset or len(array_fixup_list) == 1:
                        old_position = g.tell()
                        g.seek(array_location + array_fixup.offset)
                        try:
                            val = read_null_ending_string(g)
                        except:
                            pass
                        g.seek(old_position)
                        break
                if expected_size == 4:
                    g.seek(4, io.SEEK_CUR)
                elif expected_size == 1:
                    g.seek(1, io.SEEK_CUR)
            elif type_text in ['PCgParameterInfoGCM', 'PCgCodebookGCM', 'PCgBindingParameterInfoGXM', 'PCgBindingSceneConstantsGXM']:
                val = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
            elif type_text in ['Vector4'] and expected_size == 4:
                val = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
            elif type_text in ['PLightType', 'PRenderDataType', 'PAnimationKeyDataType', 'PTextureFormatBase', 'PSceneRenderPassType']:
                val = None
                for pointer_fixup in pointer_fixup_list:
                    if pointer_fixup.is_class_data_member():
                        user_fix_id = pointer_fixup.user_fixup_id
                        if user_fix_id != None and cluster_list_fixup_info != None and (user_fix_id < len(cluster_list_fixup_info.user_fixup_results)):
                            val = cluster_list_fixup_info.user_fixup_results[user_fix_id].data
                        else:
                            val = pointer_fixup.destination_object.object_list
            elif type_text in ['PClassDescriptor']:
                val = None
                for pointer_fixup in pointer_fixup_list:
                    if pointer_fixup.is_class_data_member():
                        user_fix_id = pointer_fixup.user_fixup_id
                        if user_fix_id != None and cluster_list_fixup_info != None and (user_fix_id < len(cluster_list_fixup_info.user_fixup_results)):
                            val = cluster_list_fixup_info.user_fixup_results[user_fix_id].data
                        else:
                            val = pointer_fixup.destination_object.object_list
                        break
            elif class_type_descriptor != None and class_type_descriptor.get_size_in_bytes() == expected_size and (class_name[0:9] == 'PSharray<' and class_name[-1:] == '>') and (variable_text in ['m_u']):
                val = {}
                process_data_members_recursive(id_=class_type_id, member_location=data_offset, class_name=type_text, dict_data=val, offset_from_parent=offset_from_parent + value_offset, root_member_id=member_id)
            elif class_type_descriptor != None and (class_type_descriptor.get_size_in_bytes() * (1 if data_member.fixed_array_size == 0 else data_member.fixed_array_size) == expected_size or (type_text[0:7] == 'PArray<' and type_text[-1:] == '>') or (type_text[0:9] == 'PSharray<' and type_text[-1:] == '>')):
                if data_member.fixed_array_size > 0:
                    val = []
                    structsize = class_type_descriptor.get_size_in_bytes()
                    for i in range(data_member.fixed_array_size):
                        val2 = {}
                        process_data_members_recursive(id_=class_type_id, member_location=data_offset + structsize * i, class_name=type_text, dict_data=val2, offset_from_parent=offset_from_parent + value_offset + structsize * i, root_member_id=member_id)
                        val.append(val2)
                else:
                    val = {}
                    process_data_members_recursive(id_=class_type_id, member_location=data_offset, class_name=type_text, dict_data=val, offset_from_parent=offset_from_parent + value_offset, root_member_id=member_id)
            if data_instances_by_class != None and val != None or data_instances_by_class == None:
                dict_data[variable_text] = val
        process_data_members_recursive(id_=class_descriptor.super_class_id)
        return dict_data
cluster_classes_to_handle = ['PAnimationChannel', 'PAnimationChannelTimes', 'PAnimationClip', 'PAnimationConstantChannel', 'PAnimationSet', 'PAssetReference', 'PAssetReferenceImport', 'PCgParameterInfoGCM', 'PContextVariantFoldingTable', 'PDataBlock', 'PDataBlockD3D11', 'PDataBlockGCM', 'PDataBlockGL', 'PDataBlockGNM', 'PDataBlockGXM', 'PEffect', 'PEffectVariant', 'PLight', 'PMaterial', 'PMaterialSwitch', 'PMatrix4', 'PMesh', 'PMeshInstance', 'PMeshInstanceBounds', 'PMeshInstanceSegmentContext', 'PMeshInstanceSegmentStreamBinding', 'PMeshSegment', 'PNode', 'PNodeContext', 'PParameterBuffer', 'PSamplerState', 'PSceneRenderPass', 'PShader', 'PShaderComputeProgram', 'PShaderFragmentProgram', 'PShaderGeometryProgram', 'PShaderParameterCaptureBufferLocation', 'PShaderParameterCaptureBufferLocationTypeConstantBuffer', 'PShaderParameterDefinition', 'PShaderPass', 'PShaderPassInfo', 'PShaderStreamDefinition', 'PShaderVertexProgram', 'PSkeletonJointBounds', 'PSkinBoneRemap', 'PString', 'PTexture2D', 'PTextureCubeMap', 'PVertexStream', 'PWorldMatrix']

def process_cluster_instance_list_header(cluster_instance_list_header, g, count_list, cluster_type_info, cluster_list_fixup_info, cluster_mesh_info, cluster_header, filename, data_instances_by_class):
    member_location = g.tell()
    array_location = g.tell() + cluster_instance_list_header['m_objectsSize']
    should_print_class = ''
    class_name = get_class_name(cluster_type_info, cluster_instance_list_header['m_classID'])
    class_size = get_class_size(cluster_type_info, cluster_instance_list_header['m_classID'])
    should_print_class = class_name == should_print_class
    should_handle_class = should_print_class or class_name in cluster_classes_to_handle
    data_instances = None
    if data_instances_by_class == None:
        cluster_type_info.classes_strings.append(class_name)
        data_instances = []
    elif count_list in data_instances_by_class:
        data_instances = data_instances_by_class[count_list]
    else:
        should_handle_class = False
    if should_handle_class:
        object_member_pointer_fixup_list_map = None
        object_member_array_fixup_list_map = None
        if cluster_list_fixup_info != None:
            object_member_pointer_fixup_list_map = get_object_member_pointer_fixup_list_map(cluster_type_info, cluster_list_fixup_info, cluster_instance_list_header)
            object_member_array_fixup_list_map = get_object_member_array_fixup_list_map(cluster_type_info, cluster_list_fixup_info, cluster_instance_list_header)

        def process_data_members_curry(id_=cluster_instance_list_header['m_classID'], member_location=0, class_element=0, class_name=class_name, dict_data=None, data_instances_by_class=data_instances_by_class, offset_from_parent=0, array_fixup_count=cluster_instance_list_header['m_arrayFixupCount'], pointer_fixup_count=cluster_instance_list_header['m_pointerFixupCount'], root_member_id=None, is_class_data_member=True):
            process_data_members(g, cluster_type_info, cluster_list_fixup_info, id_, member_location, array_location, class_element, cluster_mesh_info, class_name, should_print_class, dict_data, cluster_header, data_instances_by_class, offset_from_parent, array_fixup_count, pointer_fixup_count, object_member_pointer_fixup_list_map, object_member_array_fixup_list_map, root_member_id, is_class_data_member)
        for i in range(cluster_instance_list_header['m_count']):
            dict_data = None
            if data_instances_by_class == None:
                dict_data = {}
                data_instances.append(dict_data)
            else:
                dict_data = data_instances[i]
            g.seek(member_location)
            process_data_members_curry(member_location=member_location, class_element=i, dict_data=dict_data)
            if data_instances_by_class == None:
                dict_data['mu_memberLoc'] = member_location
                dict_data['mu_memberClass'] = class_name
            else:
                reference_from_class_descriptor_index = get_reference_from_class_descriptor_index(cluster_type_info, class_name, i)
                if reference_from_class_descriptor_index != None and len(list(reference_from_class_descriptor_index)) > 1:
                    dict_data['mu_name'] = reference_from_class_descriptor_index[1]
            member_location += class_size
    if cluster_list_fixup_info != None:
        cluster_list_fixup_info.pointer_array_fixup_offset += cluster_instance_list_header['m_pointerArrayFixupCount']
        cluster_list_fixup_info.pointer_fixup_offset += cluster_instance_list_header['m_pointerFixupCount']
        cluster_list_fixup_info.array_fixup_offset += cluster_instance_list_header['m_arrayFixupCount']
    if data_instances_by_class != None:
        return None
    if class_name == 'PAssetReference':
        for assetReference in data_instances:
            if not assetReference['m_assetType'] in cluster_type_info.list_for_class_descriptors:
                cluster_type_info.list_for_class_descriptors[assetReference['m_assetType']] = []
            cluster_type_info.list_for_class_descriptors[assetReference['m_assetType']].append(assetReference['m_id']['m_buffer'])
    if class_name == 'PAssetReferenceImport':
        for assetReference in data_instances:
            cluster_type_info.import_classes_strings.append(assetReference['m_targetAssetType'])
    if should_handle_class:
        return data_instances
    else:
        return None

class ClusterClusterHeader:

    def __init__(self, g):
        self.cluster_marker = read_integer(g, 4, False, '<')
        self.size = read_integer(g, 4, False, '>' if self.cluster_marker == NOEPY_HEADER_BE else '<')
        self.packed_namespace_size = read_integer(g, 4, False, '>' if self.cluster_marker == NOEPY_HEADER_BE else '<')
        self.platform_id = read_integer(g, 4, False, '>' if self.cluster_marker == NOEPY_HEADER_BE else '<')
        self.instance_list_count = read_integer(g, 4, False, '>' if self.cluster_marker == NOEPY_HEADER_BE else '<')
        self.array_fixup_size = read_integer(g, 4, False, '>' if self.cluster_marker == NOEPY_HEADER_BE else '<')
        self.array_fixup_count = read_integer(g, 4, False, '>' if self.cluster_marker == NOEPY_HEADER_BE else '<')
        self.pointer_fixup_size = read_integer(g, 4, False, '>' if self.cluster_marker == NOEPY_HEADER_BE else '<')
        self.pointer_fixup_count = read_integer(g, 4, False, '>' if self.cluster_marker == NOEPY_HEADER_BE else '<')
        self.pointer_array_fixup_size = read_integer(g, 4, False, '>' if self.cluster_marker == NOEPY_HEADER_BE else '<')
        self.pointer_array_fixup_count = read_integer(g, 4, False, '>' if self.cluster_marker == NOEPY_HEADER_BE else '<')
        self.pointers_in_arrays_count = read_integer(g, 4, False, '>' if self.cluster_marker == NOEPY_HEADER_BE else '<')
        self.user_fixup_count = read_integer(g, 4, False, '>' if self.cluster_marker == NOEPY_HEADER_BE else '<')
        self.user_fixup_data_size = read_integer(g, 4, False, '>' if self.cluster_marker == NOEPY_HEADER_BE else '<')
        self.total_data_size = read_integer(g, 4, False, '>' if self.cluster_marker == NOEPY_HEADER_BE else '<')
        self.header_class_instance_count = read_integer(g, 4, False, '>' if self.cluster_marker == NOEPY_HEADER_BE else '<')
        self.header_class_child_count = read_integer(g, 4, False, '>' if self.cluster_marker == NOEPY_HEADER_BE else '<')

class ClusterPackedNamespace:

    def __init__(self, g, cluster_header):
        self.header = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.size = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.type_count = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.class_count = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.class_data_member_count = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.string_table_size = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.default_buffer_count = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.default_buffer_size = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')

class ClusterPackedDataMember:

    def __init__(self, g, cluster_header):
        self.name_offset = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.type_id = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.value_offset = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.size_in_bytes = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.flags = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.fixed_array_size = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.name = ''

class ClusterPackedClassDescriptor:

    def __init__(self, g, cluster_header, class_id):
        self.super_class_id = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.size_in_bytes_and_alignment = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.name_offset = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.class_data_member_count = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.offset_from_parent = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.offset_to_base = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.offset_to_base_in_allocated_block = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.flags = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.default_buffer_offset = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.name = ''
        self.class_id = class_id

    def get_size_in_bytes(self):
        return self.size_in_bytes_and_alignment & 268435455

    def get_alignment(self):
        return 1 << ((self.size_in_bytes_and_alignment & 4026531840) >> 28)

class ClusterHeaderClassChildArray:

    def __init__(self, g, cluster_header):
        self.type_id = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.offset = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.flags = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.count = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')

class ClusterUserFixup:

    def __init__(self, g, cluster_header):
        self.type_id = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.size = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')
        self.offset = read_integer(g, 4, False, '>' if cluster_header.cluster_marker == NOEPY_HEADER_BE else '<')

class ClusterUserFixupResult:

    def __init__(self, g, fixup, type_strings, class_descriptors, Loc):
        self.data_type = get_type(fixup.type_id, type_strings, class_descriptors)
        self.defer = False
        old_position = g.tell()
        g.seek(Loc + fixup.offset)
        if self.data_type == 'PAssetReferenceImport':
            self.user_fixup_type = self.data_type
            self.user_fixup_target_offset = None
            self.defer = True
            self.data_offset = fixup.offset
            self.data_size = fixup.size
            self.refer_type = None
            self.data = read_integer(g, self.data_size, True, '>')
        else:
            self.user_fixup_type = None
            self.user_fixup_target_offset = fixup.offset
            self.data_offset = 0
            self.data_size = 0
            self.refer_type = self.data_type
            self.data = read_null_ending_string(g)
        g.seek(old_position)

class ClusterObjectID:

    def __init__(self):
        self.object_id = 0
        self.object_list = 0

class ClusterBaseFixup:

    def __init__(self):
        self.source_offset_or_member = 0
        self.source_object_id = 0
        self.som = 0

    def unpack_source(self, fixup_buffer):
        som = cluster_variable_length_quantity_unpack(fixup_buffer)
        self.som = som >> 1
        if som & 1 != 0:
            self.source_offset_or_member = som >> 1 | 1 << 31
        else:
            self.source_offset_or_member = som >> 1

    def is_class_data_member(self):
        return self.source_offset_or_member & 1 << 31 == 0

    def unpack(self, fixup_buffer, mask):
        if mask & 1 == 0:
            self.unpack_source(fixup_buffer)
        if mask & 2 == 0:
            self.source_object_id = cluster_variable_length_quantity_unpack(fixup_buffer)

    def set_source_object_id(self, fixup_buffer, sourceObjectID):
        self.source_object_id = sourceObjectID

class ClusterArrayFixup(ClusterBaseFixup):

    def __init__(self):
        super(ClusterArrayFixup, self).__init__()
        self.source_offset_or_member = 0
        self.source_object_id = 0
        self.count = 0
        self.offset = 0
        self.fixup_type = 'Array'

    def unpack_fixup(self, fixup_buffer, mask):
        if mask & 8 == 0:
            self.count = cluster_variable_length_quantity_unpack(fixup_buffer)
        self.offset = cluster_variable_length_quantity_unpack(fixup_buffer)

    def unpack(self, fixup_buffer, mask):
        super(ClusterArrayFixup, self).unpack(fixup_buffer, mask)
        self.unpack_fixup(fixup_buffer, mask)

class ClusterPointerFixup(ClusterBaseFixup):

    def __init__(self):
        super(ClusterPointerFixup, self).__init__()
        self.source_offset_or_member = 0
        self.source_object_id = 0
        self.destination_object = ClusterObjectID()
        self.destination_offset = 0
        self.array_index = 0
        self.user_fixup_id = None
        self.fixup_type = 'Pointer'

    def unpack_fixup(self, fixup_buffer, mask):
        is_user_fixup = False
        if mask & 16 == 0:
            user_fixup_id = cluster_variable_length_quantity_unpack(fixup_buffer)
            is_user_fixup = user_fixup_id != 0
            if is_user_fixup:
                self.user_fixup_id = user_fixup_id - 1
            else:
                self.user_fixup_id = None
        if is_user_fixup != True:
            self.destination_object.object_id = cluster_variable_length_quantity_unpack(fixup_buffer)
            if mask & 32 == 0:
                self.destination_object.object_list = cluster_variable_length_quantity_unpack(fixup_buffer)
            if mask & 64 == 0:
                self.destination_offset = cluster_variable_length_quantity_unpack(fixup_buffer)
        if mask & 8 == 0:
            self.array_index = cluster_variable_length_quantity_unpack(fixup_buffer)

    def unpack(self, fixup_buffer, mask):
        super(ClusterPointerFixup, self).unpack(fixup_buffer, mask)
        self.unpack_fixup(fixup_buffer, mask)

class ClusterFixupUnpacker:

    def __init__(self, unpack_mask, object_count):
        self.unpack_mask = unpack_mask
        self.object_count = object_count

    def unpack_strided(self, template_fixup, fixup_buffer, use_unpack_id):
        object_id = cluster_variable_length_quantity_unpack(fixup_buffer)
        stride = cluster_variable_length_quantity_unpack(fixup_buffer)
        stridedSeriesLength = cluster_variable_length_quantity_unpack(fixup_buffer)
        for i in range(stridedSeriesLength):
            fixup_buffer.set_fixup(template_fixup)
            if use_unpack_id:
                unpack_id(fixup_buffer, object_id, self.unpack_mask)
            else:
                unpack_with_fixup(fixup_buffer, object_id, self.unpack_mask)
            fixup_buffer.next_fixup()
            object_id += stride

    def unpack_all(self, template_fixup, fixup_buffer):
        for i in range(self.object_count):
            fixup_buffer.set_fixup(template_fixup)
            unpack_with_fixup(fixup_buffer, i, self.unpack_mask)
            fixup_buffer.next_fixup()

    def unpack_inclusive(self, template_fixup, fixup_buffer):
        patching_count = cluster_variable_length_quantity_unpack(fixup_buffer)
        for i in range(patching_count):
            next_ = 0
            if self.object_count < 256:
                next_ = fixup_buffer.read()
            else:
                next_ = cluster_variable_length_quantity_unpack(fixup_buffer)
            fixup_buffer.set_fixup(template_fixup)
            unpack_id(fixup_buffer, next_, self.unpack_mask)
            fixup_buffer.next_fixup()
        return patching_count

    def unpack_exclusive(self, template_fixup, fixup_buffer):
        patching_count = cluster_variable_length_quantity_unpack(fixup_buffer)
        last = 0
        for i in range(patching_count):
            next_ = 0
            if self.object_count < 256:
                next_ = fixup_buffer.read()
            else:
                next_ = cluster_variable_length_quantity_unpack(fixup_buffer)
            for o in range(last, next_):
                fixup_buffer.set_fixup(template_fixup)
                unpack_id(fixup_buffer, o, self.unpack_mask)
                fixup_buffer.next_fixup()
            last = next_ + 1
        for o in range(last, self.object_count):
            fixup_buffer.set_fixup(template_fixup)
            unpack_id(fixup_buffer, o, self.unpack_mask)
            fixup_buffer.next_fixup()
        return patching_count

    def unpack_bitmasked(self, template_fixup, fixup_buffer, use_unpack_id):
        bytes_required_as_bit_mask = self.object_count >> 3
        if self.object_count & 7 != 0:
            bytes_required_as_bit_mask += 1
        bit_mask_offset = fixup_buffer.offset
        fixup_buffer.offset += bytes_required_as_bit_mask
        current_bit = 1
        object_id = 0
        while object_id < self.object_count:
            if object_id & 7 == 0:
                current_bit = 1
            bit_mask = fixup_buffer.get_value_at(bit_mask_offset)
            if bit_mask & current_bit != 0:
                fixup_buffer.set_fixup(template_fixup)
                if use_unpack_id:
                    unpack_id(fixup_buffer, object_id, self.unpack_mask)
                else:
                    unpack_with_fixup(fixup_buffer, object_id, self.unpack_mask)
                fixup_buffer.next_fixup()
            if object_id & 7 == 7:
                bit_mask_offset += 1
            else:
                current_bit = current_bit << 1
            object_id += 1

class ClusterProcessTypeInfo:

    def __init__(self, class_descriptor, data_members, type_strings):
        self.class_descriptors = class_descriptor
        self.data_members = data_members
        self.type_strings = type_strings
        self.list_for_class_descriptors = {}
        self.classes_strings = []
        self.import_classes_strings = []

class ClusterProcessListFixupInfo:

    def __init__(self, pointer_array_fixups, pointer_fixups, array_fixups, user_fixup_results):
        self.pointer_array_fixup_offset = 0
        self.pointer_fixup_offset = 0
        self.array_fixup_offset = 0
        self.pointer_array_fixups = pointer_array_fixups
        self.pointer_fixups = pointer_fixups
        self.array_fixups = array_fixups
        self.user_fixup_results = user_fixup_results

    def reset_offset(self):
        self.pointer_array_fixup_offset = 0
        self.pointer_fixup_offset = 0
        self.array_fixup_offset = 0

class FixUpBuffer:

    def __init__(self, g, size, decompressed):
        self.pointer_index = 0
        self.offset = 0
        self.size = size
        self.fixup_buffer = g.read(self.size)
        self.decompressed = decompressed

    def read(self):
        val = self.fixup_buffer[self.offset]
        self.offset += 1
        return val

    def get_value_at(self, index):
        return self.fixup_buffer[index]

    def get_fixup(self):
        return self.decompressed[self.pointer_index]

    def set_fixup(self, fixup):
        self.decompressed[self.pointer_index].source_offset_or_member = fixup.source_offset_or_member
        self.decompressed[self.pointer_index].source_object_id = fixup.source_object_id
        self.decompressed[self.pointer_index].som = fixup.som
        if fixup.fixup_type == 'Array':
            self.decompressed[self.pointer_index].count = fixup.count
            self.decompressed[self.pointer_index].offset = fixup.offset
        elif fixup.fixup_type == 'Pointer':
            if self.decompressed[self.pointer_index].destination_object == None:
                self.decompressed[self.pointer_index].destination_object = ClusterObjectID()
            self.decompressed[self.pointer_index].destination_object.object_id = fixup.destination_object.object_id
            self.decompressed[self.pointer_index].destination_object.object_list = fixup.destination_object.object_list
            self.decompressed[self.pointer_index].destination_offset = fixup.destination_offset
            self.decompressed[self.pointer_index].array_index = fixup.array_index
            self.decompressed[self.pointer_index].user_fixup_id = fixup.user_fixup_id

    def next_fixup(self):
        self.pointer_index += 1

def unpack_with_fixup(fixup_buffer, ID, mask):
    fixup_buffer.get_fixup().set_source_object_id(fixup_buffer, ID)
    fixup_buffer.get_fixup().unpack_fixup(fixup_buffer, mask)

def unpack_id(fixup_buffer, ID, mask):
    fixup_buffer.get_fixup().set_source_object_id(fixup_buffer, ID)

def initialize_fixup_as_template(template_fixup, fixup_buffer, mask):
    if mask & 32 != 0:
        template_fixup.destination_object.object_list = cluster_variable_length_quantity_unpack(fixup_buffer)
    return template_fixup

def cluster_variable_length_quantity_unpack(fixup_buffer):
    by_pass = True
    result = 0
    next_ = 0
    shift = 0
    while next_ & 128 != 0 or by_pass:
        by_pass = False
        next_ = fixup_buffer.read()
        result |= (next_ & 127) << shift
        shift += 7
    return result

def decompress(fixup_buffer, fixup_count, object_count, is_pointer):
    pointer_end = fixup_buffer.pointer_index + fixup_count
    while fixup_buffer.pointer_index < pointer_end:
        pack_type_with_mask = fixup_buffer.read()
        pack_type = pack_type_with_mask & 7
        mask = pack_type_with_mask & ~7
        mask_for_fixups = mask | 1
        if object_count == 1:
            mask_for_fixups |= 2
        template_fixup = None
        if is_pointer:
            template_fixup = ClusterPointerFixup()
        else:
            template_fixup = ClusterArrayFixup()
        template_fixup.unpack_source(fixup_buffer)
        if is_pointer:
            template_fixup = initialize_fixup_as_template(template_fixup, fixup_buffer, mask_for_fixups)
        unpacker = ClusterFixupUnpacker(mask_for_fixups, object_count)
        if pack_type == 0:
            unpacker.unpack_all(template_fixup, fixup_buffer)
        elif pack_type == 2:
            decompressed_with_id_pointer = fixup_buffer.pointer_index
            patching_count = unpacker.unpack_inclusive(template_fixup, fixup_buffer)
            save_pointer = fixup_buffer.pointer_index
            for i in range(patching_count):
                fixup_buffer.pointer_index = decompressed_with_id_pointer
                fixup_buffer.get_fixup().unpack_fixup(fixup_buffer, mask_for_fixups)
                decompressed_with_id_pointer += 1
            fixup_buffer.pointer_index = save_pointer
        elif pack_type == 3:
            decompressed_with_id_pointer = fixup_buffer.pointer_index
            patching_count = unpacker.unpack_exclusive(template_fixup, fixup_buffer)
            inclusive_count = object_count - patching_count
            save_pointer = fixup_buffer.pointer_index
            for i in range(inclusive_count):
                fixup_buffer.pointer_index = decompressed_with_id_pointer
                fixup_buffer.get_fixup().unpack_fixup(fixup_buffer, mask_for_fixups)
                decompressed_with_id_pointer += 1
            fixup_buffer.pointer_index = save_pointer
        elif pack_type == 4:
            unpacker.unpack_bitmasked(template_fixup, fixup_buffer, False)
        elif pack_type == 5:
            patching_count = cluster_variable_length_quantity_unpack(fixup_buffer)
            for i in range(patching_count):
                fixup_buffer.set_fixup(template_fixup)
                fixup_buffer.get_fixup().unpack(fixup_buffer, mask_for_fixups)
                fixup_buffer.next_fixup()
        elif pack_type == 6:
            unpacker.unpack_strided(template_fixup, fixup_buffer, False)
        elif pack_type == 1:
            decompressed_group_end_pointer = fixup_buffer.pointer_index + object_count
            template_fixup_for_target = template_fixup
            while fixup_buffer.pointer_index < decompressed_group_end_pointer:
                pack_type_for_groups = fixup_buffer.read()
                template_fixup_for_target.unpack_fixup(fixup_buffer, mask_for_fixups)
                if pack_type_for_groups == 2:
                    unpacker.unpack_inclusive(template_fixup_for_target, fixup_buffer)
                elif pack_type_for_groups == 3:
                    unpacker.unpack_exclusive(template_fixup_for_target, fixup_buffer)
                elif pack_type_for_groups == 4:
                    unpacker.unpack_bitmasked(template_fixup_for_target, fixup_buffer, True)
                elif pack_type_for_groups == 6:
                    unpacker.unpack_strided(template_fixup_for_target, fixup_buffer, True)

def decompress_fixups(fixup_buffer, instance_list, is_pointer_array, is_pointer):
    for cluster_instance_list_header in instance_list:
        fixup_count = 0
        if is_pointer:
            fixup_count = cluster_instance_list_header['m_pointerFixupCount']
        else:
            fixup_count = cluster_instance_list_header['m_arrayFixupCount']
            if is_pointer_array:
                fixup_count = cluster_instance_list_header['m_pointerArrayFixupCount']
        decompress(fixup_buffer, fixup_count, cluster_instance_list_header['m_count'], is_pointer)
    return fixup_buffer.decompressed

def parse_cluster(filename='', noesis_model=None, storage_media=None):
    type_strings = []
    g = storage_media.open(filename, 'rb')
    g.seek(0)
    cluster_header = ClusterClusterHeader(g)
    g.seek(cluster_header.size)
    name_spaces = ClusterPackedNamespace(g, cluster_header)
    type_ids = memoryview(bytearray(g.read(name_spaces.type_count * 4)))
    if cluster_header.cluster_marker == NOEPY_HEADER_BE:
        bytearray_byteswap(type_ids, 4)
    type_ids = cast_memoryview(memoryview(type_ids), 'i')
    class_member_count = 0
    class_descriptors = [ClusterPackedClassDescriptor(g, cluster_header, i + 1) for i in range(name_spaces.class_count)]
    for class_descriptor in class_descriptors:
        class_descriptor.member_offset = class_member_count
        class_member_count += class_descriptor.class_data_member_count
    class_data_members = [ClusterPackedDataMember(g, cluster_header) for i in range(name_spaces.class_data_member_count)]
    string_table_offset = g.tell()
    for type_id_offset in type_ids:
        g.seek(string_table_offset + type_id_offset)
        type_strings.append(read_null_ending_string(g))
    for class_descriptor in class_descriptors:
        g.seek(string_table_offset + class_descriptor.name_offset)
        class_descriptor.name = read_null_ending_string(g)
    for class_data_member in class_data_members:
        g.seek(string_table_offset + class_data_member.name_offset)
        class_data_member.name = read_null_ending_string(g)
    instance_list_offset = string_table_offset + name_spaces.string_table_size
    cluster_mesh_info = MeshInfo()
    cluster_mesh_info.storage_media = storage_media
    cluster_mesh_info.filename = filename
    cluster_type_info = ClusterProcessTypeInfo(class_descriptors, class_data_members, type_strings)
    for class_descriptor in class_descriptors:
        if class_descriptor.name == 'PClusterHeader':
            g.seek(0)
            process_data_members(g, cluster_type_info, None, class_descriptor.class_id, 0, 0, 0, cluster_mesh_info, class_descriptor.name, False, cluster_mesh_info.cluster_header, cluster_header, None, 0, 0, 0, None, None, None, False)
            break
    instance_list = None
    object_data_offset = None
    for class_descriptor in class_descriptors:
        if class_descriptor.name == 'PInstanceListHeader':
            g.seek(instance_list_offset)
            class_size = get_class_size(cluster_type_info, class_descriptor.class_id)
            object_data_offset = instance_list_offset + cluster_mesh_info.cluster_header['m_instanceListCount'] * class_size
            instance_list = [process_data_members(g, cluster_type_info, None, class_descriptor.class_id, instance_list_offset + class_size * j, 0, j, cluster_mesh_info, class_descriptor.name, False, {}, cluster_header, None, 0, 0, 0, None, None, None, False) for j in range(cluster_mesh_info.cluster_header['m_instanceListCount'])]
            break
    user_fixup_data_offset = object_data_offset + cluster_mesh_info.cluster_header['m_totalDataSize']
    user_fixup_offset = user_fixup_data_offset + cluster_mesh_info.cluster_header['m_userFixupDataSize']
    g.seek(user_fixup_offset)
    user_fixups = [ClusterUserFixup(g, cluster_header) for i in range(cluster_mesh_info.cluster_header['m_userFixupCount'])]
    header_class_ids = bytearray(g.read(cluster_mesh_info.cluster_header['m_headerClassInstanceCount'] * 4))
    if cluster_header.cluster_marker == NOEPY_HEADER_BE:
        bytearray_byteswap(header_class_ids, 4)
    header_class_ids = cast_memoryview(memoryview(header_class_ids), 'i')
    header_class_children = [ClusterHeaderClassChildArray(g, cluster_header) for i in range(cluster_mesh_info.cluster_header['m_headerClassChildCount'])]
    pointer_array_fixup_offset = g.tell()
    pointer_fixup_offset = pointer_array_fixup_offset + cluster_mesh_info.cluster_header['m_pointerArrayFixupSize']
    array_fixup_offset = pointer_fixup_offset + cluster_mesh_info.cluster_header['m_pointerFixupSize']
    cluster_mesh_info.vram_model_data_offset = array_fixup_offset + cluster_mesh_info.cluster_header['m_arrayFixupSize']
    user_fixup_results = [ClusterUserFixupResult(g, fixup, type_strings, class_descriptors, user_fixup_data_offset) for fixup in user_fixups]
    pointer_array_fixups = [ClusterArrayFixup() for i in range(cluster_mesh_info.cluster_header['m_pointerArrayFixupCount'])]
    g.seek(pointer_array_fixup_offset)
    pointer_array_fixups = decompress_fixups(FixUpBuffer(g, cluster_mesh_info.cluster_header['m_pointerArrayFixupSize'], pointer_array_fixups), instance_list, True, False)
    pointer_fixups = [ClusterPointerFixup() for i in range(cluster_mesh_info.cluster_header['m_pointerFixupCount'])]
    g.seek(pointer_fixup_offset)
    pointer_fixups = decompress_fixups(FixUpBuffer(g, cluster_mesh_info.cluster_header['m_pointerFixupSize'], pointer_fixups), instance_list, False, True)
    array_fixups = [ClusterArrayFixup() for i in range(cluster_mesh_info.cluster_header['m_arrayFixupCount'])]
    g.seek(array_fixup_offset)
    array_fixups = decompress_fixups(FixUpBuffer(g, cluster_mesh_info.cluster_header['m_arrayFixupSize'], array_fixups), instance_list, False, False)
    cluster_list_fixup_info = ClusterProcessListFixupInfo(pointer_array_fixups, pointer_fixups, array_fixups, user_fixup_results)
    class_location = object_data_offset
    count_list = 0
    data_instances_by_class = {}
    for cluster_instance_list_header in instance_list:
        g.seek(class_location)
        data_instances = process_cluster_instance_list_header(cluster_instance_list_header, g, count_list, cluster_type_info, cluster_list_fixup_info, cluster_mesh_info, cluster_header, filename, None)
        if data_instances != None:
            data_instances_by_class[get_class_name(cluster_type_info, cluster_instance_list_header['m_classID'])] = data_instances
            data_instances_by_class[count_list] = data_instances
        class_location += cluster_instance_list_header['m_size']
        count_list += 1
    cluster_mesh_info.data_instances_by_class = data_instances_by_class
    cluster_list_fixup_info.reset_offset()
    class_location = object_data_offset
    count_list = 0
    for cluster_instance_list_header in instance_list:
        g.seek(class_location)
        process_cluster_instance_list_header(cluster_instance_list_header, g, count_list, cluster_type_info, cluster_list_fixup_info, cluster_mesh_info, cluster_header, filename, data_instances_by_class)
        class_location += cluster_instance_list_header['m_size']
        count_list += 1
    render_mesh(g, cluster_mesh_info, cluster_header)
    return cluster_mesh_info

def file_is_ed8_pkg(path):
    path = os.path.realpath(path)
    if not os.path.isfile(path):
        return False
    max_offset = 0
    with open(path, 'rb') as f:
        f.seek(0, 2)
        length = f.tell()
        f.seek(0, 0)
        if length <= 4:
            return False
        f.seek(4, io.SEEK_CUR)
        total_file_entries, = struct.unpack('<I', f.read(4))
        if length < 8 + (64 + 4 + 4 + 4 + 4) * total_file_entries:
            return False
        for i in range(total_file_entries):
            file_entry_name, file_entry_uncompressed_size, file_entry_compressed_size, file_entry_offset, file_entry_flags = struct.unpack('<64sIIII', f.read(64 + 4 + 4 + 4 + 4))
            cur_offset = file_entry_offset + file_entry_compressed_size
            if cur_offset > max_offset:
                max_offset = cur_offset
        if length < max_offset:
            return False
    return True

class MeshInfo:

    def __init__(self):
        self.cluster_header = {}
        self.data_instances_by_class = {}
        self.gltf_data = {}
        self.filename = ''
        self.storage_media = None
        self.vram_model_data_offset = 0
        self.bone_names = []

class IStorageMedia:

    def normalize_path_name(self, name):
        raise Exception('This member needs to be overrided')

    def check_existent_storage(self, name):
        raise Exception('This member needs to be overrided')

    def open(self, name, flags):
        raise Exception('This member needs to be overrided')

    def get_list_at(self, name, list_callback):
        raise Exception('This member needs to be overrided')

class TFileMedia(IStorageMedia):

    def __init__(self, basepath):
        basepath = os.path.realpath(basepath)
        if not os.path.isdir(basepath):
            raise Exception('Passed in basepath is not directory')
        self.basepath = basepath

    def normalize_path_name(self, name):
        return os.path.normpath(name)

    def check_existent_storage(self, name):
        return os.path.isfile(self.basepath + '/' + name)

    def open(self, name, flags='rb', **kwargs):
        if 'w' in flags:
            return open(self.basepath + '/' + name, flags, **kwargs)
        else:
            input_data = None
            with open(self.basepath + '/' + name, 'rb') as f:
                input_data = f.read()
            if 'b' in flags:
                return io.BytesIO(input_data, **kwargs)
            else:
                return io.TextIOWrapper(io.BytesIO(input_data), **kwargs)

    def get_list_at(self, name, list_callback):
        llist = sorted(os.listdir(self.basepath))
        for item in llist:
            if list_callback(item):
                break

class TED8PkgMedia(IStorageMedia):

    def __init__(self, path):
        path = os.path.realpath(path)
        if not os.path.isfile(path):
            raise Exception('Passed in path is not file')
        self.path = path
        basepath = os.path.dirname(path)
        if not os.path.isdir(basepath):
            raise Exception('Parent path is not directory')
        self.basepath = basepath
        f = open(path, 'rb')
        self.f = f
        f.seek(4, io.SEEK_CUR)
        package_file_entries = {}
        total_file_entries, = struct.unpack('<I', f.read(4))
        for i in range(total_file_entries):
            file_entry_name, file_entry_uncompressed_size, file_entry_compressed_size, file_entry_offset, file_entry_flags = struct.unpack('<64sIIII', f.read(64 + 4 + 4 + 4 + 4))
            package_file_entries[file_entry_name.rstrip(b'\x00').decode('ASCII')] = [file_entry_offset, file_entry_compressed_size, file_entry_uncompressed_size, file_entry_flags]
        self.file_entries = package_file_entries
        needscommonpkg = False
        for file_entry_name in sorted(package_file_entries.keys()):
            file_entry = package_file_entries[file_entry_name]
            if file_entry[3] & 1 != 0 and file_entry[3] & 8 != 0 and (file_entry[0] == 0) and (file_entry[1] == 0):
                needscommonpkg = True
                break
        commonpkg = None
        if needscommonpkg:
            commonpkg = TED8PkgMedia(basepath + '/common.pkg')
        self.commonpkg = commonpkg

    def normalize_path_name(self, name):
        return os.path.normpath(name)

    def check_existent_storage(self, name):
        return name in self.file_entries

    def open(self, name, flags='rb', **kwargs):
        file_entry = self.file_entries[name]
        if file_entry[3] & 1 != 0 and file_entry[3] & 8 != 0 and (file_entry[0] == 0) and (file_entry[1] == 0):
            return self.commonpkg.open(name, flags, **kwargs)
        self.f.seek(file_entry[0])
        output_data = None
        if file_entry[3] & 2:
            self.f.seek(4, io.SEEK_CUR)
        if file_entry[3] & 4:
            output_data = uncompress_lz4(self.f, file_entry[2], file_entry[1])
        elif file_entry[3] & 8 or file_entry[3] & 16:
            if 'zstandard' in sys.modules:
                output_data = uncompress_zstd(self.f, file_entry[2], file_entry[1])
            else:
                raise Exception('File %s could not be extracted because zstandard module is not installed' % name)
        elif file_entry[3] & 1:
            is_lz4 = True
            compressed_size = file_entry[1]
            if compressed_size >= 8:
                self.f.seek(4, io.SEEK_CUR)
                cms = int.from_bytes(self.f.read(4), byteorder='little')
                self.f.seek(-8, io.SEEK_CUR)
                is_lz4 = cms != compressed_size and compressed_size - cms != 4
            if is_lz4:
                output_data = uncompress_lz4(self.f, file_entry[2], file_entry[1])
            else:
                output_data = uncompress_nislzss(self.f, file_entry[2], file_entry[1])
        else:
            output_data = self.f.read(file_entry[2])
        if 'b' in flags:
            return io.BytesIO(output_data, **kwargs)
        else:
            return io.TextIOWrapper(io.BytesIO(output_data), **kwargs)

    def get_list_at(self, name, list_callback):
        llist = sorted(self.file_entries.keys())
        for item in llist:
            if list_callback(item):
                break

class BytesIOOnCloseHandler(io.BytesIO):

    def __init__(self, *args, **kwargs):
        self.handler = None
        super().__init__(*args, **kwargs)

    def close(self, *args, **kwargs):
        if self.handler != None and (not self.closed):
            self.handler(self.getvalue())
        super().close(*args, **kwargs)

    def set_close_handler(self, handler):
        self.handler = handler

class TSpecialMemoryMedia(IStorageMedia):

    def __init__(self):
        self.file_entries = {}

    def normalize_path_name(self, name):
        return os.path.normpath(name)

    def check_existent_storage(self, name):
        return name in self.file_entries

    def open(self, name, flags='rb', **kwargs):
        if 'b' in flags:
            f = None

            def close_handler(value):
                self.file_entries[name] = value
            if name in self.file_entries:
                f = BytesIOOnCloseHandler(self.file_entries[name])
            else:
                f = BytesIOOnCloseHandler()
            f.set_close_handler(close_handler)
            return f
        else:
            raise Exception('Reading in text mode not supported')

    def get_list_at(self, name, list_callback):
        llist = sorted(self.file_entries.keys())
        for item in llist:
            if list_callback(item):
                break

class TSpecialOverlayMedia(IStorageMedia):

    def __init__(self, path, allowed_write_extensions=None):
        self.storage0 = TFileMedia(os.path.dirname(path))
        self.storage1 = TSpecialMemoryMedia()
        self.storage2 = TED8PkgMedia(path)
        self.allowed_write_extensions = allowed_write_extensions

    def normalize_path_name(self, name):
        return os.path.normpath(name)

    def check_existent_storage(self, name):
        return self.storage1.check_existent_storage(name) or self.storage2.check_existent_storage(name)

    def open(self, name, flags='rb', **kwargs):
        if 'w' in flags:
            has_passthrough_extension = False
            if self.allowed_write_extensions != None:
                for ext in self.allowed_write_extensions:
                    if name.endswith(ext):
                        has_passthrough_extension = True
                        break
            if has_passthrough_extension:
                return self.storage0.open(name, flags, **kwargs)
            return self.storage1.open(name, flags, **kwargs)
        else:
            if self.storage1.check_existent_storage(name):
                return self.storage1.open(name, flags, **kwargs)
            elif self.storage2.check_existent_storage(name):
                return self.storage2.open(name, flags, **kwargs)
            raise Exception('File ' + str(name) + ' not found')

    def get_list_at(self, name, list_callback):
        items = {}

        def xlist_callback(item):
            items[item] = True
        self.storage1.get_list_at('.', xlist_callback)
        self.storage2.get_list_at('.', xlist_callback)
        llist = sorted(items.keys())
        for item in llist:
            if list_callback(item):
                break

def get_texture_size(width, height, bpp, is_dxt):
    current_width = width
    current_height = height
    if is_dxt:
        current_width = current_width + 3 & ~3
        current_height = current_height + 3 & ~3
    return current_width * current_height * bpp // 8

def get_mipmap_offset_and_size(mipmap_level, width, height, texture_format, is_cube_map):
    size_map = {'DXT1': 4, 'DXT3': 8, 'DXT5': 8, 'BC5': 8, 'BC7': 8, 'RGBA8': 32, 'ARGB8': 32, 'L8': 8, 'A8': 8, 'LA88': 16, 'RGBA16F': 64, 'ARGB1555': 16, 'ARGB4444': 16, 'ARGB8_SRGB': 32}
    block_map = ['DXT1', 'DXT3', 'DXT5', 'BC5', 'BC7']
    bpp = size_map[texture_format]
    is_dxt = texture_format in block_map
    offset = 0
    current_mipmap_level = mipmap_level
    current_width = width
    current_height = height
    while current_mipmap_level != 0:
        current_mipmap_level -= 1
        offset += get_texture_size(current_width, current_height, bpp, is_dxt)
        current_width = max(current_width >> 1, 1)
        current_height = max(current_height >> 1, 1)
    if is_dxt:
        current_width = current_width + 3 & ~3
        current_height = current_height + 3 & ~3
    return (offset, current_width * current_height * bpp // 8, current_width, current_height)

def create_texture(g, dict_data, cluster_mesh_info, cluster_header, is_cube_map):
    g.seek(cluster_mesh_info.vram_model_data_offset)
    if is_cube_map:
        image_width = dict_data['m_size']
        image_height = dict_data['m_size']
    else:
        image_width = dict_data['m_width']
        image_height = dict_data['m_height']
    image_data = None
    texture_size = 0
    is_gxt = 'm_mainTextureBufferSize' in cluster_mesh_info.cluster_header or 'm_textureBufferSize' in cluster_mesh_info.cluster_header
    if is_gxt:
        g.seek(64, io.SEEK_CUR)
    for attribute in ['m_sharedVideoMemoryBufferSize', 'm_maxTextureBufferSize', 'm_vramBufferSize', 'm_mainTextureBufferSize', 'm_textureBufferSize']:
        if attribute in cluster_mesh_info.cluster_header:
            texture_size = cluster_mesh_info.cluster_header[attribute]
            break
    if is_gxt:
        if texture_size != 0:
            texture_size -= 64
    if texture_size == 0:
        raise Exception('Unknown cluster header format')
    image_data = g.read(texture_size)
    if len(image_data) != texture_size:
        raise Exception('Unable to read whole data')
    pitch = 0
    if 'm_sharedVideoMemoryBufferSize' in cluster_mesh_info.cluster_header:
        temporary_pitch = GetInfo(struct.unpack('<I', bytes(dict_data['m_texState']['m_buffers']['m_u'][0]['m_gnmTexture']['m_elements'])[16:20])[0], 26, 13) + 1
        if image_width != temporary_pitch:
            pitch = temporary_pitch
    if 'm_sharedVideoMemoryBufferSize' in cluster_mesh_info.cluster_header or is_gxt:
        image_data = Unswizzle(image_data, image_width, image_height, dict_data['m_format'], imageUntileVita if is_gxt else imageUntilePS4, pitch)
    elif 'm_vramBufferSize' in cluster_mesh_info.cluster_header:
        size_map = {'ARGB8': 4, 'RGBA8': 4, 'ARGB4444': 2, 'L8': 1, 'LA8': 2}
        if dict_data['m_format'] in size_map:
            image_data = Unswizzle(image_data, image_width, image_height, dict_data['m_format'], imageUntileMorton, pitch)
    if True:
        png_output_path = cluster_mesh_info.filename.rsplit('.', maxsplit=2)[0] + '.png'
        if True:
            dxgiFormat = None
            decode_callback = None
            if dict_data['m_format'] == 'DXT1' or dict_data['m_format'] == 'BC1':
                dxgiFormat = 71
            elif dict_data['m_format'] == 'DXT3' or dict_data['m_format'] == 'BC2':
                dxgiFormat = 74
            elif dict_data['m_format'] == 'DXT5' or dict_data['m_format'] == 'BC3':
                dxgiFormat = 77
            elif dict_data['m_format'] == 'BC5':
                dxgiFormat = 83
            elif dict_data['m_format'] == 'BC7':
                dxgiFormat = 98
            elif dict_data['m_format'] == 'LA8':
                decode_callback = decode_la8_into_abgr8
            elif dict_data['m_format'] == 'L8':
                decode_callback = decode_l8_into_abgr8
            elif dict_data['m_format'] == 'ARGB8' or dict_data['m_format'] == 'ARGB8_SRGB':
                decode_callback = decode_argb8_into_agbr8
            elif dict_data['m_format'] == 'RGBA8':
                decode_callback = decode_rgba8_into_abgr8
            elif dict_data['m_format'] == 'RGB565':
                decode_callback = decode_rgb565_into_abgr8
            elif dict_data['m_format'] == 'ARGB4444':
                decode_callback = decode_argb4444_into_abgr8
            else:
                raise Exception('Unhandled format ' + dict_data['m_format'] + ' for PNG conversion')
            if dxgiFormat != None:
                decode_callback = decode_block_into_abgr8
            zfio = io.BytesIO()
            zfio.write(image_data)
            zfio.seek(0)
            rgba_image_data = decode_callback(zfio, image_width, image_height, dxgiFormat)
            with cluster_mesh_info.storage_media.open(png_output_path, 'wb') as f:
                import zlib
                f.write(b'\x89PNG\r\n\x1a\n')

                def write_png_chunk(wf, ident, d):
                    wf.write(len(d).to_bytes(4, byteorder='big'))
                    wf.write(ident[0:4])
                    wf.write(d)
                    wf.write(zlib.crc32(d, zlib.crc32(ident[0:4])).to_bytes(4, byteorder='big'))
                ihdr_str = struct.pack('>IIBBBBB', image_width, image_height, 8, 6, 0, 0, 0)
                write_png_chunk(f, b'IHDR', ihdr_str)
                cbio = io.BytesIO()
                cobj = zlib.compressobj(level=1)
                for row in range(image_height):
                    cbio.write(cobj.compress(b'\x00'))
                    out_offset = row * image_width * 4
                    cbio.write(cobj.compress(rgba_image_data[out_offset:out_offset + image_width * 4]))
                cbio.write(cobj.flush())
                write_png_chunk(f, b'IDAT', cbio.getbuffer())
                write_png_chunk(f, b'IEND', b'')

def load_texture(dict_data, cluster_mesh_info):
    dds_basename = os.path.basename(dict_data['m_id']['m_buffer'])
    found_basename = []

    def list_callback(item):
        if item[:-6] == dds_basename:
            found_basename.append(item)
            return True
    cluster_mesh_info.storage_media.get_list_at('.', list_callback)
    loaded_texture = False
    if len(found_basename) > 0:
        parse_cluster(found_basename[0], None, cluster_mesh_info.storage_media)
        loaded_texture = True

def load_materials_with_actual_name(dict_data, cluster_mesh_info):
    if type(dict_data['m_effectVariant']) == dict and 'm_id' in dict_data['m_effectVariant']:
        dict_data['mu_compiledShaderName'] = dict_data['m_effectVariant']['m_id']['m_buffer']

def load_shader_parameters(g, dict_data, cluster_header):
    if 'mu_shaderParameters' in dict_data:
        return
    old_position = g.tell()
    g.seek(dict_data['mu_memberLoc'])
    parameter_buffer = g.read(dict_data['m_parameterBufferSize'])
    g.seek(old_position)
    shader_parameters = {}
    for shaderParameterDefinition in dict_data['m_tweakableShaderParameterDefinitions']['m_els']:
        parameter_offset = shaderParameterDefinition['m_bufferLoc']['m_offset']
        parameter_size = shaderParameterDefinition['m_bufferLoc']['m_size']
        if shaderParameterDefinition['m_parameterType'] == 66 or shaderParameterDefinition['m_parameterType'] == 68:
            arr = bytearray(parameter_buffer[parameter_offset:parameter_offset + parameter_size])
            if cluster_header.cluster_marker == NOEPY_HEADER_BE:
                bytearray_byteswap(arr, 4)
            arr = cast_memoryview(memoryview(arr), 'I')
            shader_parameters[shaderParameterDefinition['m_name']['m_buffer']] = arr
            if shaderParameterDefinition['m_name']['m_buffer'] in dict_data['m_tweakableShaderParameterDefinitions']['mu_object_references']:
                shader_parameters[shaderParameterDefinition['m_name']['m_buffer']] = dict_data['m_tweakableShaderParameterDefinitions']['mu_object_references'][shaderParameterDefinition['m_name']['m_buffer']]['m_id']['m_buffer']
        elif shaderParameterDefinition['m_parameterType'] == 71:
            arr = bytearray(parameter_buffer[parameter_offset:parameter_offset + parameter_size])
            if cluster_header.cluster_marker == NOEPY_HEADER_BE:
                bytearray_byteswap(arr, 4)
            arr = cast_memoryview(memoryview(arr), 'I')
            shader_parameters[shaderParameterDefinition['m_name']['m_buffer']] = arr
            if shaderParameterDefinition['m_name']['m_buffer'] in dict_data['m_tweakableShaderParameterDefinitions']['mu_object_references']:
                shader_parameters[shaderParameterDefinition['m_name']['m_buffer']] = dict_data['m_tweakableShaderParameterDefinitions']['mu_object_references'][shaderParameterDefinition['m_name']['m_buffer']]
        elif parameter_size == 24:
            shader_parameters[shaderParameterDefinition['m_name']['m_buffer']] = struct.unpack('IIQQ', parameter_buffer[parameter_offset:parameter_offset + parameter_size])
        elif parameter_size % 4 == 0:
            arr = bytearray(parameter_buffer[parameter_offset:parameter_offset + parameter_size])
            if cluster_header.cluster_marker == NOEPY_HEADER_BE:
                bytearray_byteswap(arr, 4)
            arr = cast_memoryview(memoryview(arr), 'f')
            shader_parameters[shaderParameterDefinition['m_name']['m_buffer']] = arr
        else:
            shader_parameters[shaderParameterDefinition['m_name']['m_buffer']] = parameter_buffer[parameter_offset:parameter_offset + parameter_size]
    dict_data['mu_shaderParameters'] = shader_parameters

def multiply_array_as_4x4_matrix(arra, arrb):
    newarr = cast_memoryview(memoryview(bytearray(cast_memoryview(memoryview(arra), 'B'))), 'f')
    for i in range(4):
        for j in range(4):
            newarr[i * 4 + j] = 0 + arrb[i * 4 + 0] * arra[j + 0] + arrb[i * 4 + 1] * arra[j + 4] + arrb[i * 4 + 2] * arra[j + 8] + arrb[i * 4 + 3] * arra[j + 12]
    return newarr

def invert_matrix_44(m):
    inv = cast_memoryview(memoryview(bytearray(cast_memoryview(memoryview(m), 'B'))), 'f')
    inv[0] = m[5] * m[10] * m[15] - m[5] * m[11] * m[14] - m[9] * m[6] * m[15] + m[9] * m[7] * m[14] + m[13] * m[6] * m[11] - m[13] * m[7] * m[10]
    inv[1] = -m[1] * m[10] * m[15] + m[1] * m[11] * m[14] + m[9] * m[2] * m[15] - m[9] * m[3] * m[14] - m[13] * m[2] * m[11] + m[13] * m[3] * m[10]
    inv[2] = m[1] * m[6] * m[15] - m[1] * m[7] * m[14] - m[5] * m[2] * m[15] + m[5] * m[3] * m[14] + m[13] * m[2] * m[7] - m[13] * m[3] * m[6]
    inv[3] = -m[1] * m[6] * m[11] + m[1] * m[7] * m[10] + m[5] * m[2] * m[11] - m[5] * m[3] * m[10] - m[9] * m[2] * m[7] + m[9] * m[3] * m[6]
    inv[4] = -m[4] * m[10] * m[15] + m[4] * m[11] * m[14] + m[8] * m[6] * m[15] - m[8] * m[7] * m[14] - m[12] * m[6] * m[11] + m[12] * m[7] * m[10]
    inv[5] = m[0] * m[10] * m[15] - m[0] * m[11] * m[14] - m[8] * m[2] * m[15] + m[8] * m[3] * m[14] + m[12] * m[2] * m[11] - m[12] * m[3] * m[10]
    inv[6] = -m[0] * m[6] * m[15] + m[0] * m[7] * m[14] + m[4] * m[2] * m[15] - m[4] * m[3] * m[14] - m[12] * m[2] * m[7] + m[12] * m[3] * m[6]
    inv[7] = m[0] * m[6] * m[11] - m[0] * m[7] * m[10] - m[4] * m[2] * m[11] + m[4] * m[3] * m[10] + m[8] * m[2] * m[7] - m[8] * m[3] * m[6]
    inv[8] = m[4] * m[9] * m[15] - m[4] * m[11] * m[13] - m[8] * m[5] * m[15] + m[8] * m[7] * m[13] + m[12] * m[5] * m[11] - m[12] * m[7] * m[9]
    inv[9] = -m[0] * m[9] * m[15] + m[0] * m[11] * m[13] + m[8] * m[1] * m[15] - m[8] * m[3] * m[13] - m[12] * m[1] * m[11] + m[12] * m[3] * m[9]
    inv[10] = m[0] * m[5] * m[15] - m[0] * m[7] * m[13] - m[4] * m[1] * m[15] + m[4] * m[3] * m[13] + m[12] * m[1] * m[7] - m[12] * m[3] * m[5]
    inv[11] = -m[0] * m[5] * m[11] + m[0] * m[7] * m[9] + m[4] * m[1] * m[11] - m[4] * m[3] * m[9] - m[8] * m[1] * m[7] + m[8] * m[3] * m[5]
    inv[12] = -m[4] * m[9] * m[14] + m[4] * m[10] * m[13] + m[8] * m[5] * m[14] - m[8] * m[6] * m[13] - m[12] * m[5] * m[10] + m[12] * m[6] * m[9]
    inv[13] = m[0] * m[9] * m[14] - m[0] * m[10] * m[13] - m[8] * m[1] * m[14] + m[8] * m[2] * m[13] + m[12] * m[1] * m[10] - m[12] * m[2] * m[9]
    inv[14] = -m[0] * m[5] * m[14] + m[0] * m[6] * m[13] + m[4] * m[1] * m[14] - m[4] * m[2] * m[13] - m[12] * m[1] * m[6] + m[12] * m[2] * m[5]
    inv[15] = m[0] * m[5] * m[10] - m[0] * m[6] * m[9] - m[4] * m[1] * m[10] + m[4] * m[2] * m[9] + m[8] * m[1] * m[6] - m[8] * m[2] * m[5]
    det = m[0] * inv[0] + m[1] * inv[4] + m[2] * inv[8] + m[3] * inv[12]
    if det == 0:
        return None
    det = 1.0 / det
    for i in range(16):
        inv[i] *= det
    return inv

def dot_product_vector3(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

def mul_vector3_vector3_float(r, a, f):
    r[0] = a[0] * f
    r[1] = a[1] * f
    r[2] = a[2] * f

def zero_vector3(r):
    r[0] = 0.0
    r[1] = 0.0
    r[2] = 0.0

def normalize_v3_v3_length(r, a, unit_length=1.0):
    d = dot_product_vector3(a, a)
    if d > 1e-35:
        d = d ** 0.5
        mul_vector3_vector3_float(r, a, unit_length / d)
    else:
        zero_vector3(r)
        d = 0.0
    return d

def normalize_matrix_44(m):
    norm = cast_memoryview(memoryview(bytearray(cast_memoryview(memoryview(m), 'B'))), 'f')
    norm[0:15] = m[0:15]
    for i in range(3):
        tmp_v3 = array.array('f')
        tmp_v3.extend(norm[0 + i * 4:3 + i * 4])
        normalize_v3_v3_length(tmp_v3, tmp_v3, 1.0)
        norm[0 + i * 4:3 + i * 4] = tmp_v3
    return norm

def decompose_matrix_44(mat, translation, rotation, scale):
    m00 = mat[0]
    m01 = mat[1]
    m02 = mat[2]
    m03 = mat[3]
    m10 = mat[4]
    m11 = mat[5]
    m12 = mat[6]
    m13 = mat[7]
    m20 = mat[8]
    m21 = mat[9]
    m22 = mat[10]
    m23 = mat[11]
    m30 = mat[12]
    m31 = mat[13]
    m32 = mat[14]
    m33 = mat[15]
    translation[0] = m30
    translation[1] = m31
    translation[2] = m32
    scale[0] = (m00 ** 2 + m10 ** 2 + m20 ** 2) ** 0.5
    scale[1] = (m01 ** 2 + m11 ** 2 + m21 ** 2) ** 0.5
    scale[2] = (m02 ** 2 + m12 ** 2 + m22 ** 2) ** 0.5
    mat = normalize_matrix_44(mat)
    m00 = mat[0]
    m01 = mat[1]
    m02 = mat[2]
    m03 = mat[3]
    m10 = mat[4]
    m11 = mat[5]
    m12 = mat[6]
    m13 = mat[7]
    m20 = mat[8]
    m21 = mat[9]
    m22 = mat[10]
    m23 = mat[11]
    m30 = mat[12]
    m31 = mat[13]
    m32 = mat[14]
    m33 = mat[15]
    tr = 0.25 * (1.0 + m00 + m11 + m22)
    if tr > 0.0001:
        s = tr ** 0.5
        rotation[3] = s
        s = 1.0 / (4.0 * s)
        rotation[0] = (m12 - m21) * s
        rotation[1] = (m20 - m02) * s
        rotation[2] = (m01 - m10) * s
    elif m00 > m11 and m00 > m22:
        s = 2.0 * (1.0 + m00 - m11 - m22) ** 0.5
        rotation[0] = 0.25 * s
        s = 1.0 / s
        rotation[3] = (m12 - m21) * s
        rotation[1] = (m10 + m01) * s
        rotation[2] = (m20 + m02) * s
    elif m11 > m22:
        s = 2.0 * (1.0 + m11 - m00 - m22) ** 0.5
        rotation[1] = 0.25 * s
        s = 1.0 / s
        rotation[3] = (m20 - m02) * s
        rotation[0] = (m10 + m01) * s
        rotation[2] = (m21 + m12) * s
    else:
        s = 2.0 * (1.0 + m22 - m00 - m11) ** 0.5
        rotation[2] = 0.25 * s
        s = 1.0 / s
        rotation[3] = (m01 - m10) * s
        rotation[0] = (m20 + m02) * s
        rotation[1] = (m21 + m12) * s
    rot_len = (rotation[0] * rotation[0] + rotation[1] * rotation[1] + rotation[2] * rotation[2] + rotation[3] * rotation[3]) ** 0.5
    if rot_len != 0.0:
        f = 1.0 / rot_len
        for i in range(len(rotation)):
            rotation[i] *= f
    else:
        rotation[0] = 0.0
        rotation[1] = 0.0
        rotation[2] = 0.0
        rotation[3] = 1.0

def derive_matrix_44(dic, mat):
    translation = array.array('f')
    translation.extend([0, 0, 0])
    dic['mu_translation'] = translation
    rotation = array.array('f')
    rotation.extend([0, 0, 0, 0])
    dic['mu_rotation'] = rotation
    scale = array.array('f')
    scale.extend([0, 0, 0])
    dic['mu_scale'] = scale
    decompose_matrix_44(mat, translation, rotation, scale)
dataTypeMappingForGltf = {0: 5126, 4: 5131, 8: 5125, 12: 5123, 16: 5121, 20: 5123, 24: 5121, 28: 5124, 32: 5123, 36: 5121, 40: 5123, 44: 5121}
dataTypeMappingForPython = {0: 'f', 4: 'e', 8: 'I', 12: 'H', 16: 'B', 20: 'H', 24: 'B', 28: 'i', 32: 'h', 36: 'b', 40: 'h', 44: 'b'}
dataTypeMappingNonstandardRemapForGltf = {4: 0, 28: 0}
dataTypeMappingNormalizationMultiplier = {20: 65535, 24: 255, 40: 32767, 44: 127}
dataTypeMappingPrimitiveRemap = {0: 0, 1: 0, 2: 0, 3: 0, 4: 4, 5: 4, 6: 4, 7: 4, 8: 8, 9: 8, 10: 8, 11: 8, 12: 12, 13: 12, 14: 12, 15: 12, 16: 16, 17: 16, 18: 16, 19: 16, 20: 20, 21: 20, 22: 20, 23: 20, 24: 24, 25: 24, 26: 24, 27: 24, 28: 28, 29: 28, 30: 28, 31: 28, 32: 32, 33: 32, 34: 32, 35: 32, 36: 36, 37: 36, 38: 36, 39: 36, 40: 40, 41: 40, 42: 40, 43: 40, 44: 44, 45: 44, 46: 44, 47: 44}
dataTypeCountMappingForGltf = {0: 'SCALAR', 1: 'VEC2', 2: 'VEC3', 3: 'VEC4'}

def render_mesh(g, cluster_mesh_info, cluster_header):
    if 'PTexture2D' in cluster_mesh_info.data_instances_by_class:
        for texture2d in cluster_mesh_info.data_instances_by_class['PTexture2D']:
            create_texture(g, texture2d, cluster_mesh_info, cluster_header, False)
    if 'PTextureCubeMap' in cluster_mesh_info.data_instances_by_class:
        for textureCubeMap in cluster_mesh_info.data_instances_by_class['PTextureCubeMap']:
            create_texture(g, textureCubeMap, cluster_mesh_info, cluster_header, True)
    if 'PAssetReferenceImport' in cluster_mesh_info.data_instances_by_class:
        for assetReferenceImport in cluster_mesh_info.data_instances_by_class['PAssetReferenceImport']:
            if assetReferenceImport['m_targetAssetType'] == 'PTexture2D' or assetReferenceImport['m_targetAssetType'] == 'PTextureCubeMap':
                load_texture(assetReferenceImport, cluster_mesh_info)
    if 'PParameterBuffer' in cluster_mesh_info.data_instances_by_class:
        for k in cluster_mesh_info.data_instances_by_class.keys():
            has_key = False
            if type(k) == int:
                data_instances = cluster_mesh_info.data_instances_by_class[k]
                if len(data_instances) > 0:
                    if data_instances[0]['mu_memberClass'] == 'PParameterBuffer':
                        has_key = True
            if has_key == True:
                for parameterBuffer in cluster_mesh_info.data_instances_by_class[k]:
                    load_shader_parameters(g, parameterBuffer, cluster_header)
    clsuter_basename_noext = cluster_mesh_info.filename.split('.', 1)[0]
    if 'PMaterial' in cluster_mesh_info.data_instances_by_class:
        import hashlib
        for material in cluster_mesh_info.data_instances_by_class['PMaterial']:
            load_materials_with_actual_name(material, cluster_mesh_info)
            if 'mu_name' in material:
                material['mu_materialname'] = material['mu_name']
    pdatablock_list = []
    if 'PDataBlock' in cluster_mesh_info.data_instances_by_class:
        pdatablock_list = cluster_mesh_info.data_instances_by_class['PDataBlock']
    else:
        for class_name in cluster_mesh_info.data_instances_by_class.keys():
            if type(class_name) == str and class_name.startswith('PDataBlock'):
                pdatablock_list = cluster_mesh_info.data_instances_by_class[class_name]
                break
    g.seek(cluster_mesh_info.vram_model_data_offset)
    indvertbuffer = memoryview(g.read())
    indvertbuffercache = {}
    if 'PMeshSegment' in cluster_mesh_info.data_instances_by_class:
        for meshSegment in cluster_mesh_info.data_instances_by_class['PMeshSegment']:
            if 'm_mappableBuffers' in meshSegment['m_indexData']:
                meshSegment['mu_indBufferPosition'] = meshSegment['m_indexData']['m_mappableBuffers']['m_offsetInAllocatedBuffer']
                meshSegment['mu_indBufferSize'] = meshSegment['m_indexData']['m_dataSize']
            else:
                meshSegment['mu_indBufferPosition'] = meshSegment['m_indexData']['m_offsetInIndexBuffer']
                meshSegment['mu_indBufferSize'] = meshSegment['m_indexData']['m_dataSize']
            cachekey = meshSegment['mu_indBufferPosition'].to_bytes(4, byteorder='little') + meshSegment['mu_indBufferSize'].to_bytes(4, byteorder='little')
            if cachekey not in indvertbuffercache:
                indvertbuffercache[cachekey] = bytes(cast_memoryview(indvertbuffer[meshSegment['mu_indBufferPosition']:meshSegment['mu_indBufferPosition'] + meshSegment['mu_indBufferSize']], 'B'))
            meshSegment['mu_indBuffer'] = indvertbuffercache[cachekey]
    for vertexData in pdatablock_list:
        for streamInfo in vertexData['m_streams']['m_els']:
            if 'm_mappableBuffers' in vertexData:
                streamInfo['mu_vertBufferPosition'] = vertexData['m_mappableBuffers']['m_offsetInAllocatedBuffer'] + streamInfo['m_offset']
                streamInfo['mu_vertBufferSize'] = vertexData['m_mappableBuffers']['m_strideInAllocatedBuffer']
            elif 'm_indexBufferSize' in cluster_mesh_info.cluster_header:
                streamInfo['mu_vertBufferPosition'] = cluster_mesh_info.cluster_header['m_indexBufferSize'] + vertexData['m_offsetInVertexBuffer'] + streamInfo['m_offset']
                streamInfo['mu_vertBufferSize'] = vertexData['m_dataSize']
            cachekey = streamInfo['mu_vertBufferPosition'].to_bytes(4, byteorder='little') + streamInfo['mu_vertBufferSize'].to_bytes(4, byteorder='little')
            if cachekey not in indvertbuffercache:
                indvertbuffercache[cachekey] = bytes(cast_memoryview(indvertbuffer[streamInfo['mu_vertBufferPosition']:streamInfo['mu_vertBufferPosition'] + streamInfo['mu_vertBufferSize']], 'B'))
            streamInfo['mu_vertBuffer'] = indvertbuffercache[cachekey]
    if True:
        cur_min = float('inf')
        cur_max = float('-inf')
        if 'PAnimationChannelTimes' in cluster_mesh_info.data_instances_by_class:
            for animationChannelTime in cluster_mesh_info.data_instances_by_class['PAnimationChannelTimes']:
                timestamps = cast_memoryview(memoryview(bytearray(cast_memoryview(animationChannelTime['m_timeKeys']['m_els'][:animationChannelTime['m_keyCount']], 'B'))), 'f')
                animationChannelTime['mu_animation_timestamps'] = timestamps
                for timestamp in timestamps:
                    if timestamp < cur_min:
                        cur_min = timestamp
                    if timestamp > cur_max:
                        cur_max = timestamp
        if 'PAnimationClip' in cluster_mesh_info.data_instances_by_class:
            for animationClip in cluster_mesh_info.data_instances_by_class['PAnimationClip']:
                timestamps = cast_memoryview(memoryview(bytearray(2 * 4)), 'f')
                timestamps[0] = animationClip['m_constantChannelStartTime']
                timestamps[1] = animationClip['m_constantChannelEndTime']
                animationClip['mu_animation_timestamps'] = timestamps
                for timestamp in timestamps:
                    if timestamp < cur_min:
                        cur_min = timestamp
                    if timestamp > cur_max:
                        cur_max = timestamp
    map_bone_name_to_matrix = {}
    if 'PMesh' in cluster_mesh_info.data_instances_by_class:
        data_instances = cluster_mesh_info.data_instances_by_class['PMesh']
        for mesh in cluster_mesh_info.data_instances_by_class['PMesh']:
            bonePosePtr = mesh['m_defaultPose']['m_els']
            bonePoseName = mesh['m_matrixNames']['m_els']
            bonePoseInd = mesh['m_matrixParents']['m_els']
            boneSkelMat = mesh['m_skeletonMatrices']['m_els']
            boneSkelBounds = mesh['m_skeletonBounds']['m_els']
            boneSkelMap = {}
            boneSkelInverseMap = {}
            matrix_hierarchy_only_indices = []
            if boneSkelBounds != None and len(boneSkelBounds) > 0 and (type(boneSkelBounds) != int) and ('m_els' not in boneSkelMat):
                bone_hierarchy_indices = []
                for i in range(len(boneSkelBounds)):
                    hierarchy_matrix_index = boneSkelBounds[i]['m_hierarchyMatrixIndex']
                    inverse_bind_matrix_data = boneSkelMat[i]['m_elements']
                    bone_hierarchy_indices.append(hierarchy_matrix_index)
                    matrix_inverted = invert_matrix_44(inverse_bind_matrix_data)
                    if matrix_inverted != None:
                        boneSkelMap[hierarchy_matrix_index] = matrix_inverted
                        boneSkelInverseMap[hierarchy_matrix_index] = inverse_bind_matrix_data
                matrix_hierarchy_only_indices = [i for i in range(len(boneSkelMat)) if i not in bone_hierarchy_indices]
            hierarchy_additional_inverse_bind_matrices = []
            hierarchy_additional_names = []
            if len(bonePosePtr) > 0 and 'm_els' not in bonePosePtr and (type(bonePosePtr[0]) != int):
                skinMat = [bonePosePtr[i]['m_elements'] for i in range(len(bonePosePtr))]
                skinReducedMatrix = {}
                skinRootName = None
                if True:
                    jump_count = 0
                    jump_count_max = len(boneSkelBounds)
                    cur_parent_index = len(boneSkelBounds) - 1
                    while cur_parent_index >= 0 and jump_count < jump_count_max:
                        if cur_parent_index == bonePoseInd[cur_parent_index]:
                            break
                        nex_parent_index = bonePoseInd[cur_parent_index]
                        if nex_parent_index < 0:
                            break
                        cur_parent_index = nex_parent_index
                    if cur_parent_index >= 0 and len(bonePoseName) > cur_parent_index:
                        skinRootName = bonePoseName[cur_parent_index]['m_buffer']
                for sm in range(len(skinMat)):
                    pm = bonePoseInd[sm]
                    pn = 'TERoots'
                    if pm >= 0 and len(bonePoseName) > pm:
                        pn = bonePoseName[pm]['m_buffer']
                    bn = 'TERoots'
                    if sm >= 0 and len(bonePoseName) > sm:
                        bn = bonePoseName[sm]['m_buffer']
                    cur_matrix = skinMat[sm]
                    cur_reduced_matrix = None
                    if sm in boneSkelMap:
                        cur_matrix = boneSkelMap[sm]
                        if pm >= 0 and pm in boneSkelInverseMap:
                            cur_reduced_matrix = multiply_array_as_4x4_matrix(boneSkelInverseMap[pm], cur_matrix)
                    else:
                        jump_count = 0
                        jump_count_max = len(boneSkelBounds)
                        cur_parent_index = pm
                        while cur_parent_index != -1 and len(skinMat) > cur_parent_index and (jump_count < jump_count_max):
                            cur_parent_mat = skinMat[cur_parent_index]
                            if cur_parent_index in boneSkelMap:
                                cur_parent_mat = boneSkelMap[cur_parent_index]
                                cur_matrix = multiply_array_as_4x4_matrix(cur_parent_mat, cur_matrix)
                                break
                            cur_matrix = multiply_array_as_4x4_matrix(cur_parent_mat, cur_matrix)
                            if cur_parent_index == bonePoseInd[cur_parent_index]:
                                break
                            cur_parent_index = bonePoseInd[cur_parent_index]
                    cluster_mesh_info.bone_names.append(bn)
                    if cur_reduced_matrix != None:
                        skinReducedMatrix[bn] = cur_reduced_matrix
                    if sm in matrix_hierarchy_only_indices and bn != '':
                        hierarchy_additional_inverse_bind_matrices.append(invert_matrix_44(cur_matrix))
                        hierarchy_additional_names.append(bn)
                mesh['mu_reduced_matrix'] = skinReducedMatrix
                mesh['mu_root_matrix_name'] = skinRootName
                mesh['mu_hierarchy_additional_inverse_bind_matrices'] = hierarchy_additional_inverse_bind_matrices
                mesh['mu_hierarchy_additional_names'] = hierarchy_additional_names
            if type(mesh['m_meshSegments']['m_els']) == list:
                for m in mesh['m_meshSegments']['m_els']:
                    boneRemapForHierarchy = cast_memoryview(memoryview(bytearray(len(m['m_skinBones']['m_els']) * 2)), 'H')
                    boneRemapForSkeleton = cast_memoryview(memoryview(bytearray(len(m['m_skinBones']['m_els']) * 2)), 'H')
                    if len(bonePosePtr) > 0 and 'm_els' not in bonePosePtr and (len(m['m_skinBones']['m_els']) > 0) and (type(m['m_skinBones']['m_els'][0]) != int):
                        for i in range(len(m['m_skinBones']['m_els'])):
                            sb = m['m_skinBones']['m_els'][i]
                            boneRemapForHierarchy[i] = sb['m_hierarchyMatrixIndex']
                            boneRemapForSkeleton[i] = sb['m_skeletonMatrixIndex']
                    for vertexData in m['m_vertexData']['m_els']:
                        for streamInfo in vertexData['m_streams']['m_els']:
                            renderDataType = streamInfo['m_renderDataType']
                            datatype = streamInfo['m_type']
                            datatyperemapped = dataTypeMappingPrimitiveRemap[datatype]
                            datatypepython = dataTypeMappingForPython[datatyperemapped]
                            dataTypeCount = datatype % 4 + 1
                            blobdata = streamInfo['mu_vertBuffer']
                            singleelementsize = struct.calcsize(datatypepython)
                            blobstride = vertexData['m_stride']
                            elementcount = vertexData['m_elementCount']
                            if renderDataType in ['SkinIndices']:
                                if dataTypeCount * singleelementsize != blobstride:
                                    deinterleaved_stride = singleelementsize * dataTypeCount
                                    deinterleaved_data = memoryview(bytearray(deinterleaved_stride * elementcount))
                                    for i in range(elementcount):
                                        deinterleaved_data[deinterleaved_stride * i:deinterleaved_stride * (i + 1)] = blobdata[blobstride * i:blobstride * i + deinterleaved_stride]
                                    blobstride = dataTypeCount * singleelementsize
                                    blobdata = bytes(deinterleaved_data)
                                elif dataTypeCount * singleelementsize * elementcount != len(blobdata):
                                    blobdata = blobdata[0:dataTypeCount * singleelementsize * elementcount]
                                if cluster_header.cluster_marker == NOEPY_HEADER_BE:
                                    blobdatabyteswap = bytearray(blobdata)
                                    bytearray_byteswap(blobdatabyteswap, singleelementsize)
                                    blobdata = blobdatabyteswap
                                skinInd = cast_memoryview(memoryview(blobdata), datatypepython)
                                if len(boneRemapForHierarchy) > 0:
                                    remapIndForHierarchy = cast_memoryview(memoryview(bytearray(len(skinInd) * 2)), 'H')
                                    for i in range(len(skinInd)):
                                        mb = skinInd[i]
                                        if mb < len(boneRemapForHierarchy):
                                            remapIndForHierarchy[i] = boneRemapForHierarchy[mb]
                                    streamInfo['mu_remappedVertBufferHierarchy'] = bytes(cast_memoryview(remapIndForHierarchy, 'B'))
                                if len(boneRemapForSkeleton) > 0:
                                    remapIndForSkeleton = cast_memoryview(memoryview(bytearray(len(skinInd) * 2)), 'H')
                                    for i in range(len(skinInd)):
                                        mb = skinInd[i]
                                        if mb < len(boneRemapForSkeleton):
                                            remapIndForSkeleton[i] = boneRemapForSkeleton[mb]
                                    streamInfo['mu_remappedVertBufferSkeleton'] = bytes(cast_memoryview(remapIndForSkeleton, 'B'))
                            elif renderDataType in ['Color']:
                                if True:
                                    if datatyperemapped == 0:
                                        if dataTypeCount * singleelementsize != blobstride:
                                            deinterleaved_stride = singleelementsize * dataTypeCount
                                            deinterleaved_data = memoryview(bytearray(deinterleaved_stride * elementcount))
                                            for i in range(elementcount):
                                                deinterleaved_data[deinterleaved_stride * i:deinterleaved_stride * (i + 1)] = blobdata[blobstride * i:blobstride * i + deinterleaved_stride]
                                            blobstride = dataTypeCount * singleelementsize
                                            blobdata = bytes(deinterleaved_data)
                                        elif dataTypeCount * singleelementsize * elementcount != len(blobdata):
                                            blobdata = blobdata[0:dataTypeCount * singleelementsize * elementcount]
                                        if cluster_header.cluster_marker == NOEPY_HEADER_BE:
                                            blobdatabyteswap = bytearray(blobdata)
                                            bytearray_byteswap(blobdatabyteswap, singleelementsize)
                                            blobdata = blobdatabyteswap
                                        unconverted_data = cast_memoryview(memoryview(blobdata), datatypepython)
                                        converted_data = cast_memoryview(memoryview(bytearray(elementcount * 4 * 4)), 'f')
                                        for i in range(elementcount):
                                            for ii in range(3):
                                                c = converted_data[i * dataTypeCount + ii]
                                                if c < 0.04045:
                                                    if c < 0.0:
                                                        c = 0.0
                                                    else:
                                                        c *= 1.0 / 12.92
                                                else:
                                                    c = ((c + 0.055) * (1.0 / 1.055)) ** 2.4
                                                converted_data[i * 4 + ii] = c
                                                converted_data[i * 4 + ii] = unconverted_data[i * dataTypeCount + ii]
                                            if dataTypeCount == 3:
                                                converted_data[i * 4 + 3] = 1
                                            else:
                                                converted_data[i * 4 + 3] = unconverted_data[i * dataTypeCount + 3]
                                        blobstride = 4 * singleelementsize
                                        blobdata = bytes(cast_memoryview(converted_data, 'B'))
                                        streamInfo['mu_convertedColor'] = blobdata
    if 'PNode' in cluster_mesh_info.data_instances_by_class:
        for node in cluster_mesh_info.data_instances_by_class['PNode']:
            node['mu_matrixToUse'] = node['m_localMatrix']['m_elements']

    def get_all_node_children(deposit_list, parent_of_node):
        current_children = [child for child in cluster_mesh_info.data_instances_by_class['PNode'] if child['m_parent'] is parent_of_node]
        deposit_list.extend(current_children)
        for child in current_children:
            get_all_node_children(deposit_list, child)

    def map_all_node_children(deposit_dict, in_list):
        for node in in_list:
            deposit_dict[node['m_name']['m_buffer']] = node
    if 'PNode' in cluster_mesh_info.data_instances_by_class:
        for node in cluster_mesh_info.data_instances_by_class['PNode']:
            derive_matrix_44(node, node['mu_matrixToUse'])
    if True:
        gltf_export(g, cluster_mesh_info, cluster_header, pdatablock_list)
        return

def gltf_export(g, cluster_mesh_info, cluster_header, pdatablock_list):
    if True:
        asset = {}
        asset['generator'] = 'ed8pkg2glb'
        asset['version'] = '2.0'
        cluster_mesh_info.gltf_data['asset'] = asset
        extensionsUsed = []
        cluster_mesh_info.gltf_data['extensionsUsed'] = extensionsUsed
        buffers = []
        need_embed = False
        if True:
            need_embed = True
        if need_embed == False:
            need_embed = cluster_header.cluster_marker == NOEPY_HEADER_BE
        buffer0 = {}
        buffers.append(buffer0)
        if need_embed == False:
            buffer1 = {}
            buffer1['uri'] = cluster_mesh_info.filename
            g.seek(0, os.SEEK_END)
            buffer1['byteLength'] = g.tell()
            buffers.append(buffer1)
        cluster_mesh_info.gltf_data['buffers'] = buffers
        bufferviews = []
        accessors = []
        embedded_giant_buffer = []
        embedded_giant_buffer_length = [0]

        def add_bufferview_embed(data, stride=None):
            bufferview = {}
            bufferview['buffer'] = 0
            bufferview['byteOffset'] = embedded_giant_buffer_length[0]
            bufferview['byteLength'] = len(data)
            if stride != None:
                bufferview['byteStride'] = stride
            embedded_giant_buffer.append(data)
            embedded_giant_buffer_length[0] += len(data)
            padding_length = 4 - len(data) % 4
            embedded_giant_buffer.append(b'\x00' * padding_length)
            embedded_giant_buffer_length[0] += padding_length
            bufferviews.append(bufferview)

        def add_bufferview_reference(position, size, stride=None):
            bufferview = {}
            bufferview['buffer'] = 1
            bufferview['byteOffset'] = position
            bufferview['byteLength'] = size
            if stride != None:
                bufferview['byteStride'] = stride
            bufferviews.append(bufferview)
        dummy_color_accessor_index = {}
        dummy_color_float4 = array.array('f')
        dummy_color_float4.append(1.0)
        dummy_color_float4.append(1.0)
        dummy_color_float4.append(1.0)
        dummy_color_float4.append(1.0)
        dummy_color_float4_blob = bytes(dummy_color_float4)

        def get_accessor_color_dummy(count):
            if count in dummy_color_accessor_index:
                return dummy_color_accessor_index[count]
            blobdata = dummy_color_float4_blob * count
            accessor = {}
            accessor['bufferView'] = len(bufferviews)
            accessor['componentType'] = 5126
            accessor['type'] = 'VEC4'
            accessor['count'] = count
            accessor_index = len(accessors)
            accessors.append(accessor)
            add_bufferview_embed(data=blobdata)
            dummy_color_accessor_index[count] = accessor_index
            return accessor_index
        if 'PMeshSegment' in cluster_mesh_info.data_instances_by_class:
            for meshSegment in cluster_mesh_info.data_instances_by_class['PMeshSegment']:
                accessor = {}
                accessor['bufferView'] = len(bufferviews)
                datatype = meshSegment['m_indexData']['m_type']
                datatyperemapped = dataTypeMappingPrimitiveRemap[datatype]
                dataTypeForGltf = dataTypeMappingForGltf[datatyperemapped]
                elementcount = meshSegment['m_indexData']['m_elementCount']
                accessor['componentType'] = dataTypeForGltf
                accessor['min'] = [meshSegment['m_indexData']['m_minimumIndex']]
                accessor['max'] = [meshSegment['m_indexData']['m_maximumIndex']]
                accessor['type'] = 'SCALAR'
                accessor['count'] = elementcount
                meshSegment['mu_gltfAccessorIndex'] = len(accessors)
                if need_embed:
                    datatypepython = dataTypeMappingForPython[datatyperemapped]
                    blobdata = meshSegment['mu_indBuffer']
                    singleelementsize = struct.calcsize(datatypepython)
                    if singleelementsize * elementcount != len(blobdata):
                        blobdata = blobdata[:singleelementsize * elementcount]
                    if cluster_header.cluster_marker == NOEPY_HEADER_BE:
                        blobdatabyteswap = bytearray(blobdata)
                        bytearray_byteswap(blobdatabyteswap, singleelementsize)
                        blobdata = blobdatabyteswap
                    add_bufferview_embed(data=blobdata)
                else:
                    add_bufferview_reference(position=cluster_mesh_info.vram_model_data_offset + meshSegment['mu_indBufferPosition'], size=meshSegment['mu_indBufferSize'])
                accessors.append(accessor)
        if 'PMesh' in cluster_mesh_info.data_instances_by_class:
            for mesh in cluster_mesh_info.data_instances_by_class['PMesh']:
                matrix_list = []
                if 'm_skeletonMatrices' in mesh and type(mesh['m_skeletonMatrices']['m_els']) == list:
                    for skeletonMatrix in mesh['m_skeletonMatrices']['m_els']:
                        matrix_list.append(bytes(cast_memoryview(skeletonMatrix['m_elements'], 'B')))
                if len(matrix_list) > 0:
                    blobdata = b''.join(matrix_list)
                    accessor = {}
                    accessor['bufferView'] = len(bufferviews)
                    accessor['componentType'] = 5126
                    accessor['type'] = 'MAT4'
                    accessor['count'] = len(matrix_list)
                    mesh['mu_gltfAccessorForInverseBindMatrixIndex'] = len(accessors)
                    add_bufferview_embed(data=blobdata)
                    accessors.append(accessor)
        if 'PMeshSegment' in cluster_mesh_info.data_instances_by_class:
            for meshSegment in cluster_mesh_info.data_instances_by_class['PMeshSegment']:
                for vertexData in meshSegment['m_vertexData']['m_els']:
                    for streamInfo in vertexData['m_streams']['m_els']:
                        renderDataType = streamInfo['m_renderDataType']
                        if renderDataType in ['SkinIndices'] and 'mu_remappedVertBufferSkeleton' in streamInfo:
                            blobdata = streamInfo['mu_remappedVertBufferSkeleton']
                            accessor = {}
                            accessor['bufferView'] = len(bufferviews)
                            accessor['componentType'] = 5123
                            accessor['type'] = 'VEC4'
                            accessor['count'] = vertexData['m_elementCount']
                            streamInfo['mu_gltfAccessorForRemappedSkinIndiciesIndex'] = len(accessors)
                            add_bufferview_embed(data=blobdata)
                            accessors.append(accessor)
                        if renderDataType in ['Color'] and 'mu_convertedColor' in streamInfo:
                            blobdata = streamInfo['mu_convertedColor']
                            accessor = {}
                            accessor['bufferView'] = len(bufferviews)
                            accessor['componentType'] = 5126
                            accessor['type'] = 'VEC4'
                            accessor['count'] = vertexData['m_elementCount']
                            streamInfo['mu_gltfAccessorForConvertedColor'] = len(accessors)
                            add_bufferview_embed(data=blobdata)
                            accessors.append(accessor)
                        if renderDataType in ['Tangent', 'SkinnableTangent'] and 'mu_expandedHandednessTangent' in streamInfo:
                            blobdata = streamInfo['mu_expandedHandednessTangent']
                            accessor = {}
                            accessor['bufferView'] = len(bufferviews)
                            accessor['componentType'] = 5126
                            accessor['type'] = 'VEC4'
                            accessor['count'] = vertexData['m_elementCount']
                            streamInfo['mu_gltfAccessorForExpandedHandednessTangent'] = len(accessors)
                            add_bufferview_embed(data=blobdata)
                            accessors.append(accessor)
        for vertexData in pdatablock_list:
            for streamInfo in vertexData['m_streams']['m_els']:
                accessor = {}
                accessor['bufferView'] = len(bufferviews)
                dataTypeForGltf = 5123
                datatype = streamInfo['m_type']
                datatyperemapped = dataTypeMappingPrimitiveRemap[datatype]
                datatypenew = None
                if datatyperemapped in dataTypeMappingNonstandardRemapForGltf:
                    datatypenew = dataTypeMappingNonstandardRemapForGltf[datatyperemapped]
                    dataTypeForGltf = dataTypeMappingForGltf[datatypenew]
                else:
                    dataTypeForGltf = dataTypeMappingForGltf[datatyperemapped]
                elementcount = vertexData['m_elementCount']
                datastride = vertexData['m_stride']
                accessor['componentType'] = dataTypeForGltf
                accessor['type'] = dataTypeCountMappingForGltf[datatype % 4]
                accessor['count'] = elementcount
                if datatyperemapped in dataTypeMappingNormalizationMultiplier:
                    accessor['normalized'] = True
                streamInfo['mu_gltfAccessorIndex'] = len(accessors)
                if need_embed or datatypenew != None:
                    datatypepython = dataTypeMappingForPython[datatyperemapped]
                    dataTypeCount = datatype % 4 + 1
                    blobdata = streamInfo['mu_vertBuffer']
                    singleelementsize = struct.calcsize(datatypepython)
                    blobstride = datastride
                    if dataTypeCount * singleelementsize != blobstride:
                        deinterleaved_stride = singleelementsize * dataTypeCount
                        deinterleaved_data = memoryview(bytearray(deinterleaved_stride * elementcount))
                        for i in range(elementcount):
                            deinterleaved_data[deinterleaved_stride * i:deinterleaved_stride * (i + 1)] = blobdata[blobstride * i:blobstride * i + deinterleaved_stride]
                        blobstride = dataTypeCount * singleelementsize
                        blobdata = bytes(deinterleaved_data)
                    elif dataTypeCount * singleelementsize * elementcount != len(blobdata):
                        blobdata = blobdata[0:dataTypeCount * singleelementsize * elementcount]
                    if cluster_header.cluster_marker == NOEPY_HEADER_BE:
                        blobdatabyteswap = bytearray(blobdata)
                        bytearray_byteswap(blobdatabyteswap, singleelementsize)
                        blobdata = blobdatabyteswap
                    if datatypenew != None:
                        datatypenewpython = dataTypeMappingForPython[datatypenew]
                        singleelementsizenew = struct.calcsize(datatypenewpython)
                        blobdatafloatextend = cast_memoryview(memoryview(bytearray(dataTypeCount * elementcount * singleelementsizenew)), datatypenewpython)
                        for i in range(dataTypeCount * elementcount):
                            blobdatafloatextend[i] = struct.unpack(datatypepython, blobdata[i * singleelementsize:i * singleelementsize + singleelementsize])[0]
                        blobdata = bytes(cast_memoryview(blobdatafloatextend, 'B'))
                        blobstride = dataTypeCount * singleelementsizenew
                    add_bufferview_embed(data=blobdata, stride=blobstride)
                else:
                    add_bufferview_reference(position=cluster_mesh_info.vram_model_data_offset + streamInfo['mu_vertBufferPosition'], size=streamInfo['mu_vertBufferSize'], stride=datastride)
                accessors.append(accessor)
        if 'PAnimationChannelTimes' in cluster_mesh_info.data_instances_by_class:
            for animationChannelTime in cluster_mesh_info.data_instances_by_class['PAnimationChannelTimes']:
                blobdata = bytes(cast_memoryview(animationChannelTime['mu_animation_timestamps'], 'B'))
                if 0.0 != 0.0:
                    blobdatafloatextend = cast_memoryview(memoryview(bytearray(blobdata)), 'f')
                    if True:
                        float_divided = 1.0 / 0.0
                        for i in range(len(blobdatafloatextend)):
                            blobdatafloatextend[i] += float_divided
                        blobdata = bytes(cast_memoryview(blobdatafloatextend, 'B'))
                accessor = {}
                accessor['bufferView'] = len(bufferviews)
                accessor['componentType'] = 5126
                accessor['type'] = 'SCALAR'
                accessor['count'] = animationChannelTime['m_keyCount']
                cur_min = float('inf')
                cur_max = float('-inf')
                times = cast_memoryview(memoryview(blobdata), 'f')
                for time in times:
                    if time < cur_min:
                        cur_min = time
                    if time > cur_max:
                        cur_max = time
                accessor['min'] = [cur_min]
                accessor['max'] = [cur_max]
                animationChannelTime['mu_gltfAccessorIndex'] = len(accessors)
                add_bufferview_embed(data=blobdata)
                accessors.append(accessor)
        if 'PAnimationChannel' in cluster_mesh_info.data_instances_by_class:
            for animationChannel in cluster_mesh_info.data_instances_by_class['PAnimationChannel']:
                blobdata = bytes(cast_memoryview(animationChannel['m_valueKeys']['m_els'], 'B'))
                accessor = {}
                accessor['bufferView'] = len(bufferviews)
                accessor['componentType'] = 5126
                if animationChannel['m_keyType'] == 'Translation' or animationChannel['m_keyType'] == 'Scale':
                    accessor['type'] = 'VEC3'
                    accessor['count'] = animationChannel['m_keyCount']
                elif animationChannel['m_keyType'] == 'Rotation':
                    accessor['type'] = 'VEC4'
                    accessor['count'] = animationChannel['m_keyCount']
                else:
                    accessor['type'] = 'SCALAR'
                    accessor['count'] = animationChannel['m_keyCount']
                animationChannel['mu_gltfAccessorIndex'] = len(accessors)
                accessors.append(accessor)
                add_bufferview_embed(data=blobdata)
        if 'PAnimationConstantChannel' in cluster_mesh_info.data_instances_by_class:
            for animationConstantChannel in cluster_mesh_info.data_instances_by_class['PAnimationConstantChannel']:
                tmparray = bytes(animationConstantChannel['m_value'])
                if animationConstantChannel['m_keyType'] == 'Scale' or animationConstantChannel['m_keyType'] == 'Translation':
                    tmparray = tmparray[:-4]
                blobdata = tmparray * 2
                accessor = {}
                accessor['bufferView'] = len(bufferviews)
                accessor['componentType'] = 5126
                if animationConstantChannel['m_keyType'] == 'Translation' or animationConstantChannel['m_keyType'] == 'Scale':
                    accessor['type'] = 'VEC3'
                    accessor['count'] = 2
                elif animationConstantChannel['m_keyType'] == 'Rotation':
                    accessor['type'] = 'VEC4'
                    accessor['count'] = 2
                else:
                    accessor['type'] = 'SCALAR'
                    accessor['count'] = 2
                animationConstantChannel['mu_gltfAccessorIndex'] = len(accessors)
                accessors.append(accessor)
                add_bufferview_embed(data=blobdata)
        if 'PAnimationClip' in cluster_mesh_info.data_instances_by_class:
            for animationClip in cluster_mesh_info.data_instances_by_class['PAnimationClip']:
                tmparray = animationClip['mu_animation_timestamps']
                blobdata = bytes(cast_memoryview(tmparray, 'B'))
                accessor = {}
                accessor['bufferView'] = len(bufferviews)
                accessor['componentType'] = 5126
                accessor['type'] = 'SCALAR'
                accessor['count'] = 2
                accessor['min'] = [tmparray[0]]
                accessor['max'] = [tmparray[1]]
                animationClip['mu_gltfAccessorIndex'] = len(accessors)
                accessors.append(accessor)
                add_bufferview_embed(data=blobdata)
        images = []
        if 'PAssetReferenceImport' in cluster_mesh_info.data_instances_by_class:
            for assetReferenceImport in cluster_mesh_info.data_instances_by_class['PAssetReferenceImport']:
                if assetReferenceImport['m_targetAssetType'] == 'PTexture2D':
                    image = {}
                    image_path = os.path.basename(assetReferenceImport['m_id']['m_buffer'])
                    image_name = image_path.rsplit('.', maxsplit=2)[0]
                    if True:
                        image_name += '.png'
                    if cluster_mesh_info.storage_media.check_existent_storage(image_name):
                        with cluster_mesh_info.storage_media.open(image_name, 'rb') as f:
                            blobdata = f.read()
                            image['bufferView'] = len(bufferviews)
                            if True:
                                image['mimeType'] = 'image/png'
                            add_bufferview_embed(data=blobdata)
                    else:
                        image['uri'] = image_name
                    assetReferenceImport['mu_gltfImageIndex'] = len(images)
                    images.append(image)
        cluster_mesh_info.gltf_data['images'] = images
        samplers = []
        filter_map = {0: 9728, 1: 9729, 2: 9984, 3: 9985, 4: 9986, 5: 9987}
        wrap_map = {0: 33071, 1: 10497, 2: 33071, 3: 33071, 4: 33648}
        if 'PSamplerState' in cluster_mesh_info.data_instances_by_class:
            for samplerState in cluster_mesh_info.data_instances_by_class['PSamplerState']:
                sampler = {}
                if samplerState['m_magFilter'] in filter_map:
                    sampler['magFilter'] = filter_map[samplerState['m_magFilter']]
                if samplerState['m_minFilter'] in filter_map:
                    sampler['minFilter'] = filter_map[samplerState['m_minFilter']]
                if samplerState['m_wrapS'] in wrap_map:
                    sampler['wrapS'] = wrap_map[samplerState['m_wrapS']]
                if samplerState['m_wrapT'] in wrap_map:
                    sampler['wrapT'] = wrap_map[samplerState['m_wrapT']]
                samplerState['mu_gltfSamplerIndex'] = len(samplers)
                samplers.append(sampler)
        cluster_mesh_info.gltf_data['samplers'] = samplers
        textures = []
        if 'PParameterBuffer' in cluster_mesh_info.data_instances_by_class:
            for k in cluster_mesh_info.data_instances_by_class.keys():
                has_key = False
                if type(k) == int:
                    data_instances = cluster_mesh_info.data_instances_by_class[k]
                    if len(data_instances) > 0:
                        if data_instances[0]['mu_memberClass'] == 'PParameterBuffer':
                            has_key = True
                if has_key == True:
                    for parameter_buffer in cluster_mesh_info.data_instances_by_class[k]:
                        shaderparam = parameter_buffer['mu_shaderParameters']
                        if True:
                            samplerstate = None
                            if 'DiffuseMapSamplerS' in shaderparam and type(shaderparam['DiffuseMapSamplerS']) == dict:
                                samplerstate = shaderparam['DiffuseMapSamplerS']
                            elif 'DiffuseMapSamplerSampler' in shaderparam and type(shaderparam['DiffuseMapSamplerSampler']) == dict:
                                samplerstate = shaderparam['DiffuseMapSamplerSampler']
                            if 'DiffuseMapSampler' in parameter_buffer['mu_shaderParameters'] and type(parameter_buffer['mu_shaderParameters']['DiffuseMapSampler']) == str:
                                if 'PAssetReferenceImport' in cluster_mesh_info.data_instances_by_class:
                                    for assetReferenceImport in cluster_mesh_info.data_instances_by_class['PAssetReferenceImport']:
                                        if assetReferenceImport['m_id']['m_buffer'] == parameter_buffer['mu_shaderParameters']['DiffuseMapSampler'] and 'mu_gltfImageIndex' in assetReferenceImport:
                                            texture = {}
                                            if samplerstate != None:
                                                texture['sampler'] = samplerstate['mu_gltfSamplerIndex']
                                            texture['source'] = assetReferenceImport['mu_gltfImageIndex']
                                            parameter_buffer['mu_gltfTextureDiffuseIndex'] = len(textures)
                                            textures.append(texture)
                                            break
                        if True:
                            samplerstate = None
                            if 'NormalMapSamplerS' in shaderparam and type(shaderparam['NormalMapSamplerS']) == dict:
                                samplerstate = shaderparam['NormalMapSamplerS']
                            elif 'NormalMapSamplerSampler' in shaderparam and type(shaderparam['NormalMapSamplerSampler']) == dict:
                                samplerstate = shaderparam['NormalMapSamplerSampler']
                            if 'NormalMapSampler' in parameter_buffer['mu_shaderParameters'] and type(parameter_buffer['mu_shaderParameters']['NormalMapSampler']) == str:
                                if 'PAssetReferenceImport' in cluster_mesh_info.data_instances_by_class:
                                    for assetReferenceImport in cluster_mesh_info.data_instances_by_class['PAssetReferenceImport']:
                                        if assetReferenceImport['m_id']['m_buffer'] == parameter_buffer['mu_shaderParameters']['NormalMapSampler'] and 'mu_gltfImageIndex' in assetReferenceImport:
                                            texture = {}
                                            if samplerstate != None:
                                                texture['sampler'] = samplerstate['mu_gltfSamplerIndex']
                                            texture['source'] = assetReferenceImport['mu_gltfImageIndex']
                                            parameter_buffer['mu_gltfTextureNormalIndex'] = len(textures)
                                            textures.append(texture)
                                            break
                        if True:
                            samplerstate = None
                            if 'SpecularMapSamplerS' in shaderparam and type(shaderparam['SpecularMapSamplerS']) == dict:
                                samplerstate = shaderparam['SpecularMapSamplerS']
                            elif 'SpecularMapSamplerSampler' in shaderparam and type(shaderparam['SpecularMapSamplerSampler']) == dict:
                                samplerstate = shaderparam['SpecularMapSamplerSampler']
                            if 'SpecularMapSampler' in parameter_buffer['mu_shaderParameters'] and type(parameter_buffer['mu_shaderParameters']['SpecularMapSampler']) == str:
                                if 'PAssetReferenceImport' in cluster_mesh_info.data_instances_by_class:
                                    for assetReferenceImport in cluster_mesh_info.data_instances_by_class['PAssetReferenceImport']:
                                        if assetReferenceImport['m_id']['m_buffer'] == parameter_buffer['mu_shaderParameters']['SpecularMapSampler'] and 'mu_gltfImageIndex' in assetReferenceImport:
                                            texture = {}
                                            if samplerstate != None:
                                                texture['sampler'] = samplerstate['mu_gltfSamplerIndex']
                                            texture['source'] = assetReferenceImport['mu_gltfImageIndex']
                                            parameter_buffer['mu_gltfTextureSpecularIndex'] = len(textures)
                                            textures.append(texture)
                                            break
        cluster_mesh_info.gltf_data['textures'] = textures
        materials = []
        if 'PMaterial' in cluster_mesh_info.data_instances_by_class:
            for material in cluster_mesh_info.data_instances_by_class['PMaterial']:
                material_obj = {}
                material_obj['name'] = material['mu_materialname']
                parameter_buffer = material['m_parameterBuffer']
                if 'mu_gltfTextureDiffuseIndex' in parameter_buffer:
                    textureInfo = {}
                    textureInfo['index'] = parameter_buffer['mu_gltfTextureDiffuseIndex']
                    pbrMetallicRoughness = {}
                    pbrMetallicRoughness['baseColorTexture'] = textureInfo
                    pbrMetallicRoughness['metallicFactor'] = 0.0
                    material_obj['pbrMetallicRoughness'] = pbrMetallicRoughness
                if 'mu_gltfTextureNormalIndex' in parameter_buffer:
                    normalTextureInfo = {}
                    normalTextureInfo['index'] = parameter_buffer['mu_gltfTextureNormalIndex']
                    material_obj['normalTexture'] = normalTextureInfo
                material['mu_gltfMaterialIndex'] = len(materials)
                materials.append(material_obj)
        cluster_mesh_info.gltf_data['materials'] = materials
        meshes = []
        mesh_instances = []
        if 'PMeshInstance' in cluster_mesh_info.data_instances_by_class:
            mesh_instances = cluster_mesh_info.data_instances_by_class['PMeshInstance']
        for meshInstance in mesh_instances:
            curmesh = meshInstance['m_mesh']
            primitives = []
            for tt in range(len(curmesh['m_meshSegments']['m_els'])):
                primitive = {}
                m = curmesh['m_meshSegments']['m_els'][tt]
                if curmesh['m_defaultMaterials']['m_materials']['m_u'] != None and len(curmesh['m_defaultMaterials']['m_materials']['m_u']) > m['m_materialIndex']:
                    mat = curmesh['m_defaultMaterials']['m_materials']['m_u'][m['m_materialIndex']]
                    if mat != None:
                        primitive['material'] = mat['mu_gltfMaterialIndex']
                segmentcontext = meshInstance['m_segmentContext']['m_els'][tt]
                attributes = {}
                colorCount = 0
                for vertexData in m['m_vertexData']['m_els']:
                    for streamInfo in vertexData['m_streams']['m_els']:
                        renderDataType = streamInfo['m_renderDataType']
                        if renderDataType in ['Vertex', 'SkinnableVertex']:
                            attributes['POSITION'] = streamInfo['mu_gltfAccessorIndex']
                        elif renderDataType in ['Normal', 'SkinnableNormal']:
                            attributes['NORMAL'] = streamInfo['mu_gltfAccessorIndex']
                        elif renderDataType in ['ST']:
                            pass
                        elif renderDataType in ['SkinWeights']:
                            attributes['WEIGHTS_0'] = streamInfo['mu_gltfAccessorIndex']
                        elif renderDataType in ['SkinIndices']:
                            if 'mu_gltfAccessorForRemappedSkinIndiciesIndex' in streamInfo:
                                attributes['JOINTS_0'] = streamInfo['mu_gltfAccessorForRemappedSkinIndiciesIndex']
                            else:
                                attributes['JOINTS_0'] = streamInfo['mu_gltfAccessorIndex']
                        elif renderDataType in ['Color']:
                            if 'mu_gltfAccessorForConvertedColor' in streamInfo:
                                attributes['COLOR_' + str(colorCount)] = streamInfo['mu_gltfAccessorForConvertedColor']
                            else:
                                attributes['COLOR_' + str(colorCount)] = streamInfo['mu_gltfAccessorIndex']
                            colorCount += 1
                        elif renderDataType in ['Tangent', 'SkinnableTangent']:
                            if 'mu_gltfAccessorForExpandedHandednessTangent' in streamInfo:
                                attributes['TANGENT'] = streamInfo['mu_gltfAccessorForExpandedHandednessTangent']
                uvDataStreamSet = {}
                for vertexData in m['m_vertexData']['m_els']:
                    for streamInfo in vertexData['m_streams']['m_els']:
                        renderDataType = streamInfo['m_renderDataType']
                        if renderDataType in ['ST']:
                            streamSet = streamInfo['m_streamSet']
                            uvDataStreamSet[streamSet] = [vertexData, streamInfo]
                uvDataLowest = None
                for i in sorted(uvDataStreamSet.keys()):
                    if uvDataStreamSet[i] != None:
                        uvDataLowest = uvDataStreamSet[i]
                        break
                uvDataRemapped = [uvDataStreamSet[i] for i in sorted(uvDataStreamSet.keys()) if uvDataStreamSet[i] != None]
                if uvDataLowest != None:
                    for i in sorted(uvDataStreamSet.keys()):
                        vertexData = uvDataStreamSet[i][0]
                        if vertexData == None:
                            continue
                        streamInfo = uvDataStreamSet[i][1]
                        if type(segmentcontext['m_streamBindings']) == dict:
                            for streamBinding in segmentcontext['m_streamBindings']['m_u']:
                                if streamBinding['m_renderDataType'] == 'ST' and streamBinding['m_inputSet'] == streamInfo['m_streamSet']:
                                    name_lower = streamBinding['m_name']['m_buffer'].lower()
                                    name_to_uv_index_map = {'texcoord7': 6, 'texcoord6': 5, 'texcoord5': 4, 'texcoord4': 3, 'texcoord3': 2, 'texcoord2': 1, 'texcoord': 0, 'vitexcoord': 0, 'texcoord0': 0}
                                    if name_lower in name_to_uv_index_map:
                                        uvIndex = name_to_uv_index_map[name_lower]
                                        while len(uvDataRemapped) <= uvIndex:
                                            uvDataRemapped.append(None)
                                        uvDataRemapped[uvIndex] = [vertexData, streamInfo]
                if len(uvDataRemapped) > 0:
                    while uvDataRemapped[-1] == None:
                        uvDataRemapped.pop()
                for i in range(len(uvDataRemapped)):
                    if uvDataRemapped[i] == None:
                        uvDataRemapped[i] = uvDataLowest
                for i in range(len(uvDataRemapped)):
                    vertexData = uvDataRemapped[i][0]
                    streamInfo = uvDataRemapped[i][1]
                    attributes['TEXCOORD_' + str(i)] = streamInfo['mu_gltfAccessorIndex']
                primitive['attributes'] = attributes
                primitive['indices'] = m['mu_gltfAccessorIndex']
                primitiveTypeForGltf = 0
                primitiveTypeMappingForGltf = {0: 0, 1: 1, 2: 4, 3: 5, 4: 6, 5: 0}
                if m['m_primitiveType'] in primitiveTypeMappingForGltf:
                    primitiveTypeForGltf = primitiveTypeMappingForGltf[m['m_primitiveType']]
                primitive['mode'] = primitiveTypeForGltf
                primitives.append(primitive)
            if True:
                mesh = {}
                mesh['primitives'] = primitives
                mesh['name'] = curmesh['mu_name']
                meshInstance['mu_gltfMeshIndex'] = len(meshes)
                meshes.append(mesh)
        cluster_mesh_info.gltf_data['meshes'] = meshes
        extensions = {}
        lights = []
        if 'PLight' in cluster_mesh_info.data_instances_by_class:
            light_type_map = {'DirectionalLight': 'directional', 'PointLight': 'point', 'SpotLight': 'spot'}
            for light in cluster_mesh_info.data_instances_by_class['PLight']:
                if light['m_lightType'] in light_type_map:
                    light_obj = {}
                    name = ''
                    if name == '':
                        if 'mu_name' in light:
                            name = light['mu_name']
                    if name != '':
                        light_obj['name'] = name
                    color = light['m_color']['m_elements']
                    light_obj['color'] = [color[0], color[1], color[2]]
                    light_obj['intensity'] = light['m_intensity']
                    light_obj['type'] = light_type_map[light['m_lightType']]
                    if light_obj['type'] == 'spot':
                        spot = {}
                        spot['innerConeAngle'] = light['m_innerConeAngle']
                        spot['outerConeAngle'] = light['m_outerConeAngle']
                        light_obj['spot'] = spot
                    if light_obj['type'] == 'point' or (light_obj['type'] == 'spot' and light['m_outerRange'] > 0):
                        light_obj['range'] = light['m_outerRange']
                    light['mu_gltfLightIndex'] = len(lights)
                    lights.append(light_obj)
        if len(lights) > 0:
            KHR_lights_punctual = {}
            KHR_lights_punctual['lights'] = lights
            extensionsUsed.append('KHR_lights_punctual')
            extensions['KHR_lights_punctual'] = KHR_lights_punctual
        if len(extensions) > 0:
            cluster_mesh_info.gltf_data['extensions'] = extensions
        nodes = []
        if 'PNode' in cluster_mesh_info.data_instances_by_class:
            mesh_segment_nodes = []
            for node in cluster_mesh_info.data_instances_by_class['PNode']:
                node_obj = {}
                node_extensions = {}
                if True:
                    node_obj['matrix'] = node['mu_matrixToUse'].tolist()
                name = node['m_name']['m_buffer']
                if name == '':
                    if 'mu_name' in node:
                        name = node['mu_name']
                mesh_node_indices = None
                if 'PMeshInstance' in cluster_mesh_info.data_instances_by_class:
                    for meshInstance in cluster_mesh_info.data_instances_by_class['PMeshInstance']:
                        if meshInstance['m_localToWorldMatrix'] is node['m_worldMatrix']:
                            if name == '' and 'mu_name' in meshInstance:
                                name = meshInstance['mu_name']
                            if name == '' and 'mu_name' in meshInstance['m_mesh']:
                                name = meshInstance['m_mesh']['mu_name']
                            if 'mu_gltfMeshIndex' in meshInstance:
                                node_obj['mesh'] = meshInstance['mu_gltfMeshIndex']
                                meshInstance['mu_gltfNodeIndex'] = len(nodes)
                            elif 'mu_gltfMeshSegmentsIndicies' in meshInstance:
                                mesh_node_indices = meshInstance['mu_gltfMeshSegmentsIndicies']
                            break
                if 'PLight' in cluster_mesh_info.data_instances_by_class:
                    node_KHR_lights_punctual = {}
                    for light in cluster_mesh_info.data_instances_by_class['PLight']:
                        if light['m_localToWorldMatrix'] is node['m_worldMatrix'] and 'mu_gltfLightIndex' in light:
                            if name == '' and 'mu_name' in light:
                                name = light['mu_name']
                            node_KHR_lights_punctual['light'] = light['mu_gltfLightIndex']
                            light['mu_gltfNodeIndex'] = len(nodes)
                            break
                    if len(node_KHR_lights_punctual) > 0:
                        node_extensions['KHR_lights_punctual'] = node_KHR_lights_punctual
                if len(node_extensions) > 0:
                    node_obj['extensions'] = node_extensions
                if name != '':
                    node_obj['name'] = name
                children = [i for i in range(len(cluster_mesh_info.data_instances_by_class['PNode'])) if cluster_mesh_info.data_instances_by_class['PNode'][i]['m_parent'] is node]
                if mesh_node_indices != None:
                    for mesh_node_index in mesh_node_indices:
                        mesh_segment_node = {}
                        mesh_segment_node['name'] = meshes[mesh_node_index]['name'] + '_node'
                        mesh_segment_node['mesh'] = mesh_node_index
                        children.append(len(cluster_mesh_info.data_instances_by_class['PNode']) + len(mesh_segment_nodes))
                        mesh_segment_nodes.append(mesh_segment_node)
                if len(children) > 0:
                    node_obj['children'] = children
                node['mu_gltfNodeIndex'] = len(nodes)
                node['mu_gltfNodeName'] = name
                nodes.append(node_obj)
            for node_obj in mesh_segment_nodes:
                nodes.append(node_obj)
        cluster_mesh_info.gltf_data['nodes'] = nodes
        skins = []
        if 'PMeshInstance' in cluster_mesh_info.data_instances_by_class:
            for meshInstance in cluster_mesh_info.data_instances_by_class['PMeshInstance']:
                mesh = meshInstance['m_mesh']
                if 'mu_gltfAccessorForInverseBindMatrixIndex' in mesh and 'mu_gltfNodeIndex' in meshInstance:
                    nodes[meshInstance['mu_gltfNodeIndex']]['skin'] = len(skins)
                    skin = {}
                    if 'mu_root_matrix_name' in mesh and mesh['mu_root_matrix_name'] != None:
                        joint = None
                        for i in range(len(nodes)):
                            node_obj = nodes[i]
                            if node_obj['name'] == mesh['mu_root_matrix_name']:
                                joint = i
                                break
                        if joint != None:
                            skin['skeleton'] = joint
                    skin['inverseBindMatrices'] = mesh['mu_gltfAccessorForInverseBindMatrixIndex']
                    if len(nodes) > 0 and type(mesh['m_matrixNames']['m_els']) == list and (type(mesh['m_matrixParents']['m_els']) == memoryview or type(mesh['m_matrixParents']['m_els']) == array.array) and (len(mesh['m_matrixNames']['m_els']) == len(mesh['m_matrixParents']['m_els'])):
                        joints = []
                        skeleton_matrix_names = []
                        matrix_index_to_node = {}
                        matrix_names = mesh['m_matrixNames']['m_els']
                        for i in range(len(matrix_names)):
                            matrix_name = matrix_names[i]
                            for ii in range(len(nodes)):
                                node_obj = nodes[ii]
                                if node_obj['name'] == matrix_name['m_buffer']:
                                    matrix_index_to_node[i] = ii
                                    break
                        for skeletonJointBound in mesh['m_skeletonBounds']['m_els']:
                            hierarchy_matrix_index = skeletonJointBound['m_hierarchyMatrixIndex']
                            matrix_name = matrix_names[hierarchy_matrix_index]
                            skeleton_matrix_names.append(matrix_name['m_buffer'])
                            joint = None
                            for i in range(len(nodes)):
                                node_obj = nodes[i]
                                if node_obj['name'] == matrix_name['m_buffer']:
                                    joint = i
                                    break
                            if joint != None:
                                joints.append(joint)
                                matrix_index_to_node[hierarchy_matrix_index] = joint
                            else:
                                joints.append(1)
                        if len(joints) > 0:
                            skin['joints'] = joints
                            meshInstance['mu_gltfSkinMatrixIndexToNode'] = matrix_index_to_node
                    meshInstance['mu_gltfSkinIndex'] = len(skins)
                    skins.append(skin)
        mesh_is_empty = True
        if 'PMeshInstance' in cluster_mesh_info.data_instances_by_class:
            for meshInstance in cluster_mesh_info.data_instances_by_class['PMeshInstance']:
                mesh_is_empty = False
                break
        if mesh_is_empty and 'PAnimationSet' in cluster_mesh_info.data_instances_by_class:
            skin = {}
            skin['skeleton'] = 0
            joints = [i for i in range(len(nodes)) if i != 0]
            if len(joints) > 0:
                skin['joints'] = joints
            skins.append(skin)
        cluster_mesh_info.gltf_data['skins'] = skins
        animations = []
        targetMap = {'Translation': 'translation', 'Rotation': 'rotation', 'Scale': 'scale'}
        if 'PAnimationSet' in cluster_mesh_info.data_instances_by_class:
            for animationSet in cluster_mesh_info.data_instances_by_class['PAnimationSet']:
                for animationClip in animationSet['m_animationClips']['m_u']:
                    animation = {}
                    samplers = []
                    channels = []
                    for animationChannel in animationClip['m_channels']['m_els']:
                        if animationChannel['m_keyType'] not in targetMap:
                            continue
                        channel = {}
                        channel['sampler'] = len(samplers)
                        target = {}
                        target['path'] = targetMap[animationChannel['m_keyType']]
                        if animationChannel['m_instanceObjectType'] == 'PNode':
                            if 'PNode' in cluster_mesh_info.data_instances_by_class:
                                for node in cluster_mesh_info.data_instances_by_class['PNode']:
                                    if node['mu_gltfNodeName'] == animationChannel['m_name']['m_buffer']:
                                        target['node'] = node['mu_gltfNodeIndex']
                                        break
                        elif animationChannel['m_instanceObjectType'] == 'PMeshInstance':
                            if animationChannel['m_name']['m_buffer'] == 'm_currentPose':
                                instance_obj = animationChannel['m_instanceObject']
                                if instance_obj != None:
                                    if 'mu_gltfSkinMatrixIndexToNode' in instance_obj:
                                        target['node'] = instance_obj['mu_gltfSkinMatrixIndexToNode'][animationChannel['m_index']]
                        channel['target'] = target
                        sampler = {}
                        sampler['input'] = animationChannel['m_times']['mu_gltfAccessorIndex']
                        sampler['output'] = animationChannel['mu_gltfAccessorIndex']
                        if animationChannel['m_interp'] == 2:
                            sampler['interpolation'] = 'STEP'
                        else:
                            sampler['interpolation'] = 'LINEAR'
                        channels.append(channel)
                        samplers.append(sampler)
                    for animationConstantChannel in animationClip['m_constantChannels']['m_els']:
                        if animationConstantChannel['m_keyType'] not in targetMap:
                            continue
                        channel = {}
                        channel['sampler'] = len(samplers)
                        target = {}
                        target['path'] = targetMap[animationConstantChannel['m_keyType']]
                        if 'PNode' in cluster_mesh_info.data_instances_by_class:
                            for node in cluster_mesh_info.data_instances_by_class['PNode']:
                                if node['mu_gltfNodeName'] == animationConstantChannel['m_name']['m_buffer']:
                                    target['node'] = node['mu_gltfNodeIndex']
                                    break
                        channel['target'] = target
                        sampler = {}
                        sampler['input'] = animationClip['mu_gltfAccessorIndex']
                        sampler['output'] = animationConstantChannel['mu_gltfAccessorIndex']
                        if animationConstantChannel['m_interp'] == 2:
                            sampler['interpolation'] = 'STEP'
                        else:
                            sampler['interpolation'] = 'LINEAR'
                        channels.append(channel)
                        samplers.append(sampler)
                    animation['channels'] = channels
                    animation['samplers'] = samplers
                animations.append(animation)
        cluster_mesh_info.gltf_data['animations'] = animations
        cluster_mesh_info.gltf_data['scene'] = 0
        scenes = []
        if 'PNode' in cluster_mesh_info.data_instances_by_class:
            scene = {}
            nodes = [node['mu_gltfNodeIndex'] for node in cluster_mesh_info.data_instances_by_class['PNode'] if node['m_parent'] == None]
            scene['nodes'] = nodes
            scenes.append(scene)
        cluster_mesh_info.gltf_data['scenes'] = scenes
        cluster_mesh_info.gltf_data['bufferViews'] = bufferviews
        cluster_mesh_info.gltf_data['accessors'] = accessors
        if len(nodes) > 0:
            import json
            import base64
            embedded_giant_buffer_joined = b''.join(embedded_giant_buffer)
            buffer0['byteLength'] = len(embedded_giant_buffer_joined)
            if True:
                with cluster_mesh_info.storage_media.open(cluster_mesh_info.filename.split('.', 1)[0] + '.glb', 'wb') as f:
                    jsondata = json.dumps(cluster_mesh_info.gltf_data).encode('utf-8')
                    jsondata += b' ' * (4 - len(jsondata) % 4)
                    f.write(struct.pack('<III', 1179937895, 2, 12 + 8 + len(jsondata) + 8 + len(embedded_giant_buffer_joined)))
                    f.write(struct.pack('<II', len(jsondata), 1313821514))
                    f.write(jsondata)
                    f.write(struct.pack('<II', len(embedded_giant_buffer_joined), 5130562))
                    f.write(embedded_giant_buffer_joined)

def standalone_main():
    file_type = None
    storage_media = None
    in_name = None
    if True:
        in_name = sys.argv[1]
    if file_type == None:
        is_pkg = file_is_ed8_pkg(in_name)
        if is_pkg:
            file_type = 'pkg'
    if file_type == 'pkg':
        allowed_write_extensions = []
        allowed_write_extensions.append('.glb')
        storage_media = TSpecialOverlayMedia(os.path.realpath(in_name), allowed_write_extensions)
        items = []

        def list_callback(item):
            if item[-10:-6] == '.dae':
                items.append(item)
        storage_media.get_list_at('.', list_callback)
        if len(items) == 0:
            allowed_write_extensions.append('.png')

            def list_callback2(item):
                if item[-10:-6] in ['.dds', '.png', '.bmp']:
                    items.append(item)
            storage_media.get_list_at('.', list_callback2)
        for item in items:
            parse_cluster(item, None, storage_media)
        return
    raise Exception('Passed in file is not compatible file')
if __name__ == '__main__':
    standalone_main()
