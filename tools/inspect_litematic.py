#!/usr/bin/env python3
"""litemapy 를 쓰지 않고 .litematic 을 직접 파싱해 포맷을 독립 검증한다.

Litematica 포맷: gzip 압축된 NBT.
  Version, MinecraftDataVersion, Metadata{...}, Regions{ 이름: {...} }
  BlockStates 는 long 배열에 팔레트 인덱스를 bit-pack 한 것.
    bits = max(2, ceil(log2(팔레트크기))), 항목이 long 경계를 넘나드는 pre-1.16 방식.
    인덱스 = y*width*length + z*width + x
"""
from __future__ import annotations

import gzip
import struct
import sys

TAG_END, TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG = 0, 1, 2, 3, 4
TAG_FLOAT, TAG_DOUBLE, TAG_BYTE_ARRAY, TAG_STRING = 5, 6, 7, 8
TAG_LIST, TAG_COMPOUND, TAG_INT_ARRAY, TAG_LONG_ARRAY = 9, 10, 11, 12


class Reader:
    def __init__(self, data: bytes):
        self.d, self.i = data, 0

    def raw(self, n: int) -> bytes:
        b = self.d[self.i:self.i + n]
        if len(b) != n:
            raise EOFError("파일이 잘렸다")
        self.i += n
        return b

    def u1(self): return self.raw(1)[0]
    def i1(self): return struct.unpack(">b", self.raw(1))[0]
    def i2(self): return struct.unpack(">h", self.raw(2))[0]
    def i4(self): return struct.unpack(">i", self.raw(4))[0]
    def i8(self): return struct.unpack(">q", self.raw(8))[0]
    def f4(self): return struct.unpack(">f", self.raw(4))[0]
    def f8(self): return struct.unpack(">d", self.raw(8))[0]

    def string(self) -> str:
        return self.raw(self.i2()).decode("utf-8")

    def payload(self, tag: int):
        if tag == TAG_BYTE:   return self.i1()
        if tag == TAG_SHORT:  return self.i2()
        if tag == TAG_INT:    return self.i4()
        if tag == TAG_LONG:   return self.i8()
        if tag == TAG_FLOAT:  return self.f4()
        if tag == TAG_DOUBLE: return self.f8()
        if tag == TAG_BYTE_ARRAY: return self.raw(self.i4())
        if tag == TAG_STRING: return self.string()
        if tag == TAG_LIST:
            t, n = self.u1(), self.i4()
            return [self.payload(t) for _ in range(n)]
        if tag == TAG_COMPOUND:
            out = {}
            while True:
                t = self.u1()
                if t == TAG_END:
                    return out
                # 주의: out[self.string()] = self.payload(t) 로 쓰면 안 된다.
                # 파이썬은 대입문 우변을 먼저 평가하므로 이름보다 값을 먼저 읽어버린다.
                key = self.string()
                out[key] = self.payload(t)
        if tag == TAG_INT_ARRAY:  return [self.i4() for _ in range(self.i4())]
        if tag == TAG_LONG_ARRAY: return [self.i8() for _ in range(self.i4())]
        raise ValueError(f"알 수 없는 태그 {tag}")


def parse(path: str) -> dict:
    with gzip.open(path, "rb") as fh:
        r = Reader(fh.read())
    tag = r.u1()
    if tag != TAG_COMPOUND:
        raise ValueError("루트가 TAG_Compound 가 아니다")
    r.string()
    return r.payload(TAG_COMPOUND)


def unpack_states(longs: list[int], bits: int, count: int) -> list[int]:
    """Litematica 의 pre-1.16 스타일 비트 언패킹 (항목이 long 경계를 넘나든다)."""
    mask = (1 << bits) - 1
    u = [x & 0xFFFFFFFFFFFFFFFF for x in longs]
    out = []
    for i in range(count):
        start = i * bits
        a, b = start >> 6, ((i + 1) * bits - 1) >> 6
        off = start & 63
        if a == b:
            v = (u[a] >> off) & mask
        else:
            written = 64 - off
            v = ((u[a] >> off) | (u[b] << written)) & mask
        out.append(v)
    return out


def name_of(entry: dict) -> str:
    n = entry["Name"]
    props = entry.get("Properties") or {}
    return n + ("[" + ",".join(f"{k}={v}" for k, v in sorted(props.items())) + "]" if props else "")


def main(path: str) -> int:
    nbt = parse(path)
    print(f"파일: {path}")
    print(f"  Version              : {nbt.get('Version')}")
    print(f"  SubVersion           : {nbt.get('SubVersion')}")
    print(f"  MinecraftDataVersion : {nbt.get('MinecraftDataVersion')}")
    md = nbt.get("Metadata", {})
    print(f"  Metadata.Name        : {md.get('Name')}")
    print(f"  Metadata.EnclosingSize: {md.get('EnclosingSize')}")
    print(f"  Metadata.TotalBlocks : {md.get('TotalBlocks')}   TotalVolume: {md.get('TotalVolume')}")
    print(f"  Metadata.RegionCount : {md.get('RegionCount')}")

    problems = []
    for rname, region in nbt["Regions"].items():
        size, pos = region["Size"], region["Position"]
        w, h, l = abs(size["x"]), abs(size["y"]), abs(size["z"])
        palette = region["BlockStatePalette"]
        longs = region["BlockStates"]
        bits = max(2, (len(palette) - 1).bit_length())
        volume = w * h * l
        expected_longs = (volume * bits + 63) // 64
        print(f"\n  리전 '{rname}'  위치 {pos}  크기 {w}x{h}x{l} (부피 {volume})")
        print(f"    팔레트 {len(palette)}종 → {bits} bit/블록, long {len(longs)}개 (기대 {expected_longs})")
        if len(longs) != expected_longs:
            problems.append(f"long 배열 길이 불일치: {len(longs)} != {expected_longs}")
        if name_of(palette[0]) != "minecraft:air":
            problems.append(f"팔레트 0번이 air 가 아님: {name_of(palette[0])}")

        idx = unpack_states(longs, bits, volume)
        if max(idx) >= len(palette):
            problems.append(f"팔레트 범위를 넘는 인덱스 발견: {max(idx)} >= {len(palette)}")
        non_air = sum(1 for v in idx if v != 0)
        print(f"    비공기 블록 {non_air}개")
        if md.get("TotalBlocks") is not None and md["TotalBlocks"] != non_air:
            problems.append(f"TotalBlocks({md['TotalBlocks']}) != 실제 비공기({non_air})")

        from collections import Counter
        c = Counter(name_of(palette[v]) for v in idx if v != 0)
        print("    상위 블록:")
        for nm, n in c.most_common(8):
            print(f"      {nm:<58} {n:>4}")
    if problems:
        print("\n포맷 문제:")
        for p in problems:
            print("  !", p)
        return 1
    print("\n포맷 검증 통과: 헤더 / 팔레트 / 비트패킹 / 블록 수 모두 일관됨")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "blueprints/sugarcane_12.litematic"))
