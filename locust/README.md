# LOCUST Starter Project

This folder is a self-contained local presentation and reproduction map for the LOCUST native-resolution 3D Gaussian reconstruction. The website is in `site/`; the original DOCX and reproduction code stay outside the public web root.

## Run the local website

Run:

```powershell
cd "D:\codex_proj\ecoPlants\3DGaussian\starter proj"
.\start-site.ps1
```

Open `http://127.0.0.1:4173/`. The page is fixed to the selected 50K output and loads the centered SOG directly from `site/assets/`, avoiding the remote 3003 transfer. The website server binds to `127.0.0.1` only.

## Reproduction code map

1. Metashape exports the multi-view image set and camera model. The reconstruction used 45 source images, with 44 registered images retained for the native-resolution run.
2. COLMAP verifies the camera reconstruction and provides the fixed split: 38 training images and 6 held-out images.
3. `pipeline/run_masks.py` runs SAM2Matting foreground-mask propagation. The prompt and alpha threshold should be checked visually before training.
4. `pipeline/training_config.json` records 50,000 iterations, a 2,000,000 Gaussian cap, MRNF, PPISP, evaluation and save at iteration 50,000, and `ppisp_use_controller: false`.
5. `pipeline/run_reconstruction.sh` launches native-resolution MRNF + PPISP with `--resize_factor 1`, `--max-cap 2000000`, `--iter 50000`, `--eval`, and `--undistort`.
6. `scripts/recenter_ply.py` makes a local copy and translates XYZ by the bounding-box center. It does not change the source PLY.
7. The centered PLY is converted to `site/assets/locust_original45_50k.sog` with `@playcanvas/splat-transform`; SOG is the GitHub Pages delivery asset.

## Important paths

The reconstruction source is kept locally at `local-assets/locust_original45_50k_centered.ply`. The website targets the compressed delivery asset:

`site/assets/locust_original45_50k.sog`

The supplied report is included unchanged under `docs/` for local project reference. It is outside the public `site/` directory and is not downloadable from the website. The large centered PLY is kept outside the public site so the GitHub Pages repository stays within GitHub's file limits.

## Source ownership

Files copied from the existing reconstruction workflow are marked in the file history and retain their original logic: `pipeline/run_masks.py`, `pipeline/run_reconstruction.sh`, `pipeline/training_config.json`, and `pipeline/supersplat_output_browser_server.py`. Files written for this starter project are `site/index.html`, `site/styles.css`, `site/app.js`, `scripts/recenter_ply.py`, `start-site.ps1`, and this README. The only substantive new processing step is the local, reversible coordinate translation in `scripts/recenter_ply.py`.
