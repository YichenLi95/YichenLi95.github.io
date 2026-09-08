const target = 'LOCUST_METASHAPE_ORIGINAL45_FULLRES_2M_50K_GROW30K_MASK_BPLUS_NOCTRL_PLY';
const iteration = '50000';
const viewer = document.querySelector('#splat');
const localSog = 'assets/locust_original45_50k.sog';
const viewerUrl = `viewer/index.html?content=${encodeURIComponent(localSog)}&settings=${encodeURIComponent('viewer/settings.json')}&lang=en`;
viewer.src = viewerUrl;
document.querySelector('#standalone').href = viewerUrl;
viewer.addEventListener('load', () => document.querySelector('#viewerFallback').style.display = 'none');
document.querySelector('#reportContent').innerHTML = `<h3 class="sheet-title">LOCUST 3D Gaussian Reconstruction</h3><p>A multi-view reconstruction workflow designed around thin-structure preservation, background cleanup, and novel-view evaluation.</p><div class="timeline"><div class="timeline-row"><b>August 2026</b><span>Built the reconstruction and evaluation pipeline with registered imagery, COLMAP inputs, and a fixed holdout protocol.</span></div><div class="timeline-row"><b>Late August</b><span>Registered 44 of 45 images and trained the native-resolution 2M-cap MRNF plus PPISP model with the controller disabled.</span></div><div class="timeline-row"><b>Result</b><span>38 training views, 6 held-out views · PSNR 23.062487 · SSIM 0.887327.</span></div></div>`;
