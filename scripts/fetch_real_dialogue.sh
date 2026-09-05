#!/bin/zsh
# Fetch the freely licensed real recordings that scripts/dialogue_benchmark.py measures.
# Everything lands in ~/.cache/cumple/real-dialogue/ and nothing is redistributed by cumple.
#
#   Sintel (2010) and Tears of Steel (2012): Blender Foundation, CC BY 3.0. Both publish the
#     finished mix and a music-and-effects version without dialogue; Tears of Steel also ships
#     its 5.1 mix as six discrete mono AIFF files, a real delivery package.
#   Sprite Fright (2021): Blender Studio, CC BY 4.0.
#   His Girl Friday (1940) and Night of the Living Dead (1968): public domain, Internet Archive.
#   LibriVox, William Again: public domain narration.
#   NASA, Houston We Have a Podcast: a work of the U.S. government, public domain.
#   EBU SQAM (Tech 3253): the EBU's terms allow use as an R&D tool only.
#   Silero VAD model: Silero Team, MIT.
#
# Files are written to <name>.part and renamed when complete, so an interrupted run resumes
# and the benchmark never reads a half-downloaded file. About 1.9 GB in total.

set -u
C="${CUMPLE_CACHE:-$HOME/.cache/cumple}/real-dialogue"
mkdir -p "$C"/{sintel,tos/surround,sprite-fright,pd-films,nasa,librivox,sqam}

get() {  # get <url> <dest>
  local url="$1" dest="$2"
  if [[ -s "$dest" ]]; then echo "have  ${dest#$C/}"; return 0; fi
  echo "fetch ${dest#$C/}"
  if curl -sSL --retry 3 --retry-delay 5 -C - -m 7200 -o "$dest.part" "$url"; then
    mv "$dest.part" "$dest"
  else
    echo "FAILED $url" >&2
    return 1
  fi
}

get "https://media.xiph.org/sintel/sintel-master-51.flac"      "$C/sintel/sintel-master-51.flac"
get "https://media.xiph.org/sintel/sintel-master-st.flac"      "$C/sintel/sintel-master-st.flac"
get "https://media.xiph.org/sintel/sintel-m+e-st.flac"         "$C/sintel/sintel-m+e-st.flac"
get "https://media.xiph.org/sintel/sintel_trailer-audio.flac"  "$C/sintel/sintel_trailer-audio.flac"

get "https://download.blender.org/demo/movies/ToS/TOS_DVDSTEREOMIX.aif"           "$C/tos/TOS_DVDSTEREOMIX.aif"
get "https://download.blender.org/demo/movies/ToS/TOS_MUSIC%2BFX_NO_DIALOGUE.aif" "$C/tos/TOS_MUSIC+FX_NO_DIALOGUE.aif"
for ch in L R C LFE Ls Rs; do
  get "https://download.blender.org/demo/movies/ToS/surround/TOS_DVDSURROUND.$ch.aif" "$C/tos/surround/TOS_DVDSURROUND.$ch.aif"
done

get "https://archive.org/download/sprite-fright/Sprite%20Fright%20-%20Open%20Movie%20by%20Blender%20Studio-804p.mp4" "$C/sprite-fright/sprite_fright_804p.mp4"
get "https://archive.org/download/his_girl_friday/his_girl_friday.mp3"                          "$C/pd-films/his_girl_friday_1940.mp3"
get "https://archive.org/download/Night.Of.The.Living.Dead_1080p/NightOfTheLivingDead_DVD9.mp3" "$C/pd-films/night_of_the_living_dead_1968.mp3"
get "https://archive.org/download/williamagain_1902_librivox/williamagain_01_crompton_64kb.mp3" "$C/librivox/william_again_ch01.mp3"
get "https://traffic.megaphone.fm/NATIONALAERONAUTICSANDSPACEADMINISTRATION7649878096.mp3"      "$C/nasa/hwhap_national_lab_15.mp3"
get "https://qc.ebu.io/testmaterials/523/1/download/"                                           "$C/sqam/TECH3253_SQAM_FLAC.zip"

# Silero VAD v5 (Silero Team, MIT licence), the independent voice detector the benchmark compares
# against when onnxruntime is installed: uv run --with onnxruntime scripts/dialogue_benchmark.py
get "https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.onnx" "$C/../silero_vad.onnx"

echo "done: $(du -sh "$C" | cut -f1) in $C"
