#!/bin/bash
source ~/.nvm/nvm.sh
nvm use 20
cd /media/ai/1646F35346F3325B/survialance/frontend
export CI=true
npm install --no-fund --no-audit
npm run dev
