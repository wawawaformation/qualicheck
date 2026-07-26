#!/usr/bin/env bash
# traite_son.sh — chaîne voix : extraire -> débruiter (ventilo) -> compresser -> normaliser
#
# Usage :
#   ./traite_son.sh            # traite valide1..4.mkv -> son1..4.wav (à -12 LUFS)
#   LUFS=-14 ./traite_son.sh   # cible -14 LUFS
#   FORMAT=flac ./traite_son.sh # sortie en .flac au lieu de .wav
#   ./traite_son.sh valide2.mkv # un seul fichier
#
# Ordre de la chaîne (important) :
#   1) extraction audio
#   2) highpass 80 Hz   -> coupe le ronflement grave
#   3) afftdn           -> réduction du bruit de ventilo (FFT denoise)
#   4) acompressor      -> homogénéise la dynamique de la voix
#   5) loudnorm         -> cible LUFS (TOUJOURS en dernier)

set -euo pipefail

LUFS="${LUFS:--12}"          # -12 par défaut ; passe LUFS=-14 pour adoucir
FORMAT="${FORMAT:-wav}"      # wav (pcm 16 bits) ou flac
TP="-1.0"                    # true peak max
LRA="11"

# Réglages compresseur (voix) — ajuste THRESHOLD selon ton niveau d'enregistrement
C_THRESHOLD="-18dB"   # agit au-dessus de -18 dB ; descends à -20/-22 si voix basse
C_RATIO="3"           # 3:1, naturel ; 4 = plus marqué, 2 = très doux
C_ATTACK="5"          # ms
C_RELEASE="120"       # ms
C_MAKEUP="2"          # léger gain de compensation (le loudnorm rattrape le reste)

# Réglage débruiteur ventilo — nr = force en dB (12 = doux, 20 = agressif)
DN_NR="12"

# Construction de la chaîne de filtres
FILTERS="highpass=f=80,\
afftdn=nr=${DN_NR}:nf=-25,\
acompressor=threshold=${C_THRESHOLD}:ratio=${C_RATIO}:attack=${C_ATTACK}:release=${C_RELEASE}:makeup=${C_MAKEUP},\
loudnorm=I=${LUFS}:TP=${TP}:LRA=${LRA}"

# Codec de sortie selon le format
if [ "$FORMAT" = "flac" ]; then
  ACODEC="flac"; EXT="flac"
else
  ACODEC="pcm_s16le"; EXT="wav"
fi

# Liste des fichiers à traiter
if [ "$#" -ge 1 ]; then
  FILES="$@"
else
  FILES=$(ls valide*.mkv 2>/dev/null)
fi

[ -z "$FILES" ] && { echo "Aucun fichier valide*.mkv trouvé."; exit 1; }

for f in $FILES; do
  base="$(basename "$f" .mkv)"
  num="${base#valide}"
  out="son${num}.${EXT}"
  echo "=== $f -> $out  (cible ${LUFS} LUFS) ==="
  ffmpeg -hide_banner -y -i "$f" -vn \
    -af "$FILTERS" \
    -ar 48000 -c:a "$ACODEC" "$out"
  echo ">> $out prêt."
  echo
done

echo "Terminé. Réécoute les fichiers son*.${EXT} pour valider."
