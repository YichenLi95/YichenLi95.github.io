import argparse
import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from sam2.build_sam import build_sam2matting_video_predictor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--original-images", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path("checkpoints/SAM2Matting-SAM2.1Base+.pt"),
    )
    parser.add_argument("--frame-idx", type=int, default=0)
    parser.add_argument(
        "--bbox",
        type=float,
        nargs=4,
        required=True,
        metavar=("X1", "Y1", "X2", "Y2"),
    )
    parser.add_argument("--alpha-threshold", type=float, default=0.10)
    args = parser.parse_args()

    frame_files = sorted(
        path
        for path in args.images.iterdir()
        if path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )
    if not frame_files:
        raise RuntimeError(f"No images found in {args.images}")
    original_images = args.original_images or args.images
    files = sorted(
        path
        for path in original_images.iterdir()
        if path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )
    if len(frame_files) != len(files):
        raise RuntimeError(
            f"Frame/original count mismatch: {len(frame_files)} vs {len(files)}"
        )
    if not 0.0 < args.alpha_threshold < 1.0:
        raise ValueError("--alpha-threshold must be between 0 and 1")

    alpha_dir = args.output_root / "alpha"
    mask_dir = args.output_root / "binary_masks"
    preview_dir = args.output_root / "previews"
    for directory in (alpha_dir, mask_dir, preview_dir):
        directory.mkdir(parents=True, exist_ok=True)

    predictor = build_sam2matting_video_predictor(
        "configs/sam2matting-sam2.1base+.yaml",
        str(args.checkpoint),
        device="cuda",
    )
    state = predictor.init_state(video_path=str(args.images))
    predictor.reset_state(state)
    predictor.add_new_points_or_box(
        inference_state=state,
        frame_idx=args.frame_idx,
        obj_id=1,
        box=np.asarray(args.bbox, dtype=np.float32),
    )

    report = {
        "images": [],
        "alpha_threshold": args.alpha_threshold,
        "seed_frame": files[args.frame_idx].name,
        "seed_bbox": args.bbox,
    }
    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
        for index, _, _, alpha, _ in predictor.propagate_in_video(state):
            image_path = files[index]
            with Image.open(image_path) as image:
                rgb = np.asarray(image.convert("RGB"))
            alpha_np = alpha.detach().float().cpu().numpy().squeeze().clip(0.0, 1.0)
            if alpha_np.shape != rgb.shape[:2]:
                alpha_np = np.asarray(
                    Image.fromarray(alpha_np, mode="F").resize(
                        (rgb.shape[1], rgb.shape[0]), Image.Resampling.BILINEAR
                    )
                )
            mask_u8 = (alpha_np >= args.alpha_threshold).astype(np.uint8) * 255
            alpha_u8 = (alpha_np * 255.0).round().astype(np.uint8)
            stem = image_path.stem
            Image.fromarray(alpha_u8, mode="L").save(alpha_dir / f"{stem}.png")
            Image.fromarray(mask_u8, mode="L").save(mask_dir / f"{stem}.png")
            green = np.array([0, 255, 0], dtype=np.float32)
            preview = (
                rgb.astype(np.float32) * alpha_np[..., None]
                + green * (1.0 - alpha_np[..., None])
            ).round().astype(np.uint8)
            Image.fromarray(preview, mode="RGB").save(
                preview_dir / f"{stem}.jpg", quality=92
            )
            report["images"].append(
                {
                    "name": image_path.name,
                    "size": [int(rgb.shape[1]), int(rgb.shape[0])],
                    "foreground_fraction": float(mask_u8.mean() / 255.0),
                }
            )
            print(f"[{index + 1}/{len(files)}] {image_path.name}")

    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
