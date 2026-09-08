#!/usr/bin/env bash
set -uo pipefail
root=/home/ecoplants/lyc/3Dgaussians
code="$root/lichtfeld_mrnf_ppisp_locust_version1"
data="$root/datasets/LOCUST_METASHAPE_ORIGINAL"
config="$root/datasets/LOCUST/metashape_exports/train_fullres_2m_50k_grow30k_mask_bplus_noctrl.json"
output="$root/outputs/version1/L1_MRNF_PPISP_LOCUST_METASHAPE_ORIGINAL45_RUNTIME_UNDISTORT_FULLRES_2M_50K_GROW30K_MASK_BPLUS_NOCTRL"
log_dir="$code/logs"
log="$log_dir/metashape_original45_fullres_2m_50k_grow30k_mask_bplus_noctrl.log"
exit_file="$log_dir/metashape_original45_fullres_2m_50k_grow30k_mask_bplus_noctrl.exit"
pid_file="$log_dir/metashape_original45_fullres_2m_50k_grow30k_mask_bplus_noctrl.pid"
mkdir -p "$log_dir" "$root/tmp/lichtfeld_locust"
if [[ -e "$output" || -e "$exit_file" || -e "$pid_file" ]]; then exit 2; fi
printf '%s\n' "$$" > "$pid_file"
export LFS_TEMP_DIR="$root/tmp/lichtfeld_locust"
"$code/build/LichtFeld-Studio" --headless --train --safe-mode --no-splash --data-path "$data" --output-path "$output" --images images --test-every 8 --resize_factor 1 --max-width 0 --strategy mrnf --config "$config" --iter 50000 --max-cap 2000000 --ppisp --eval --undistort > "$log" 2>&1
rc=$?
printf '%s\n' "$rc" > "$exit_file"
exit "$rc"
