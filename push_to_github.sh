#!/bin/bash
# ─────────────────────────────────────────────────────────────
# FreqFind — One-command GitHub push script
# Usage: bash push_to_github.sh YOUR_GITHUB_USERNAME
# ─────────────────────────────────────────────────────────────

set -e

USERNAME=${1:-"YOUR_GITHUB_USERNAME"}
REPO="freqfind"

echo ""
echo "🎵 FreqFind — GitHub Push Script"
echo "=================================="
echo ""

# Check git
if ! command -v git &> /dev/null; then
  echo "❌ Git not found. Install it from https://git-scm.com"
  exit 1
fi

# Check gh (GitHub CLI) — optional
if command -v gh &> /dev/null; then
  echo "✅ GitHub CLI found — will create repo automatically"
  USE_GH=true
else
  echo "ℹ️  GitHub CLI not found. You'll need to create the repo manually at:"
  echo "   https://github.com/new"
  USE_GH=false
fi

echo ""
echo "📁 Initializing git..."
cd "$(dirname "$0")"

git init
git add .
git commit -m "feat: initial FreqFind — FFT-based music identification system

Implements a Shazam-inspired audio fingerprinting system from scratch:
- FFT/STFT-based spectrogram generation (NumPy/SciPy)
- Constellation map peak extraction
- Combinatorial hash fingerprinting (Wang 2003 algorithm)
- Time-offset alignment matching with confidence scoring
- FastAPI backend with spectrogram visualization endpoints
- Dark-mode single-page frontend with waveform + spectrograms
- 5 pre-built demo songs (Beethoven, Traditional)"

if [ "$USE_GH" = true ]; then
  echo ""
  echo "🚀 Creating GitHub repository..."
  gh repo create "$REPO" --public --description "FFT-based Shazam-inspired music identification — built from scratch with NumPy/SciPy" --push --source .
  echo ""
  echo "✅ Done! Your repo is live at:"
  echo "   https://github.com/$USERNAME/$REPO"
else
  echo ""
  echo "📋 Now do this in GitHub:"
  echo "   1. Go to https://github.com/new"
  echo "   2. Name it: $REPO"
  echo "   3. Keep it Public, don't add README (we have one)"
  echo "   4. Click 'Create repository'"
  echo ""
  echo "Then run:"
  echo "   git remote add origin https://github.com/$USERNAME/$REPO.git"
  echo "   git branch -M main"
  echo "   git push -u origin main"
fi

echo ""
echo "🎛️  To run locally:"
echo "   pip install -r requirements.txt"
echo "   python generate_samples.py && python index_samples.py"
echo "   cd backend && uvicorn main:app --reload --port 8000"
echo "   # Open frontend/index.html in browser"
