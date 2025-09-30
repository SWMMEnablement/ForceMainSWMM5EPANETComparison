# SWMM5 Force Mains Modeling App

## Overview

This is a comprehensive web-based toolkit built with Streamlit for modeling, analyzing, and optimizing force mains in SWMM5. The application provides engineers with interactive tools for designing pump station discharge systems, calculating hydraulic losses, analyzing complex force main networks, and generating properly formatted SWMM5 input files. The app integrates multiple calculation methods including Hazen-Williams and Darcy-Weisbach equations, implements network analysis using Hardy Cross method, and provides visualization capabilities for hydraulic grade lines and system performance.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The application uses Streamlit as the web framework, providing a multi-page interface with button-based sidebar navigation. The main entry point (`app.py`) implements a page-based architecture with nine distinct tools accessed via individual buttons: Force Main Designer, Friction Loss Calculator, Network Analyzer, SWMM Input Generator, EPANET Input Generator, Results Visualizer, EPANET vs SWMM5 Comparison, Troubleshooting Assistant, and Source Code Explorer. Each tool is implemented as a separate function within the main application, allowing for modular development and maintenance.

The navigation system uses session state (`st.session_state.selected_page`) to track the active tool, with visual feedback through primary/secondary button styling. Selected tools display with a purple-blue gradient background, while unselected tools show a white background with gray borders. Button interactions trigger page reruns to display the corresponding tool content.

### Backend Architecture
The core functionality is organized into specialized modules within the `modules/` directory:

- **Calculator Module** (`calculator.py`): Implements hydraulic calculations using both Hazen-Williams and Darcy-Weisbach methods for friction loss calculation. Uses scipy for optimization and advanced hydraulic calculations including Reynolds number computation and friction factor determination.

- **Network Module** (`network.py`): Handles complex force main network analysis using Hardy Cross method and Newton-Raphson iteration. Supports different node types (wet wells, junctions, outfalls) and implements sparse matrix operations for efficient network solving.

- **SWMM Writer Module** (`swmm_writer.py`): Generates properly formatted SWMM5 input files with configurable options, time settings, and project parameters. Creates complete input file sections including title, options, and time configuration.

- **Validator Module** (`validator.py`): Provides diagnostic capabilities for troubleshooting force main systems. Implements validation rules for full flow conditions, velocity ranges, and pressure requirements with categorized issue reporting.

- **Visualizer Module** (`visualizer.py`): Creates hydraulic visualizations using Plotly, including hydraulic grade line profiles, pressure plots, and velocity diagrams. Implements interactive plotting capabilities with customizable colors and styling.

### Data Management
The application uses in-memory data structures with pandas DataFrames for tabular data management. NumPy arrays handle numerical computations and hydraulic calculations. The system supports CSV file imports for pipe materials data and maintains reference data for standard engineering parameters.

### Calculation Engine
The hydraulic calculation engine implements multiple industry-standard equations:
- Hazen-Williams equation for friction loss calculation with SI unit corrections
- Darcy-Weisbach equation with Swamee-Jain friction factor approximation
- Reynolds number calculations using kinematic viscosity
- Pressure head and velocity computations for force main analysis

The network analysis component uses sparse matrix operations for efficient solving of large hydraulic networks, implementing iterative methods with configurable tolerance and maximum iteration limits.

## External Dependencies

### Python Scientific Stack
- **NumPy**: Numerical computations and array operations for hydraulic calculations
- **SciPy**: Optimization routines, sparse matrix operations, and special functions (Lambert W function)
- **Pandas**: Data manipulation and CSV file handling for material properties and results

### Visualization and UI
- **Streamlit**: Web application framework providing the user interface and interactive components
- **Plotly**: Interactive plotting library for hydraulic grade line profiles and system visualizations
- **Matplotlib**: Static plotting capabilities for basic charts and diagrams

### File Format Support
- **PyYAML**: Configuration file handling for system parameters and settings
- **CSV Support**: Built-in pandas functionality for importing pipe material data and exporting results

### Mathematical Libraries
- **SciPy.optimize**: Numerical optimization for friction factor calculations and network solving
- **SciPy.sparse**: Sparse matrix operations for efficient network analysis
- **SciPy.special**: Special mathematical functions including Lambert W for advanced hydraulic calculations

The application is designed to be self-contained with no external database dependencies, using file-based data storage and in-memory processing for all calculations and visualizations.