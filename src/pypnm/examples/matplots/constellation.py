#! /usr/bin/env python3

from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia
import numpy as np

from pypnm.config.system_config_settings import SystemConfigSettings
from pypnm.lib.matplot.manager import MatplotManager, PlotConfig
from pypnm.lib.qam.lut_mgr import QamLutManager
from pypnm.lib.qam.types import QamModulation
from pypnm.lib.types import ComplexArray

# Get QAM hard-decision points
qlm = QamLutManager()
hda = qlm.get_hard_decisions(QamModulation.QAM_4)
print("Hard Decisions for QAM_4:", hda)

# Generate pseudo soft samples: each hard point jittered with Gaussian noise
rng = np.random.default_rng(seed=1234)
soft_psudo: ComplexArray = []
for (ix, qy) in hda:
    # add a few noisy samples per hard symbol
    for _ in range(50):
        dx, dy = rng.normal(0, 0.3), rng.normal(0, 0.3)  # adjust noise stddev
        soft_psudo.append((ix + dx, qy + dy))

# Build config
cfg = PlotConfig(
    title="Constellation QAM_4 with Soft Decisions",
    qam=QamModulation.QAM_4,
    hard=hda,
    soft=soft_psudo,
)

# Plot constellation
mgr = MatplotManager(SystemConfigSettings.png_dir)
png_path = mgr.plot_constellation(None, "qam4_constellation.png", cfg=cfg)
print("Saved constellation:", png_path)
