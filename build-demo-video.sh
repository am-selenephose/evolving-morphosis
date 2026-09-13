#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "$0")" && pwd)"
demo_dir="$root_dir/demo"
font="/usr/share/fonts/noto/NotoSans-Regular.ttf"
bold="/usr/share/fonts/noto/NotoSans-Bold.ttf"

mkdir -p "$demo_dir"
rsvg-convert -w 1920 -h 1040 "$root_dir/architecture.svg" -o "$demo_dir/architecture.png"

make_slide() {
  local name="$1"
  local heading="$2"
  local body="$3"
  convert -size 1920x1080 xc:'#0b1020' \
    -fill '#7dd3fc' -font "$bold" -pointsize 64 -gravity northwest -annotate +120+120 "$heading" \
    -fill '#eef2ff' -font "$font" -pointsize 38 -interline-spacing 16 -annotate +120+280 "$body" \
    "$demo_dir/$name.png"
}

make_slide title 'ActionQueue' $'Evidence in. Accountable decisions out.\n\nA Strands Agents SDK professional-work agent'
make_slide input 'Noisy packet in' $'Synthetic fixture includes:\n\n• valid opportunities\n• a duplicate\n• an expired listing\n• an incomplete record\n\nNo credentials or private data required.'
make_slide result 'Evidence-backed queue out' $'2 viable records ranked\n1 expired record rejected\n1 duplicate removed\n1 invalid record rejected\n\nSources and SHA-256 evidence fingerprints retained.'
make_slide gate 'Consequential actions stop here' $'APPLY  •  PUBLISH  •  SEND\nSIGN   •  SPEND    •  SUBMIT\n\nDEFAULT-DENY — explicit human approval required'
make_slide verify 'Reproducible by design' $'Real Strands tool-use loop\nDeterministic credential-free demo model\nValidation + expiry + deduplication tests\nByte-stable replay verification\n\nMIT licensed • ./verify.sh'

ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -t 6 -i "$demo_dir/title.png" \
  -loop 1 -t 9 -i "$demo_dir/input.png" \
  -loop 1 -t 11 -i "$demo_dir/architecture.png" \
  -loop 1 -t 13 -i "$demo_dir/result.png" \
  -loop 1 -t 10 -i "$demo_dir/gate.png" \
  -loop 1 -t 7 -i "$demo_dir/verify.png" \
  -f lavfi -t 56 -i 'sine=frequency=110:sample_rate=48000' \
  -filter_complex \
  "[0:v]fps=24,format=yuv420p[v0];[1:v]fps=24,format=yuv420p[v1];[2:v]pad=1920:1080:0:20:color=#0b1020,fps=24,format=yuv420p[v2];[3:v]fps=24,format=yuv420p[v3];[4:v]fps=24,format=yuv420p[v4];[5:v]fps=24,format=yuv420p[v5];[v0][v1][v2][v3][v4][v5]concat=n=6:v=1:a=0[v];[6:a]volume=0.012,afade=t=in:st=0:d=2,afade=t=out:st=53:d=3[a]" \
  -map '[v]' -map '[a]' -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p \
  -c:a aac -b:a 96k -movflags +faststart "$demo_dir/actionqueue-demo.mp4"

ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height,r_frame_rate \
  -of default=noprint_wrappers=1 "$demo_dir/actionqueue-demo.mp4"
