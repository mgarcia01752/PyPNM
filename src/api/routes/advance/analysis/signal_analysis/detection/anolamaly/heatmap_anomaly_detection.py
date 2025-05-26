# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import numpy as np
from typing import List, Tuple, Dict, Any

class HeatmapAnomalyDetector:
    """
    Detect anomalies in a 2D array via global z-score thresholding
    and extract bounding boxes around each connected blob.

    Attributes:
      data (np.ndarray):         2D input array of measurements.
      threshold (float):         z-score cutoff T (default 3.0).
      zmap (np.ndarray):         computed z-score map.
      mask (np.ndarray):         boolean mask where |z| > T.
      boxes (List[Tuple…]]):     list of (row_min, col_min, row_max, col_max).
    """
    def __init__(self, data: np.ndarray, threshold: float = 3.0):
        self.data = np.asarray(data, dtype=float)
        if self.data.ndim != 2:
            raise ValueError("Input must be a 2-D array.")
        self.threshold = threshold
        self.zmap: np.ndarray = None  # to be computed
        self.mask: np.ndarray = None
        self.boxes: List[Tuple[int,int,int,int]] = []

    def compute_zmap(self) -> np.ndarray:
        μ = self.data.mean()
        σ = self.data.std()
        # avoid divide-by-zero
        self.zmap = np.zeros_like(self.data) if σ == 0 else (self.data - μ) / σ
        return self.zmap

    def detect(self) -> np.ndarray:
        """Apply threshold to form boolean anomaly mask."""
        if self.zmap is None:
            self.compute_zmap()
        self.mask = np.abs(self.zmap) > self.threshold
        return self.mask

    def find_boxes(self) -> List[Tuple[int,int,int,int]]:
        """
        Flood-fill the mask to find connected components (4-connectivity)
        and compute their bounding boxes.
        """
        if self.mask is None:
            self.detect()

        visited = np.zeros_like(self.mask, bool)
        rows, cols = self.data.shape
        boxes: List[Tuple[int,int,int,int]] = []

        def neighbors(r, c):
            for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < rows and 0 <= cc < cols:
                    yield rr, cc

        for i in range(rows):
            for j in range(cols):
                if self.mask[i, j] and not visited[i, j]:
                    # start new component
                    rmin = rmax = i
                    cmin = cmax = j
                    stack = [(i, j)]
                    visited[i, j] = True

                    while stack:
                        r, c = stack.pop()
                        rmin, rmax = min(rmin, r), max(rmax, r)
                        cmin, cmax = min(cmin, c), max(cmax, c)
                        for rr, cc in neighbors(r, c):
                            if self.mask[rr, cc] and not visited[rr, cc]:
                                visited[rr, cc] = True
                                stack.append((rr, cc))

                    boxes.append((rmin, cmin, rmax, cmax))

        self.boxes = boxes
        return boxes

    def to_json(self) -> Dict[str, Any]:
        """
        Package the threshold and boxes into a JSON-friendly dict.
        """
        return {
            "threshold": self.threshold,
            "boxes": [
                {"row_min": r0, "col_min": c0, "row_max": r1, "col_max": c1}
                for r0, c0, r1, c1 in self.boxes
            ]
        }
