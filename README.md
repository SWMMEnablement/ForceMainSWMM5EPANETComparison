# SWMM5 Force Mains Modeling App

> README added by Robert Dickinson via Comet.

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![EPA SWMM5](https://img.shields.io/badge/EPA%20SWMM5-005BAA)
![EPANET](https://img.shields.io/badge/EPANET-1F6FEB)

## About

**SWMM5 Force Mains Modeling App** (repository `ForceMainSWMM5EPANETComparison`) is a comprehensive web-based toolkit built with Streamlit for modeling, analyzing, and optimizing force mains in SWMM5. It provides engineers with interactive tools for designing pump-station discharge systems, calculating hydraulic losses, analyzing complex force-main networks, and generating properly formatted SWMM5 input files.

The app integrates multiple calculation methods including Hazen-Williams and Darcy-Weisbach, implements network analysis using the Hardy Cross method, and provides visualization of hydraulic grade lines and system performance. It also compares SWMM5 and EPANET approaches to force-main hydraulics and includes an AI assistant for answering SWMM5 / EPANET questions.

This project is part of the SWMMEnablement collection.

## What's Inside

| Area | Description |
| --- | --- |
| `app.py` | Main Streamlit application entry point |
| `modules/` | Calculation, network-analysis, and AI-assistant modules |
| `data/` | Force-main modeling and analysis reference data |
| `.streamlit/` | Streamlit configuration for local and cloud deployment |
| `attached_assets/` | Supporting reference assets and screenshots |
| `replit.md` | Project overview and design notes |

## Key Features

- Pump-station discharge-system design tools
- Hydraulic-loss calculations via Hazen-Williams and Darcy-Weisbach
- Complex force-main network analysis using the Hardy Cross method
- SWMM5 input-file generation from analyzed networks
- Hydraulic grade line and system-performance visualization
- SWMM5 vs. EPANET comparison for force-main hydraulics
- Built-in AI assistant for SWMM5 / EPANET questions

## Tech Stack

- **Language:** Python (100%)
- **Framework:** Streamlit
- **Packaging:** `pyproject.toml` / `uv.lock` (uv)
- **Domain:** EPA SWMM5 and EPANET force-main hydraulics

## Getting Started

```bash
# Clone the repository
git clone https://github.com/SWMMEnablement/ForceMainSWMM5EPANETComparison.git
cd ForceMainSWMM5EPANETComparison

# Install dependencies (using uv)
uv sync

# Run the Streamlit app
streamlit run app.py
```

Then open the local URL printed by Streamlit (typically http://localhost:8501) in your browser.

## License

See the repository for license details.
