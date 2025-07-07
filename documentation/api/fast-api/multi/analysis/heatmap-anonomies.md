# Anomaly Detection in 2D Arrays

This guide describes a pipeline for detecting and localizing anomalous regions in a 2D numerical array (e.g., a heat map) by thresholding its global z-score and extracting bounding boxes around connected anomalies.


## Mathematical Formulation

Given an \$M \times N\$ array of values \$X\_{i,j}\$:

1. **Global Mean**:

   $$
   \mu = \frac{1}{MN} \sum_{i=1}^M\sum_{j=1}^N X_{i,j}
   $$

2. **Global Standard Deviation**:

   $$
   \sigma = \sqrt{\frac{1}{MN} \sum_{i=1}^M\sum_{j=1}^N (X_{i,j} - \mu)^2}
   $$

3. **Z-Score Map**:

   $$
   z_{i,j} = \frac{X_{i,j} - \mu}{\sigma}
   $$

4. **Anomaly Mask** (for threshold \$T\$):

   $$
   \text{mask}_{i,j} = \begin{cases}
     1, & \text{if } |z_{i,j}| > T \\
     0, & \text{otherwise}
   \end{cases}
   $$

5. **Bounding Box Extraction** for each connected component (4‑connectivity):

   $$
   \text{row}_{\min} = \min\{i : \text{mask}_{i,j} = 1\} \\
   \text{row}_{\max} = \max\{i : \text{mask}_{i,j} = 1\} \\
   \text{col}_{\min} = \min\{j : \text{mask}_{i,j} = 1\} \\
   \text{col}_{\max} = \max\{j : \text{mask}_{i,j} = 1\}
   $$


## JSON Output Format

The detection function returns a JSON object with the threshold and a list of bounding boxes:

```json
{
  "threshold": 3.0,
  "boxes": [
    { "row_min": 10, "col_min": 20, "row_max": 12, "col_max": 22 },
    { "row_min": 35, "col_min": 40, "row_max": 37, "col_max": 42 }
  ]
}
```

* **threshold**: z-score cutoff \$T\$
* **boxes**: array of detected regions with top-left \$(\text{row}*{\min}, \text{col}*{\min})\$ and bottom-right \$(\text{row}*{\max}, \text{col}*{\max})\$ coordinates


## Algorithm Steps

1. **Compute statistics**

   * Calculate global mean \$\mu\$ and standard deviation \$\sigma\$.

2. **Create anomaly mask**

   * Compute z-score map and apply threshold \$T\$.

3. **Connected-component labeling**

   * Identify distinct anomaly clusters using 4‑connectivity.

4. **Extract bounding boxes**

   * For each cluster, compute \$\min\$/\$\max\$ row and column indices.

5. **Return results**

   * Return \$T\$ and all bounding boxes in JSON.


> 💡 **Tip:** Choose the threshold \$T\$ based on expected noise (e.g., 3–4 standard deviations). Use 8‑connectivity if you want diagonally-connected anomalies grouped together.
