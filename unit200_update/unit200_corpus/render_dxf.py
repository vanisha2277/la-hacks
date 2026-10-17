#!/usr/bin/env python3
"""Render DXF files to PNG (and optionally PDF) for eyeballing: python3 render_dxf.py <dxf> <out.png>"""
import sys

import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy


def render(dxf_path, out_path, dpi=130):
    doc = ezdxf.readfile(dxf_path)
    fig = plt.figure(figsize=(14, 10.6))
    ax = fig.add_axes([0, 0, 1, 1])
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.BLACK)
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(doc.modelspace())
    ax.set_xlim(0, 1000); ax.set_ylim(0, 760); ax.set_aspect("equal")
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2])
