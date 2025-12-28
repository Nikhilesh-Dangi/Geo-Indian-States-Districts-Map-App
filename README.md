# India Geo Explorer (GitHub Pages)

Static Leaflet app to browse India states or districts, search, hover, click to select, and download GeoJSON (full or selected). Selections persist via localStorage; optional GitHub token flow saves selections to `/saved/user_selections.json` through the GitHub API.

## Quick start (local or Pages preview)
```bash
npm install -g serve
serve .
# open http://localhost:3000
```

## Deploy on GitHub Pages (project site)
1) Ensure repo contains:
- `index.html`
- `assets/style.css`
- `assets/app.js`
- `data/states.geojson`
- `data/districts.geojson`

2) Commit & push to `main`.

3) In GitHub: Settings → Pages  
   Source: Deploy from a branch  
   Branch: `main`  
   Folder: `/ (root)`

4) Visit: `https://nikhilesh-dangi.github.io/Geo-Indian-States-Districts-Map-App/`

## Optional “save selection to GitHub”
Only needed if you want selections committed back to this repo (not secure for public sites).
- Open the settings modal, paste a GitHub token (contents:write), owner, and repo name.
- The app PUTs to `saved/user_selections.json` via GitHub REST. Without a token, selections stay in localStorage only.
