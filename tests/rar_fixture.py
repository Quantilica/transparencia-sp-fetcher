"""Gerador de RAR v4 (método "store") para os testes, sem binário externo.

O formato RAR 2.9 sem compressão é simples o bastante para ser montado à mão:
marcador, cabeçalho principal e um cabeçalho de arquivo por membro, cada um com CRC16
(baixos 16 bits do CRC32 do cabeçalho). A libarchive valida esses CRCs e o CRC32 dos
dados, então um arquivo corrompido aqui é detectado de verdade.
"""

from __future__ import annotations

import struct
import zlib

_MARKER = b"Rar!\x1a\x07\x00"
_END_BLOCK = bytes.fromhex("c43d7b00400700")


def make_rar4(members: list[tuple[str, bytes]]) -> bytes:
    out = bytearray(_MARKER)
    main = struct.pack("<BHH", 0x73, 0, 13) + b"\x00" * 6
    out += struct.pack("<H", zlib.crc32(main) & 0xFFFF) + main
    for name, data in members:
        nb = name.encode("latin-1")
        head = struct.pack("<BHH", 0x74, 0x8000, 32 + len(nb)) + struct.pack(
            "<IIBIIBBHI",
            len(data),  # PACK_SIZE
            len(data),  # UNP_SIZE
            3,  # HOST_OS (unix)
            zlib.crc32(data) & 0xFFFFFFFF,
            0x5A000000,  # FTIME
            20,  # UNP_VER
            0x30,  # METHOD: store
            len(nb),
            0x20,  # ATTR
        )
        out += struct.pack("<H", zlib.crc32(head + nb) & 0xFFFF) + head + nb + data
    out += _END_BLOCK
    return bytes(out)
