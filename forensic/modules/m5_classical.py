# M5 Classical Indicators: double JPEG, resampling, and copy-move forgery detection with region maps.
# Why: Classical physics and frequency-domain traces complement provenance and neural detectors.
# Product Rule: No binary label. States: indicated / not_indicated / not_assessed. ELA is visualization only.
from __future__ import annotations
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import cv2
from PIL import Image
from sklearn.cluster import DBSCAN

from ..core.config import Config
from ..core.record import EvidenceRecord, make_failed_record, make_not_assessed_record

MODULE_NAME = "m5_classical"
MODULE_VERSION = "0.1.0"

_LIMITATIONS = [
    "Double JPEG: depends on Q1 != Q2 and aligned 8x8 grids; high secondary quality or re-sampling can attenuate histogram periodicity.",
    "Resampling: subsequent JPEG recompression, blurring, or noise injection can suppress linear interpolation periodicities.",
    "Copy-move: keypoint matching is ineffective in flat, textureless regions and can yield false alarms in repetitive natural textures (e.g. foliage, water ripples).",
    "ELA is included strictly as a visualisation aid and must never be treated as forensic proof or used for automated decision-making.",
    "Region maps and heatmaps are statistical indications of anomalies, not exact ground-truth pixel boundaries."
]


def _detect_double_jpeg(img_gray: np.ndarray) -> Tuple[str, float, float, Optional[np.ndarray]]:
    """
    Detect Double JPEG compression via DCT coefficient histogram periodicity.
    Returns: (state, periodicity_score, peak_ratio, block_heatmap)
    """
    h, w = img_gray.shape
    if h < 32 or w < 32:
        return "not_assessed", 0.0, 0.0, None

    h8, w8 = (h // 8) * 8, (w // 8) * 8
    img_cropped = img_gray[:h8, :w8].astype(np.float32) - 128.0

    blocks = img_cropped.reshape(h8 // 8, 8, w8 // 8, 8).transpose(0, 2, 1, 3)
    num_by, num_bx = blocks.shape[0], blocks.shape[1]

    dct_blocks = np.zeros_like(blocks)
    for i in range(num_by):
        for j in range(num_bx):
            dct_blocks[i, j] = cv2.dct(blocks[i, j])

    # Analyze low-to-mid AC coefficients
    ac_coords = [(0, 1), (1, 0), (1, 1), (0, 2), (2, 0), (1, 2), (2, 1), (2, 2)]
    peak_ratios = []

    for r, c in ac_coords:
        coeffs = np.round(dct_blocks[:, :, r, c].flatten()).astype(int)
        coeffs = coeffs[(coeffs >= -35) & (coeffs <= 35) & (coeffs != 0)]
        if len(coeffs) < 100:
            continue
        hist, _ = np.histogram(coeffs, bins=71, range=(-35.5, 35.5))
        hist_detrend = hist - np.mean(hist)
        fft_h = np.abs(np.fft.rfft(hist_detrend))
        if len(fft_h) > 6:
            pk = np.max(fft_h[2:]) / (np.mean(fft_h[2:]) + 1e-6)
            peak_ratios.append(float(pk))

    peak_ratio = float(np.mean(peak_ratios)) if peak_ratios else 1.0

    # Block boundary difference ratio
    diff_h = np.abs(np.diff(img_gray[:h8, :w8].astype(np.float32), axis=1))
    boundary_h = diff_h[:, 7::8]
    interior_h = diff_h[:, [k for k in range(diff_h.shape[1]) if k % 8 != 7]]
    b_ratio = float(np.mean(boundary_h) / (np.mean(interior_h) + 1e-6)) if boundary_h.size > 0 else 1.0

    # Combined periodicity score
    periodicity_score = round(peak_ratio * (b_ratio / 1.1), 4)

    # Threshold for double JPEG indication
    state = "indicated" if periodicity_score >= 3.6 or b_ratio > 1.35 else "not_indicated"

    # Block-level heatmap (variance of AC coefficients per block)
    block_ac_energy = np.mean(np.abs(dct_blocks[:, :, 1:4, 1:4]), axis=(2, 3))
    heatmap = cv2.resize(block_ac_energy, (w, h), interpolation=cv2.INTER_NEAREST)
    heatmap_norm = np.clip(heatmap / (np.percentile(heatmap, 95) + 1e-6), 0.0, 1.0)

    return state, periodicity_score, round(peak_ratio, 4), heatmap_norm


def _detect_resampling(img_gray: np.ndarray) -> Tuple[str, float, Optional[np.ndarray]]:
    """
    Detect resampling (interpolation periodicities) using Gallagher's 2nd-difference derivative.
    Returns: (state, spectral_peak_ratio, resampling_heatmap)
    """
    h, w = img_gray.shape
    if h < 64 or w < 64:
        return "not_assessed", 0.0, None

    img_f = img_gray.astype(np.float32)

    # Horizontal and vertical second differences
    d2_h = np.diff(img_f, n=2, axis=1)
    d2_v = np.diff(img_f, n=2, axis=0)

    # Average energy across axes
    h_energy = np.abs(d2_h)
    v_energy = np.abs(d2_v)

    # 1D FFT along rows and columns
    fft_h = np.abs(np.fft.rfft(np.mean(h_energy, axis=0) - np.mean(h_energy)))
    fft_v = np.abs(np.fft.rfft(np.mean(v_energy, axis=1) - np.mean(v_energy)))

    peak_h = float(np.max(fft_h[4:-4]) / (np.mean(fft_h[4:-4]) + 1e-6)) if len(fft_h) > 12 else 1.0
    peak_v = float(np.max(fft_v[4:-4]) / (np.mean(fft_v[4:-4]) + 1e-6)) if len(fft_v) > 12 else 1.0

    spectral_peak_ratio = float(max(peak_h, peak_v))

    # Threshold: periodic interpolation creates pronounced spectral peaks (> 10.0)
    state = "indicated" if spectral_peak_ratio >= 10.5 else "not_indicated"

    # Local windowed variance of 2nd derivative for region map
    win_size = 32
    step = 16
    heat_h = (h - win_size) // step + 1
    heat_w = (w - win_size) // step + 1

    local_map = np.zeros((max(1, heat_h), max(1, heat_w)), dtype=np.float32)
    for i in range(heat_h):
        for j in range(heat_w):
            patch = img_f[i * step : i * step + win_size, j * step : j * step + win_size]
            d2_patch = np.diff(patch, n=2, axis=1)
            local_map[i, j] = float(np.var(np.abs(d2_patch)))

    heatmap_resized = cv2.resize(local_map, (w, h), interpolation=cv2.INTER_LINEAR)
    heatmap_norm = np.clip(heatmap_resized / (np.percentile(heatmap_resized, 95) + 1e-6), 0.0, 1.0)

    return state, round(spectral_peak_ratio, 4), heatmap_norm


def _detect_copy_move(img_rgb: np.ndarray) -> Tuple[str, int, int, List[Dict[str, Any]], Optional[np.ndarray]]:
    """
    Detect copy-move manipulation via SIFT keypoint matching, distance filtering,
    and geometric displacement clustering with DBSCAN.
    Returns: (state, pairs_count, clusters_count, bounding_boxes, mask)
    """
    h, w, _ = img_rgb.shape
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

    sift = cv2.SIFT_create(nfeatures=1500)
    kps, descs = sift.detectAndCompute(gray, None)

    if descs is None or len(descs) < 12:
        return "not_assessed", 0, 0, [], None

    bf = cv2.BFMatcher(cv2.NORM_L2)
    matches = bf.knnMatch(descs, descs, k=3)

    valid_pairs = []
    min_spatial_dist = 25.0
    ratio_thresh = 0.75

    for m in matches:
        if len(m) < 3:
            continue
        # m[0] is self match (distance=0)
        p1, p2 = m[1], m[2]
        if p1.distance < ratio_thresh * p2.distance:
            idx1, idx2 = p1.queryIdx, p1.trainIdx
            pt1 = np.array(kps[idx1].pt)
            pt2 = np.array(kps[idx2].pt)
            if np.linalg.norm(pt1 - pt2) >= min_spatial_dist:
                pair = tuple(sorted([idx1, idx2]))
                if pair not in valid_pairs:
                    valid_pairs.append(pair)

    if len(valid_pairs) < 4:
        return "not_indicated", len(valid_pairs), 0, [], None

    # Compute canonical displacement vectors
    displacements = []
    pt_pairs = []
    for idx1, idx2 in valid_pairs:
        pt1 = np.array(kps[idx1].pt)
        pt2 = np.array(kps[idx2].pt)
        if pt1[0] > pt2[0] or (pt1[0] == pt2[0] and pt1[1] > pt2[1]):
            pt1, pt2 = pt2, pt1
        displacements.append(pt2 - pt1)
        pt_pairs.append((pt1, pt2))

    # Cluster displacements via DBSCAN
    db = DBSCAN(eps=18.0, min_samples=4).fit(np.array(displacements))
    labels = db.labels_
    unique_labels = set(labels) - {-1}

    clusters_count = len(unique_labels)
    bounding_boxes = []
    mask = np.zeros((h, w), dtype=np.uint8)

    if clusters_count > 0:
        for lbl in unique_labels:
            cluster_indices = np.where(labels == lbl)[0]
            pts_src = np.array([pt_pairs[k][0] for k in cluster_indices])
            pts_dst = np.array([pt_pairs[k][1] for k in cluster_indices])

            # Draw circles around matched keypoints on the mask
            for pt in pts_src:
                cv2.circle(mask, (int(pt[0]), int(pt[1])), 16, 255, -1)
            for pt in pts_dst:
                cv2.circle(mask, (int(pt[0]), int(pt[1])), 16, 255, -1)

            # Compute bounding boxes for donor and recipient
            x1_s, y1_s, w_s, h_s = cv2.boundingRect(pts_src.astype(np.float32))
            x1_d, y1_d, w_d, h_d = cv2.boundingRect(pts_dst.astype(np.float32))

            bounding_boxes.append({
                "cluster_id": int(lbl),
                "inlier_count": len(cluster_indices),
                "donor_box": [int(x1_s), int(y1_s), int(w_s), int(h_s)],
                "recipient_box": [int(x1_d), int(y1_d), int(w_d), int(h_d)]
            })

    state = "indicated" if clusters_count > 0 else "not_indicated"
    return state, len(valid_pairs), clusters_count, bounding_boxes, mask


def _compute_ela(img_rgb: np.ndarray, quality: int = 90, scale: int = 15) -> Tuple[float, float, np.ndarray]:
    """
    Error Level Analysis (ELA) visualization map.
    ELA is strictly a visualisation aid and is never used as proof of manipulation.
    """
    pil_img = Image.fromarray(img_rgb)
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    recompressed = np.array(Image.open(buf).convert("RGB"))

    diff = np.abs(img_rgb.astype(np.int16) - recompressed.astype(np.int16))
    amplified = np.clip(diff * scale, 0, 255).astype(np.uint8)
    mean_error = float(np.mean(diff))
    max_error = float(np.max(diff))
    return round(mean_error, 4), round(max_error, 4), amplified


def run(image_path: Path, config: Config) -> EvidenceRecord:
    """
    Run Module M5 Classical Indicators:
      1. Double JPEG compression detection (DCT histogram periodicity).
      2. Resampling / interpolation detection (2nd difference spectral peak).
      3. Copy-move forgery detection (SIFT + 2NN + spatial displacement clustering).
      4. Error Level Analysis (visualization only).

    Returns an EvidenceRecord with typed observations, interpretations, region maps,
    and explicit limitations. Never outputs binary real/fake verdicts.
    """
    image_path = Path(image_path)
    from ..core.hashing import compute_sha256

    try:
        sha256 = compute_sha256(image_path)
    except Exception as exc:
        return make_failed_record(MODULE_NAME, MODULE_VERSION, "unknown", str(exc))

    try:
        with Image.open(image_path) as img:
            rgb = np.array(img.convert("RGB"))
            gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            h, w = gray.shape

        # 1. Double JPEG
        dj_state, dj_score, dj_peak, dj_heatmap = _detect_double_jpeg(gray)

        # 2. Resampling
        rs_state, rs_ratio, rs_heatmap = _detect_resampling(gray)

        # 3. Copy-Move
        cm_state, cm_pairs, cm_clusters, cm_boxes, cm_mask = _detect_copy_move(rgb)

        # 4. ELA (visualization only)
        ela_mean, ela_max, ela_vis = _compute_ela(rgb, quality=90, scale=15)

        # Construct typed observations
        observations: Dict[str, Any] = {
            "double_jpeg": {
                "status": dj_state,
                "periodicity_score": dj_score,
                "ac_fft_peak_ratio": dj_peak,
            },
            "resampling": {
                "status": rs_state,
                "spectral_peak_ratio": rs_ratio,
            },
            "copy_move": {
                "status": cm_state,
                "candidate_pairs_count": cm_pairs,
                "spatial_clusters_count": cm_clusters,
                "detected_regions_count": len(cm_boxes),
            },
            "ela": {
                "mean_absolute_difference": ela_mean,
                "max_absolute_difference": ela_max,
                "note": "Visualisation only. Never used as proof or decision criterion."
            }
        }

        # Overall classical indicator synthesis (non-averaged)
        any_indicated = any(s == "indicated" for s in [dj_state, rs_state, cm_state])
        all_not_assessed = all(s == "not_assessed" for s in [dj_state, rs_state, cm_state])

        overall_state = "indicated" if any_indicated else ("not_assessed" if all_not_assessed else "not_indicated")

        interpretation = {
            "double_jpeg": dj_state,
            "resampling": rs_state,
            "copy_move": cm_state,
            "classical_indicators_summary": overall_state,
            "note": "Classical indicators measure independent physical/mathematical traces. No scores are averaged."
        }

        # Serialized region maps (preview data)
        regions: List[Dict[str, Any]] = [
            {
                "indicator": "double_jpeg",
                "type": "block_energy_heatmap",
                "shape": [h, w],
                "mean_intensity": float(np.mean(dj_heatmap)) if dj_heatmap is not None else 0.0
            },
            {
                "indicator": "resampling",
                "type": "interpolation_variance_heatmap",
                "shape": [h, w],
                "mean_intensity": float(np.mean(rs_heatmap)) if rs_heatmap is not None else 0.0
            },
            {
                "indicator": "copy_move",
                "type": "binary_keypoint_mask",
                "shape": [h, w],
                "clusters": cm_boxes
            },
            {
                "indicator": "ela",
                "type": "recompression_error_map",
                "shape": [h, w, 3],
                "note": "Visualisation only"
            }
        ]

        return EvidenceRecord(
            input_sha256=sha256,
            engine=MODULE_NAME,
            version=MODULE_VERSION,
            method="double_jpeg_dct + resampling_pderivative + copymove_sift_dbscan + ela_vis",
            parameters={
                "dct_block_size": 8,
                "resampling_p_order": 2,
                "sift_features": 1500,
                "copymove_min_dist_px": 25.0,
                "copymove_dbscan_eps": 18.0,
                "ela_quality": 90,
                "ela_scale": 15
            },
            status="completed",
            observations=observations,
            interpretation=interpretation,
            regions=regions,
            confidence=None,
            limitations=_LIMITATIONS
        )

    except Exception as exc:
        return make_failed_record(MODULE_NAME, MODULE_VERSION, sha256, f"M5 execution error: {exc}")
