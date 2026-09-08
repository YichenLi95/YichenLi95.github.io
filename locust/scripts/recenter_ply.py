"""Translate a binary PLY point cloud so its XYZ bounding-box center is zero."""

import argparse
import struct
from pathlib import Path


TYPE_FORMAT = {"char": "b", "uchar": "B", "short": "h", "ushort": "H", "int": "i", "uint": "I", "float": "f", "double": "d"}


def read_header(handle):
    lines = []
    vertex_count = None
    properties = []
    in_vertex = False
    while True:
        line = handle.readline()
        if not line:
            raise ValueError("PLY header has no end_header")
        lines.append(line)
        text = line.decode("ascii").strip()
        if text.startswith("element vertex "):
            vertex_count = int(text.split()[-1])
            in_vertex = True
        elif text.startswith("element "):
            in_vertex = False
        elif in_vertex and text.startswith("property "):
            parts = text.split()
            if len(parts) == 3 and parts[1] in TYPE_FORMAT:
                properties.append((parts[2], TYPE_FORMAT[parts[1]]))
        elif text == "end_header":
            break
    if vertex_count is None or not properties:
        raise ValueError("Missing vertex element or properties")
    names = [name for name, _ in properties]
    if not all(name in names for name in ("x", "y", "z")):
        raise ValueError("Vertex properties do not include x, y, z")
    return b"".join(lines), vertex_count, properties


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with args.source.open("rb") as src:
        header, count, properties = read_header(src)
    formats = "<" + "".join(fmt for _, fmt in properties)
    record_size = struct.calcsize(formats)
    offsets = {name: struct.calcsize("<" + "".join(fmt for _, fmt in properties[:index])) for index, (name, _) in enumerate(properties)}
    xyz_offsets = [offsets[name] for name in ("x", "y", "z")]
    mins = [float("inf")] * 3
    maxs = [float("-inf")] * 3
    with args.source.open("rb") as src:
        read_header(src)
        for _ in range(count):
            record = src.read(record_size)
            if len(record) != record_size:
                raise ValueError("PLY data ends before the vertex count")
            for axis, offset in enumerate(xyz_offsets):
                value = struct.unpack_from("<f", record, offset)[0]
                mins[axis] = min(mins[axis], value)
                maxs[axis] = max(maxs[axis], value)
    center = [(low + high) / 2.0 for low, high in zip(mins, maxs)]
    with args.output.open("wb") as dst:
        dst.write(header)
        with args.source.open("rb") as src:
            read_header(src)
            for _ in range(count):
                data = bytearray(src.read(record_size))
                if len(data) != record_size:
                    raise ValueError("PLY data ends before the vertex count")
                for axis, offset in enumerate(xyz_offsets):
                    value = struct.unpack_from("<f", data, offset)[0] - center[axis]
                    struct.pack_into("<f", data, offset, value)
                dst.write(data)
    print(f"vertices={count}")
    print(f"original_bbox_min={mins}")
    print(f"original_bbox_max={maxs}")
    print(f"translation={[-value for value in center]}")
    print(f"output={args.output}")


if __name__ == "__main__":
    main()
