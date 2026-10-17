#!/usr/bin/env python3
"""Export every DXF to vector PDF and SVG. Text becomes outlines (paths), never a raster image.

    python3 export_vector.py        reads dxf/ and legend/, writes drawings/
"""
import glob
import os

import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.config import BackgroundPolicy, ColorPolicy, Configuration
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

from dxf_common import SHEET_H, SHEET_W

HERE = os.path.dirname(os.path.abspath(__file__))
matplotlib.rcParams["svg.fonttype"] = "path"
matplotlib.rcParams["pdf.fonttype"] = 3


def export(dxf_path, out_base):
    doc = ezdxf.readfile(dxf_path)
    fig = plt.figure(figsize=(14, 14.0 * SHEET_H / SHEET_W))
    ax = fig.add_axes([0, 0, 1, 1])
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.BLACK)
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(doc.modelspace())
    ax.set_xlim(0, SHEET_W); ax.set_ylim(0, SHEET_H); ax.set_aspect("equal"); ax.axis("off")
    for ext in ("pdf", "svg"):
        fig.savefig("%s.%s" % (out_base, ext))
    plt.close(fig)


if __name__ == "__main__":
    out = os.path.join(HERE, "drawings")
    os.makedirs(out, exist_ok=True)
    files = sorted(glob.glob(os.path.join(HERE, "dxf", "*.dxf")) + glob.glob(os.path.join(HERE, "legend", "*.dxf")))
    for f in files:
        export(f, os.path.join(out, os.path.basename(f)[:-4]))
    print("wrote %d drawings (pdf + svg) to %s" % (len(files), out))
