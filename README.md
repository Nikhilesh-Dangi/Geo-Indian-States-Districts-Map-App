![image](https://github.com/user-attachments/assets/8080ce7d-7058-4a71-a294-51e1593d71bd)
https://huggingface.co/spaces/Nikhilesh423/India-Map-Visualizer



# 🇮🇳 India Map Visualizer

An interactive Streamlit application that lets you:

- Visualize Indian **states** or **districts** on a map
- Select specific regions to **highlight**
- Display **connection lines** between selected regions
- Add **target coordinates** manually by clicking
- Render **interactive maps with coloring** and **hover tooltips** using `folium`

---

## 📸 Features

- ✅ Select between **State-to-State** or **District-to-District** mode
- ✅ Optional target points input (e.g., from Google Maps)
- ✅ Draw lines (Straight, Dashed, Curved) between regions
- ✅ Show/hide full India boundaries
- ✅ Interactive mode with colored regions based on attributes
- ✅ Hover tooltips with extra information (e.g., name, population)

---

## 📁 Directory Structure
state-map-app/
│
├── app.py 
├── utils.py 
├── requirements.txt
├── README.md 
└── data/
├── in.json 
└── output.geojson 



---

## 🔧 Setup Instructions

1. **Clone the repo**

```bash
git clone https://github.com/nikhil1111111/state-map-app.git
cd state-map-app


#Make sure you are in a virtual environment:
python -m venv venv
source venv/bin/activate  # on Windows use venv\Scripts\activate
pip install -r requirements.txt

#Run the app
streamlit run app.py

#⚠️ Ensure GDAL dependencies are installed if running on Linux. You can install them via:
sudo apt install gdal-bin libgdal-dev
