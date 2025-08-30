import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from modules.calculator import ForceMainCalculator
from modules.network import ForceMainNetwork
from modules.visualizer import HydraulicVisualizer
from modules.swmm_writer import SWMMInputGenerator
from modules.epanet_writer import EPANETInputGenerator
from modules.validator import TroubleshootingAssistant
import io
import os

# Page configuration
st.set_page_config(
    page_title="SWMM5 Force Mains Modeling App",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🏗️ SWMM5 Force Mains Modeling App")
    st.markdown("**Comprehensive toolkit for modeling, analyzing, and optimizing force mains in SWMM5**")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Tool",
        [
            "Force Main Designer",
            "Friction Loss Calculator", 
            "Network Analyzer",
            "SWMM Input Generator",
            "Results Visualizer",
            "EPANET vs SWMM5 Comparison",
            "Troubleshooting Assistant"
        ]
    )
    
    if page == "Force Main Designer":
        force_main_designer()
    elif page == "Friction Loss Calculator":
        friction_loss_calculator()
    elif page == "Network Analyzer":
        network_analyzer()
    elif page == "SWMM Input Generator":
        swmm_input_generator()
    elif page == "Results Visualizer":
        results_visualizer()
    elif page == "EPANET vs SWMM5 Comparison":
        epanet_swmm_comparison()
    elif page == "Troubleshooting Assistant":
        troubleshooting_assistant()

def force_main_designer():
    st.header("🔧 Force Main Designer")
    st.markdown("Interactive tool for sizing and configuring force mains")
    
    calc = ForceMainCalculator()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("System Parameters")
        
        # Flow parameters
        flow_rate = st.number_input("Flow Rate (m³/s)", min_value=0.001, max_value=10.0, value=0.1, step=0.01)
        pipe_diameter = st.number_input("Pipe Diameter (m)", min_value=0.1, max_value=3.0, value=0.3, step=0.05)
        pipe_length = st.number_input("Pipe Length (m)", min_value=10.0, max_value=10000.0, value=1000.0, step=50.0)
        
        # Material properties
        material = st.selectbox(
            "Pipe Material",
            ["PVC", "Ductile Iron", "HDPE", "Steel", "Cast Iron"]
        )
        
        # Load material properties
        materials_df = pd.read_csv("data/pipe_materials.csv")
        material_props = materials_df[materials_df['Material'] == material].iloc[0]
        
        hazen_williams_c = st.number_input(
            "Hazen-Williams C", 
            min_value=80, 
            max_value=150, 
            value=int(material_props['HW_C']),
            step=5
        )
        
        roughness = st.number_input(
            "Absolute Roughness (mm)", 
            min_value=0.01, 
            max_value=10.0, 
            value=material_props['Roughness_mm'],
            step=0.01,
            format="%.3f"
        )
        
        # Elevation data
        st.subheader("Elevation Profile")
        upstream_elev = st.number_input("Upstream Invert (m)", value=100.0, step=0.1)
        downstream_elev = st.number_input("Downstream Invert (m)", value=110.0, step=0.1)
        pump_head = st.number_input("Available Pump Head (m)", min_value=5.0, max_value=200.0, value=50.0, step=1.0)
    
    with col2:
        st.subheader("Hydraulic Analysis Results")
        
        # Calculate hydraulic parameters
        area = np.pi * pipe_diameter**2 / 4
        velocity = flow_rate / area
        static_head = downstream_elev - upstream_elev
        
        # Friction losses
        hw_loss = calc.hazen_williams_loss(flow_rate, pipe_diameter, pipe_length, hazen_williams_c)
        dw_loss = calc.darcy_weisbach_loss(flow_rate, pipe_diameter, pipe_length, roughness/1000)
        
        # System check
        hw_full_flow, hw_surplus = calc.check_full_flow_condition(pump_head, static_head, hw_loss)
        dw_full_flow, dw_surplus = calc.check_full_flow_condition(pump_head, static_head, dw_loss)
        
        # Display results
        st.metric("Pipe Velocity", f"{velocity:.2f} m/s")
        st.metric("Static Head", f"{static_head:.2f} m")
        
        st.write("**Friction Loss Comparison:**")
        col2a, col2b = st.columns(2)
        
        with col2a:
            st.metric("Hazen-Williams Loss", f"{hw_loss:.2f} m")
            if hw_full_flow:
                st.success(f"✅ Full Flow (Surplus: {hw_surplus:.2f} m)")
            else:
                st.error(f"❌ Insufficient Head (Deficit: {abs(hw_surplus):.2f} m)")
        
        with col2b:
            st.metric("Darcy-Weisbach Loss", f"{dw_loss:.2f} m")
            if dw_full_flow:
                st.success(f"✅ Full Flow (Surplus: {dw_surplus:.2f} m)")
            else:
                st.error(f"❌ Insufficient Head (Deficit: {abs(dw_surplus):.2f} m)")
        
        # Velocity check
        if velocity < 0.6:
            st.warning("⚠️ Low velocity may cause solids settling")
        elif velocity > 3.0:
            st.warning("⚠️ High velocity may cause excessive wear")
        else:
            st.success("✅ Velocity within acceptable range")
        
        # System efficiency
        total_head_hw = static_head + hw_loss
        efficiency_hw = (total_head_hw / pump_head) * 100 if pump_head > 0 else 0
        st.metric("System Efficiency (H-W)", f"{efficiency_hw:.1f}%")

def friction_loss_calculator():
    st.header("📊 Friction Loss Calculator")
    st.markdown("Compare Hazen-Williams vs Darcy-Weisbach friction loss methods")
    
    calc = ForceMainCalculator()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Input Parameters")
        
        pipe_diameter = st.slider("Pipe Diameter (m)", 0.1, 2.0, 0.3, 0.05)
        pipe_length = st.number_input("Pipe Length (m)", min_value=100, max_value=5000, value=1000, step=100)
        hazen_williams_c = st.slider("Hazen-Williams C", 80, 150, 120, 5)
        roughness_mm = st.slider("Absolute Roughness (mm)", 0.01, 5.0, 0.15, 0.01)
        
        # Flow rate range for comparison
        min_flow = st.number_input("Minimum Flow (m³/s)", min_value=0.01, max_value=1.0, value=0.05, step=0.01)
        max_flow = st.number_input("Maximum Flow (m³/s)", min_value=0.1, max_value=5.0, value=0.5, step=0.05)
    
    with col2:
        st.subheader("Friction Loss Comparison")
        
        # Generate flow range
        flows = np.linspace(min_flow, max_flow, 50)
        hw_losses = []
        dw_losses = []
        
        for flow in flows:
            hw_loss = calc.hazen_williams_loss(flow, pipe_diameter, pipe_length, hazen_williams_c)
            dw_loss = calc.darcy_weisbach_loss(flow, pipe_diameter, pipe_length, roughness_mm/1000)
            hw_losses.append(hw_loss)
            dw_losses.append(dw_loss)
        
        # Create comparison plot
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=flows, y=hw_losses,
            mode='lines',
            name='Hazen-Williams',
            line=dict(color='blue', width=3)
        ))
        
        fig.add_trace(go.Scatter(
            x=flows, y=dw_losses,
            mode='lines',
            name='Darcy-Weisbach',
            line=dict(color='red', width=3)
        ))
        
        fig.update_layout(
            title="Friction Loss Comparison",
            xaxis_title="Flow Rate (m³/s)",
            yaxis_title="Head Loss (m)",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Calculate differences
        differences = np.array(dw_losses) - np.array(hw_losses)
        avg_diff = np.mean(np.abs(differences))
        max_diff = np.max(np.abs(differences))
        
        st.write("**Statistical Comparison:**")
        st.metric("Average Absolute Difference", f"{avg_diff:.3f} m")
        st.metric("Maximum Absolute Difference", f"{max_diff:.3f} m")
        
        # Recommendations
        st.subheader("Method Recommendations")
        if avg_diff < 0.5:
            st.success("✅ Both methods provide similar results. H-W acceptable for design.")
        elif avg_diff < 1.0:
            st.warning("⚠️ Moderate difference. Consider D-W for critical applications.")
        else:
            st.error("❌ Significant difference. Use Darcy-Weisbach for accuracy.")

def network_analyzer():
    st.header("🔗 Network Analyzer")
    st.markdown("Analyze complex force main networks with multiple branches")
    
    st.info("🚧 This is a simplified network analyzer. For complex networks, consider specialized hydraulic modeling software.")
    
    network = ForceMainNetwork()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Network Configuration")
        
        # Number of nodes and links
        num_nodes = st.selectbox("Number of Nodes", [2, 3, 4, 5], index=1)
        num_links = st.selectbox("Number of Force Mains", [1, 2, 3, 4], index=0)
        num_pumps = st.selectbox("Number of Pumps", [0, 1, 2, 3], index=1)
        
        st.subheader("Node Data")
        nodes_data = []
        for i in range(num_nodes):
            st.write(f"**Node {i+1}:**")
            node_type = st.selectbox(f"Type", ["Junction", "Wet Well"], key=f"type_{i}")
            elevation = st.number_input(f"Elevation (m)", value=100.0 + i*5, key=f"elev_{i}")
            
            if node_type == "Wet Well":
                max_depth = st.number_input(f"Max Depth (m)", value=3.0, key=f"depth_{i}")
                nodes_data.append({"id": f"N{i+1}", "type": "wet_well", "elevation": elevation, "max_depth": max_depth})
            else:
                nodes_data.append({"id": f"N{i+1}", "type": "junction", "elevation": elevation})
        
        st.subheader("Link Data")
        links_data = []
        for i in range(num_links):
            st.write(f"**Force Main {i+1}:**")
            from_node = st.selectbox(f"From Node", [f"N{j+1}" for j in range(num_nodes)], key=f"from_{i}")
            to_node = st.selectbox(f"To Node", [f"N{j+1}" for j in range(num_nodes) if f"N{j+1}" != from_node], key=f"to_{i}")
            diameter = st.number_input(f"Diameter (m)", value=0.3, key=f"diam_{i}")
            length = st.number_input(f"Length (m)", value=1000.0, key=f"length_{i}")
            
            links_data.append({
                "id": f"FM{i+1}",
                "from": from_node,
                "to": to_node,
                "diameter": diameter,
                "length": length
            })
        
        st.subheader("Pump Data")
        pumps_data = []
        for i in range(num_pumps):
            st.write(f"**Pump {i+1}:**")
            from_node = st.selectbox(f"From Node", [f"N{j+1}" for j in range(num_nodes)], key=f"pump_from_{i}")
            to_node = st.selectbox(f"To Node", [f"N{j+1}" for j in range(num_nodes) if f"N{j+1}" != from_node], key=f"pump_to_{i}")
            pump_head = st.number_input(f"Design Head (m)", value=50.0, key=f"pump_head_{i}")
            pump_flow = st.number_input(f"Design Flow (m³/s)", value=0.15, key=f"pump_flow_{i}")
            
            pumps_data.append({
                "id": f"P{i+1}",
                "from": from_node,
                "to": to_node,
                "head": pump_head,
                "flow": pump_flow
            })
    
    with col2:
        st.subheader("Network Visualization")
        
        # Create simple network diagram
        fig = go.Figure()
        
        # Add nodes
        for i, node in enumerate(nodes_data):
            fig.add_trace(go.Scatter(
                x=[i], y=[node["elevation"]],
                mode='markers+text',
                marker=dict(size=20, color='blue' if node["type"] == "junction" else 'red'),
                text=[node["id"]],
                textposition="top center",
                name=node["type"],
                showlegend=i==0
            ))
        
        # Add links
        for link in links_data:
            from_idx = next(i for i, n in enumerate(nodes_data) if n["id"] == link["from"])
            to_idx = next(i for i, n in enumerate(nodes_data) if n["id"] == link["to"])
            
            fig.add_trace(go.Scatter(
                x=[from_idx, to_idx],
                y=[nodes_data[from_idx]["elevation"], nodes_data[to_idx]["elevation"]],
                mode='lines',
                line=dict(color='green', width=3),
                name='Force Main',
                showlegend=False,
                hovertemplate=f"Force Main: {link['id']}<br>Diameter: {link['diameter']:.2f}m<br>Length: {link['length']:.0f}m<extra></extra>"
            ))
        
        # Add pumps
        for pump in pumps_data:
            from_idx = next(i for i, n in enumerate(nodes_data) if n["id"] == pump["from"])
            to_idx = next(i for i, n in enumerate(nodes_data) if n["id"] == pump["to"])
            
            # Draw pump as a thicker red line with arrow markers
            fig.add_trace(go.Scatter(
                x=[from_idx, to_idx],
                y=[nodes_data[from_idx]["elevation"], nodes_data[to_idx]["elevation"]],
                mode='lines+markers',
                line=dict(color='red', width=5),
                marker=dict(size=8, symbol='arrow-right', color='red'),
                name='Pump',
                showlegend=False,
                hovertemplate=f"Pump: {pump['id']}<br>Design Head: {pump['head']:.1f}m<br>Design Flow: {pump['flow']:.3f}m³/s<extra></extra>"
            ))
            
            # Add pump label at midpoint
            mid_x = (from_idx + to_idx) / 2
            mid_y = (nodes_data[from_idx]["elevation"] + nodes_data[to_idx]["elevation"]) / 2
            fig.add_annotation(
                x=mid_x,
                y=mid_y,
                text=pump["id"],
                showarrow=False,
                bgcolor="white",
                bordercolor="red",
                borderwidth=1,
                font=dict(size=10, color="red")
            )
        
        fig.update_layout(
            title="Network Layout",
            xaxis_title="Node Position",
            yaxis_title="Elevation (m)",
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Network analysis results
        st.subheader("Analysis Results")
        
        if st.button("Analyze Network"):
            # Simplified analysis
            total_length = sum(link["length"] for link in links_data)
            avg_diameter = np.mean([link["diameter"] for link in links_data]) if links_data else 0
            elevation_diff = max(node["elevation"] for node in nodes_data) - min(node["elevation"] for node in nodes_data)
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.write("**System Metrics:**")
                st.metric("Total Force Main Length", f"{total_length:.0f} m")
                st.metric("Average Diameter", f"{avg_diameter:.2f} m")
                st.metric("Total Static Head", f"{elevation_diff:.1f} m")
            
            with col_b:
                if pumps_data:
                    st.write("**Pump Summary:**")
                    total_pump_head = sum(pump["head"] for pump in pumps_data)
                    total_pump_flow = sum(pump["flow"] for pump in pumps_data)
                    st.metric("Total Pump Head", f"{total_pump_head:.1f} m")
                    st.metric("Total Pump Flow", f"{total_pump_flow:.3f} m³/s")
                    
                    st.write("**Individual Pumps:**")
                    for pump in pumps_data:
                        st.write(f"- {pump['id']}: {pump['flow']:.3f} m³/s @ {pump['head']:.1f} m")
            
            # System adequacy check
            if pumps_data:
                max_pump_head = max(pump["head"] for pump in pumps_data)
                if max_pump_head > elevation_diff:
                    surplus_head = max_pump_head - elevation_diff
                    st.success(f"✅ Adequate pump head (surplus: {surplus_head:.1f} m)")
                else:
                    deficit_head = elevation_diff - max_pump_head
                    st.error(f"❌ Insufficient pump head (deficit: {deficit_head:.1f} m)")
            
            # Simple flow distribution (equal split for multiple branches)
            if num_links > 1:
                st.write("**Flow Distribution (Simplified):**")
                for i, link in enumerate(links_data):
                    flow_fraction = 1.0 / num_links  # Simple equal distribution
                    st.write(f"- {link['id']}: {flow_fraction*100:.1f}% of total flow")

def swmm_input_generator():
    st.header("📝 SWMM & EPANET Input Generator")
    st.markdown("Generate properly formatted SWMM5 and EPANET input files for force main systems")
    
    generator = SWMMInputGenerator()
    epanet_generator = EPANETInputGenerator()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("System Configuration")
        
        # Project information
        project_title = st.text_input("Project Title", value="Force Main System")
        flow_units = st.selectbox("Flow Units", ["CMS", "LPS", "MGD", "CFS"], index=0)
        
        # Wet well configuration
        st.subheader("Wet Well")
        ww_id = st.text_input("Wet Well ID", value="WW1")
        ww_invert = st.number_input("Invert Elevation (m)", value=95.0)
        ww_max_depth = st.number_input("Maximum Depth (m)", value=4.0)
        ww_init_depth = st.number_input("Initial Depth (m)", value=1.0)
        ww_area = st.number_input("Surface Area (m²)", value=50.0)
        
        # Pump configuration
        st.subheader("Pump")
        pump_id = st.text_input("Pump ID", value="P1")
        pump_curve_id = st.text_input("Pump Curve ID", value="PC1")
        startup_depth = st.number_input("Startup Depth (m)", value=2.0)
        shutoff_depth = st.number_input("Shutoff Depth (m)", value=0.5)
        
        # Force main configuration
        st.subheader("Force Main")
        fm_id = st.text_input("Force Main ID", value="FM1")
        fm_diameter = st.number_input("Diameter (m)", value=0.3)
        fm_length = st.number_input("Length (m)", value=1000.0)
        fm_roughness = st.number_input("Roughness Coefficient", value=0.013, format="%.4f")
        
        # Discharge node
        st.subheader("Discharge Node")
        dn_id = st.text_input("Discharge Node ID", value="DN1")
        dn_elevation = st.number_input("Discharge Elevation (m)", value=105.0)
        dn_max_depth = st.number_input("Max Depth (m)", value=2.0)
        surcharge_depth = st.number_input("Surcharge Depth (m)", value=1.5)
    
    with col2:
        st.subheader("Pump Curve Definition")
        
        # Load default pump curves
        pump_curves_df = pd.read_csv("data/pump_curves.csv")
        
        curve_type = st.selectbox("Curve Type", ["Custom", "Select from Library"])
        
        if curve_type == "Select from Library":
            available_curves = pump_curves_df['Curve_ID'].unique()
            selected_curve = st.selectbox("Select Curve", available_curves)
            curve_data = pump_curves_df[pump_curves_df['Curve_ID'] == selected_curve]
            
            # Display selected curve
            fig = px.line(curve_data, x='Flow_m3s', y='Head_m', title=f"Pump Curve: {selected_curve}")
            st.plotly_chart(fig, use_container_width=True)
            
            pump_points = list(zip(curve_data['Flow_m3s'], curve_data['Head_m']))
        else:
            st.write("Define custom pump curve points:")
            num_points = st.selectbox("Number of Points", [3, 4, 5, 6], index=1)
            
            pump_points = []
            for i in range(num_points):
                col_flow, col_head = st.columns(2)
                with col_flow:
                    flow = st.number_input(f"Flow {i+1} (m³/s)", value=0.1*(i+1), key=f"flow_{i}")
                with col_head:
                    head = st.number_input(f"Head {i+1} (m)", value=50.0-5*i, key=f"head_{i}")
                pump_points.append((flow, head))
        
        st.subheader("Generate Input Files")
        
        # Model format selection
        export_format = st.selectbox("Export Format", ["SWMM5 Only", "EPANET Only", "Both SWMM5 & EPANET"])
        
        if st.button("Generate Input Files"):
            # Create configuration dictionary
            config = {
                'project_title': project_title,
                'flow_units': flow_units,
                'wet_well': {
                    'id': ww_id,
                    'invert': ww_invert,
                    'max_depth': ww_max_depth,
                    'init_depth': ww_init_depth,
                    'area': ww_area
                },
                'pump': {
                    'id': pump_id,
                    'from': ww_id,
                    'to': fm_id + "_start",  # Intermediate node
                    'curve': pump_curve_id,
                    'startup': startup_depth,
                    'shutoff': shutoff_depth,
                    'curve_data': pump_points
                },
                'force_main': {
                    'id': fm_id,
                    'from': fm_id + "_start",
                    'to': dn_id,
                    'diameter': fm_diameter,
                    'length': fm_length,
                    'roughness': fm_roughness
                },
                'discharge_node': {
                    'id': dn_id,
                    'elevation': dn_elevation,
                    'max_depth': dn_max_depth,
                    'surcharge_depth': surcharge_depth
                }
            }
            
            # Convert SWMM config to EPANET format
            epanet_config = {
                'project_title': project_title,
                'wet_well': {
                    'id': ww_id,
                    'elevation': ww_invert,
                    'demand': -0.1  # Negative for supply source
                },
                'pump': {
                    'id': pump_id,
                    'from': ww_id,
                    'to': fm_id + "_start",
                    'curve_data': pump_points
                },
                'force_main': {
                    'id': fm_id,
                    'from': fm_id + "_start",
                    'to': dn_id,
                    'diameter': fm_diameter,
                    'length': fm_length,
                    'roughness': 120 if fm_roughness < 1 else fm_roughness  # Convert to C value if needed
                },
                'discharge_node': {
                    'id': dn_id,
                    'elevation': dn_elevation,
                    'demand': 0.1  # Positive demand at discharge
                }
            }
            
            # Generate files based on selection
            if export_format in ["SWMM5 Only", "Both SWMM5 & EPANET"]:
                swmm_content = generator.create_force_main_system(config)
                
                with st.expander("View Generated SWMM5 Input File", expanded=(export_format == "SWMM5 Only")):
                    st.code(swmm_content, language='text')
                
                st.download_button(
                    label="Download SWMM5 .inp File",
                    data=swmm_content,
                    file_name=f"{project_title.replace(' ', '_').lower()}_swmm.inp",
                    mime="text/plain",
                    key="swmm_download"
                )
            
            if export_format in ["EPANET Only", "Both SWMM5 & EPANET"]:
                epanet_content = epanet_generator.create_force_main_system(epanet_config)
                
                with st.expander("View Generated EPANET Input File", expanded=(export_format == "EPANET Only")):
                    st.code(epanet_content, language='text')
                
                st.download_button(
                    label="Download EPANET .inp File",
                    data=epanet_content,
                    file_name=f"{project_title.replace(' ', '_').lower()}_epanet.inp",
                    mime="text/plain",
                    key="epanet_download"
                )
            
            # Comparison summary
            if export_format == "Both SWMM5 & EPANET":
                st.info("💡 **Tip**: Both files have been generated. Use the 'EPANET vs SWMM5 Comparison' tool to see detailed differences between the two modeling approaches.")

def results_visualizer():
    st.header("📈 Results Visualizer")
    st.markdown("Visualize hydraulic grade lines and system performance")
    
    visualizer = HydraulicVisualizer()
    
    st.info("Upload SWMM results or use the simulation tool below for visualization")
    
    # Simulation section
    st.subheader("Quick Hydraulic Simulation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # System parameters for simulation
        st.write("**System Parameters:**")
        pump_head = st.slider("Pump Head (m)", 10, 100, 50)
        static_head = st.slider("Static Head (m)", 0, 30, 10)
        pipe_length = st.slider("Pipe Length (m)", 500, 5000, 1000)
        pipe_diameter = st.slider("Pipe Diameter (m)", 0.2, 1.0, 0.3)
        flow_rate = st.slider("Flow Rate (m³/s)", 0.05, 0.5, 0.15)
        roughness_c = st.slider("Hazen-Williams C", 80, 150, 120)
    
    with col2:
        # Calculate hydraulic grade line
        calc = ForceMainCalculator()
        
        # Discretize pipe into segments
        num_segments = 20
        segment_length = pipe_length / num_segments
        distances = np.linspace(0, pipe_length, num_segments + 1)
        
        # Calculate head at each point
        elevations = np.linspace(0, static_head, num_segments + 1)  # Simple linear profile
        heads = []
        
        pump_discharge_head = pump_head
        current_head = pump_discharge_head
        
        for i, dist in enumerate(distances):
            if i == 0:
                heads.append(current_head)
            else:
                # Calculate friction loss for this segment
                segment_loss = calc.hazen_williams_loss(flow_rate, pipe_diameter, segment_length, roughness_c)
                current_head -= segment_loss
                heads.append(current_head)
        
        # Add elevation to get hydraulic grade line
        hgl = np.array(heads) + elevations
        pipe_invert = elevations
        
        # Create hydraulic grade line plot
        fig = go.Figure()
        
        # Pipe invert
        fig.add_trace(go.Scatter(
            x=distances, y=pipe_invert,
            mode='lines',
            name='Pipe Invert',
            line=dict(color='brown', width=3)
        ))
        
        # Hydraulic grade line
        fig.add_trace(go.Scatter(
            x=distances, y=hgl,
            mode='lines',
            name='Hydraulic Grade Line',
            line=dict(color='blue', width=3),
            fill='tonexty',
            fillcolor='rgba(0,0,255,0.2)'
        ))
        
        # Pipe crown
        pipe_crown = pipe_invert + pipe_diameter
        fig.add_trace(go.Scatter(
            x=distances, y=pipe_crown,
            mode='lines',
            name='Pipe Crown',
            line=dict(color='gray', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title="Hydraulic Grade Line Profile",
            xaxis_title="Distance (m)",
            yaxis_title="Elevation (m)",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # System analysis
        min_pressure_head = np.min(hgl - pipe_crown)
        max_pressure_head = np.max(hgl - pipe_crown)
        
        st.write("**System Analysis:**")
        st.metric("Minimum Pressure Head", f"{min_pressure_head:.2f} m")
        st.metric("Maximum Pressure Head", f"{max_pressure_head:.2f} m")
        
        if min_pressure_head < 0:
            st.error("❌ Negative pressure - risk of air entrainment")
        elif min_pressure_head < 3:
            st.warning("⚠️ Low pressure - monitor for cavitation")
        else:
            st.success("✅ Adequate pressure throughout system")
    
    # Performance monitoring section
    st.subheader("Performance Monitoring")
    
    # Generate sample time series data
    if st.button("Generate Sample Performance Data"):
        time_hours = np.arange(0, 24, 0.5)
        
        # Simulate daily flow pattern
        base_flow = 0.1
        peak_factor = 2.0
        flow_pattern = base_flow * (1 + peak_factor * np.sin(2 * np.pi * time_hours / 24))
        
        # Calculate corresponding parameters
        velocities = flow_pattern / (np.pi * pipe_diameter**2 / 4)
        pressure_heads = []
        
        for flow in flow_pattern:
            friction_loss = calc.hazen_williams_loss(flow, pipe_diameter, pipe_length, roughness_c)
            pressure_head = pump_head - static_head - friction_loss
            pressure_heads.append(pressure_head)
        
        # Create performance plots
        fig_flow = go.Figure()
        fig_flow.add_trace(go.Scatter(x=time_hours, y=flow_pattern, mode='lines', name='Flow Rate'))
        fig_flow.update_layout(title="Flow Rate vs Time", xaxis_title="Time (hours)", yaxis_title="Flow Rate (m³/s)")
        
        fig_vel = go.Figure()
        fig_vel.add_trace(go.Scatter(x=time_hours, y=velocities, mode='lines', name='Velocity', line=dict(color='red')))
        fig_vel.update_layout(title="Velocity vs Time", xaxis_title="Time (hours)", yaxis_title="Velocity (m/s)")
        
        fig_pressure = go.Figure()
        fig_pressure.add_trace(go.Scatter(x=time_hours, y=pressure_heads, mode='lines', name='Pressure Head', line=dict(color='green')))
        fig_pressure.update_layout(title="Pressure Head vs Time", xaxis_title="Time (hours)", yaxis_title="Pressure Head (m)")
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_flow, use_container_width=True)
            st.plotly_chart(fig_pressure, use_container_width=True)
        
        with col2:
            st.plotly_chart(fig_vel, use_container_width=True)
            
            # Performance statistics
            st.write("**Daily Performance Summary:**")
            st.metric("Average Flow", f"{np.mean(flow_pattern):.3f} m³/s")
            st.metric("Peak Flow", f"{np.max(flow_pattern):.3f} m³/s")
            st.metric("Minimum Velocity", f"{np.min(velocities):.2f} m/s")
            st.metric("Maximum Velocity", f"{np.max(velocities):.2f} m/s")

def epanet_swmm_comparison():
    st.header("⚖️ EPANET vs SWMM5 Comparison")
    st.markdown("Compare force main modeling approaches between EPANET and SWMM5")
    
    # Comparison overview
    st.subheader("Modeling Approach Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔧 EPANET")
        st.markdown("""
        **Strengths:**
        - ✅ Dedicated water distribution system modeling
        - ✅ Advanced hydraulic analysis capabilities
        - ✅ Excellent pump modeling and optimization
        - ✅ Mature, well-established software
        - ✅ Faster computation for steady-state analysis
        - ✅ Superior pressure network analysis
        - ✅ Built-in optimization routines
        
        **Limitations:**
        - ❌ Steady-state analysis only
        - ❌ No unsteady flow capability
        - ❌ Limited wet well modeling
        - ❌ No surface runoff integration
        - ❌ No quality routing in sewers
        - ❌ Less suitable for combined systems
        """)
    
    with col2:
        st.markdown("### 🌊 SWMM5")
        st.markdown("""
        **Strengths:**
        - ✅ Dynamic/unsteady flow analysis
        - ✅ Integrated stormwater modeling
        - ✅ Advanced wet well and storage modeling
        - ✅ Combined sewer system capability
        - ✅ Water quality modeling
        - ✅ Real-time control simulation
        - ✅ Surface runoff integration
        
        **Limitations:**
        - ❌ More complex setup for simple systems
        - ❌ Longer computation times
        - ❌ Less optimized for pure pressure systems
        - ❌ Steeper learning curve
        - ❌ Can be overkill for simple force mains
        - ❌ Convergence issues with pressure systems
        """)
    
    # Feature comparison table
    st.subheader("Feature Comparison Matrix")
    
    comparison_data = {
        'Feature': [
            'Steady-State Analysis',
            'Dynamic Flow Analysis', 
            'Pump Modeling',
            'Force Main Analysis',
            'Wet Well Modeling',
            'Pressure Analysis',
            'Water Quality',
            'Real-Time Controls',
            'Network Optimization',
            'Computation Speed',
            'Learning Curve',
            'Industry Adoption'
        ],
        'EPANET': [
            '⭐⭐⭐⭐⭐',
            '❌',
            '⭐⭐⭐⭐⭐', 
            '⭐⭐⭐⭐',
            '⭐⭐',
            '⭐⭐⭐⭐⭐',
            '⭐⭐⭐',
            '⭐⭐',
            '⭐⭐⭐⭐⭐',
            '⭐⭐⭐⭐⭐',
            '⭐⭐⭐⭐',
            '⭐⭐⭐⭐⭐'
        ],
        'SWMM5': [
            '⭐⭐⭐',
            '⭐⭐⭐⭐⭐',
            '⭐⭐⭐',
            '⭐⭐⭐⭐⭐',
            '⭐⭐⭐⭐⭐',
            '⭐⭐⭐',
            '⭐⭐⭐⭐⭐',
            '⭐⭐⭐⭐⭐',
            '⭐⭐',
            '⭐⭐⭐',
            '⭐⭐',
            '⭐⭐⭐⭐'
        ],
        'Best Use Case': [
            'EPANET - More mature algorithms',
            'SWMM5 - Only option available',
            'EPANET - Advanced pump analysis',
            'Both - Depends on complexity',
            'SWMM5 - Superior storage modeling',
            'EPANET - Purpose-built for pressure',
            'SWMM5 - Comprehensive quality routing',
            'SWMM5 - Built-in control logic',
            'EPANET - Built-in optimization',
            'EPANET - Faster steady-state',
            'EPANET - Simpler setup',
            'Both - Widely adopted'
        ]
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)
    
    # When to use which software
    st.subheader("Decision Matrix: Which Software to Choose?")
    
    # Interactive decision tool
    st.markdown("### 🤔 Help Me Choose")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Project Requirements:**")
        
        analysis_type = st.selectbox(
            "Primary Analysis Type",
            ["Steady-state hydraulics", "Dynamic/unsteady flow", "Both required"]
        )
        
        system_complexity = st.selectbox(
            "System Complexity",
            ["Simple force main", "Multiple pumps/branches", "Complex network", "Integrated system"]
        )
        
        time_dependency = st.selectbox(
            "Time-Dependent Analysis Needed?",
            ["No - steady conditions", "Yes - varying demands", "Yes - pump cycling", "Yes - real-time control"]
        )
        
        quality_modeling = st.selectbox(
            "Water Quality Modeling",
            ["Not required", "Basic quality tracking", "Advanced quality analysis", "Sewer-specific quality"]
        )
        
        integration_needs = st.selectbox(
            "Integration with Other Systems",
            ["Standalone force main", "Part of water system", "Part of sewer system", "Combined stormwater system"]
        )
    
    with col2:
        st.write("**Recommendation:**")
        
        # Decision logic
        epanet_score = 0
        swmm_score = 0
        
        # Analysis type scoring
        if analysis_type == "Steady-state hydraulics":
            epanet_score += 3
        elif analysis_type == "Dynamic/unsteady flow":
            swmm_score += 3
        else:
            epanet_score += 1
            swmm_score += 2
        
        # System complexity scoring
        if system_complexity == "Simple force main":
            epanet_score += 2
        elif system_complexity in ["Multiple pumps/branches", "Complex network"]:
            epanet_score += 3
        else:
            swmm_score += 2
        
        # Time dependency scoring
        if time_dependency == "No - steady conditions":
            epanet_score += 3
        else:
            swmm_score += 3
        
        # Quality modeling scoring
        if quality_modeling == "Not required":
            epanet_score += 1
        elif quality_modeling in ["Advanced quality analysis", "Sewer-specific quality"]:
            swmm_score += 3
        else:
            epanet_score += 1
            swmm_score += 1
        
        # Integration scoring
        if integration_needs in ["Part of water system", "Standalone force main"]:
            epanet_score += 2
        else:
            swmm_score += 3
        
        # Display recommendation
        if epanet_score > swmm_score:
            st.success("🎯 **EPANET Recommended**")
            st.write(f"Score: EPANET {epanet_score} vs SWMM5 {swmm_score}")
            st.write("**Reasoning:**")
            if analysis_type == "Steady-state hydraulics":
                st.write("- EPANET excels at steady-state analysis")
            if system_complexity in ["Simple force main", "Multiple pumps/branches"]:
                st.write("- Better suited for pressure network analysis")
            if time_dependency == "No - steady conditions":
                st.write("- No need for dynamic capabilities")
            if integration_needs == "Part of water system":
                st.write("- Natural fit for water distribution systems")
            
        elif swmm_score > epanet_score:
            st.success("🎯 **SWMM5 Recommended**")
            st.write(f"Score: SWMM5 {swmm_score} vs EPANET {epanet_score}")
            st.write("**Reasoning:**")
            if analysis_type in ["Dynamic/unsteady flow", "Both required"]:
                st.write("- Dynamic analysis capabilities required")
            if time_dependency != "No - steady conditions":
                st.write("- Time-dependent analysis needed")
            if quality_modeling in ["Advanced quality analysis", "Sewer-specific quality"]:
                st.write("- Superior water quality modeling")
            if integration_needs in ["Part of sewer system", "Combined stormwater system"]:
                st.write("- Better integration with sewer/stormwater systems")
            
        else:
            st.info("🤷 **Either Software Suitable**")
            st.write(f"Score: EPANET {epanet_score} vs SWMM5 {swmm_score}")
            st.write("Both software packages would work well for your application.")
            st.write("Consider factors like:")
            st.write("- Existing software expertise")
            st.write("- Future project requirements")
            st.write("- Integration with existing models")
    
    # Model conversion guidance
    st.subheader("Model Conversion Guidance")
    
    with st.expander("Converting SWMM5 to EPANET", expanded=False):
        st.markdown("""
        **Key Conversion Steps:**
        
        1. **Nodes:**
           - Wet wells → Tanks or Reservoirs
           - Junctions → Junctions
           - Outfalls → Reservoirs
        
        2. **Links:**
           - Force mains → Pipes
           - Pumps → Pumps (convert curves)
           - Controls → Rules/Controls
        
        3. **Units:**
           - SWMM uses m³/s → EPANET uses L/s
           - Convert roughness: Manning's n → Hazen-Williams C
        
        4. **Time Settings:**
           - SWMM dynamic → EPANET steady-state
           - Use peak hour conditions
        
        **Conversion Formula Examples:**
        ```
        EPANET Flow (L/s) = SWMM Flow (m³/s) × 1000
        H-W C ≈ 120 (for typical force mains)
        Pipe Diameter (mm) = SWMM Diameter (m) × 1000
        ```
        """)
    
    with st.expander("Converting EPANET to SWMM5", expanded=False):
        st.markdown("""
        **Key Conversion Steps:**
        
        1. **Nodes:**
           - Tanks → Storage nodes
           - Junctions → Junctions
           - Reservoirs → Outfalls
        
        2. **Links:**
           - Pipes → Conduits (use FORCE_MAIN cross-section)
           - Pumps → Pumps (convert curves and controls)
        
        3. **Units:**
           - EPANET L/s → SWMM m³/s
           - Hazen-Williams C → Manning's n (if needed)
        
        4. **Time Settings:**
           - Add dynamic time settings
           - Define pump controls
           - Set up reporting intervals
        
        **Conversion Formula Examples:**
        ```
        SWMM Flow (m³/s) = EPANET Flow (L/s) ÷ 1000
        Manning's n ≈ 0.012-0.015 (for force mains)
        SWMM Diameter (m) = EPANET Diameter (mm) ÷ 1000
        ```
        """)
    
    # Practical comparison example
    st.subheader("Practical Example: Same System, Both Software")
    
    if st.button("Generate Comparison Example"):
        st.write("**Example System:**")
        st.write("- Wet well: 4m deep, 50 m² area")
        st.write("- Pump: 0.15 m³/s at 45m head")
        st.write("- Force main: 300mm diameter, 1000m length")
        st.write("- Discharge: 10m higher than wet well")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**SWMM5 Model Highlights:**")
            st.code("""
[STORAGE]
WW1  95.0  4.0  1.0  FUNCTIONAL  50.0

[PUMPS] 
P1   WW1  J1  PC1  ON  2.0  0.5

[CONDUITS]
FM1  J1  OUT1  1000  0.013  0  0

[XSECTIONS]
FM1  FORCE_MAIN  0.300  0  0  0  1

[CONTROLS]
RULE R1
IF NODE WW1 DEPTH > 2.0
THEN PUMP P1 STATUS = ON
            """)
        
        with col2:
            st.write("**EPANET Model Highlights:**")
            st.code("""
[TANKS]
WW1  95.0  1.0  0.1  4.0  8.0  0

[PUMPS]
P1   WW1  J1   HEAD  PC1

[PIPES]
FM1  J1  OUT1  1000  300  120  0  Open

[CURVES]
PC1  0.000  45.0
PC1  0.150  40.0
PC1  0.300  30.0

[CONTROLS]
LINK P1 1.0 IF NODE WW1 ABOVE 97.0
LINK P1 0.0 IF NODE WW1 BELOW 95.5
            """)
        
        st.info("💡 **Key Differences:** SWMM5 uses dynamic simulation with detailed wet well modeling, while EPANET uses steady-state with simplified tank representation.")

def troubleshooting_assistant():
    st.header("🔍 Troubleshooting Assistant")
    st.markdown("Diagnose and fix common force main modeling issues")
    
    assistant = TroubleshootingAssistant()
    
    st.subheader("Common Issues & Solutions")
    
    # Issue categories
    issue_category = st.selectbox(
        "Select Issue Category",
        [
            "Force Main Not Flowing Full",
            "Excessive Pressure",
            "Low Pressure/Cavitation",
            "High Velocities",
            "Pump Cycling",
            "Model Convergence Issues"
        ]
    )
    
    if issue_category == "Force Main Not Flowing Full":
        st.write("### 🔧 Force Main Partial Flow Solutions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Symptoms:**")
            st.write("- Pipe depth/diameter ratio < 0.95")
            st.write("- Air pockets in high points")
            st.write("- Inconsistent flow patterns")
            st.write("- H2S odor issues")
            
            st.write("**Primary Causes:**")
            st.write("- Insufficient discharge head")
            st.write("- Poor outfall design")
            st.write("- Inadequate air release")
            st.write("- Low flow conditions")
        
        with col2:
            st.write("**Solutions:**")
            
            st.success("**1. Add Break Node (Recommended)**")
            st.code("""
[JUNCTIONS]
BreakNode  105.0  3.0  0  1.5  0

[CONDUITS]
FM1_Out  BreakNode  Outfall  50  0.013  0  0  0  0
            """)
            
            st.info("**2. Install Air Release Valve**")
            st.write("- Place at high points")
            st.write("- Use combination air valves")
            st.write("- Size for 2x design flow")
            
            st.warning("**3. Increase Discharge Head**")
            st.write("- Raise pump curve")
            st.write("- Add booster pump")
            st.write("- Reduce system losses")
    
    elif issue_category == "Excessive Pressure":
        st.write("### ⚠️ High Pressure Solutions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Symptoms:**")
            st.write("- Pressure > 150 psi (103 m)")
            st.write("- Pipe stress concerns")
            st.write("- Joint failures")
            st.write("- Water hammer")
            
            st.write("**Causes:**")
            st.write("- Excessive pump head")
            st.write("- Valve closure")
            st.write("- Pipe blockage")
            st.write("- Pump start/stop")
        
        with col2:
            st.write("**Solutions:**")
            
            st.success("**1. Pressure Reducing Valve**")
            st.code("""
[OUTLETS]
PRV1  Node1  Node2  TABULAR/HEAD  PRV_Curve
            """)
            
            st.info("**2. Surge Protection**")
            st.write("- Air vessels")
            st.write("- Surge tanks")
            st.write("- Check valves")
            st.write("- Slow pump startup")
            
            st.warning("**3. System Modifications**")
            st.write("- Larger diameter pipe")
            st.write("- Parallel force mains")
            st.write("- Variable speed pumps")
    
    elif issue_category == "Low Pressure/Cavitation":
        st.write("### 🌊 Low Pressure & Cavitation Solutions")
        
        with st.expander("Diagnostic Tool", expanded=True):
            st.write("**Check System Conditions:**")
            
            col1, col2 = st.columns(2)
            with col1:
                elevation_diff = st.number_input("Elevation Difference (m)", value=20.0)
                pump_head = st.number_input("Pump Total Head (m)", value=40.0)
                pipe_length = st.number_input("Total Length (m)", value=1500.0)
                flow_rate = st.number_input("Flow Rate (m³/s)", value=0.2)
            
            with col2:
                pipe_diameter = st.number_input("Diameter (m)", value=0.3)
                roughness_c = st.number_input("H-W Coefficient", value=120)
                vapor_pressure = st.number_input("Vapor Pressure Head (m)", value=0.24)
                atmospheric_pressure = st.number_input("Atmospheric Pressure Head (m)", value=10.33)
            
            # Calculate NPSH available
            calc = ForceMainCalculator()
            friction_loss = calc.hazen_williams_loss(flow_rate, pipe_diameter, pipe_length, roughness_c)
            
            pressure_head = pump_head - elevation_diff - friction_loss
            npsh_available = atmospheric_pressure + pressure_head - vapor_pressure
            
            st.write("**Analysis Results:**")
            st.metric("System Pressure Head", f"{pressure_head:.2f} m")
            st.metric("NPSH Available", f"{npsh_available:.2f} m")
            
            if npsh_available < 3.0:
                st.error("❌ Risk of cavitation - NPSH too low")
                st.write("**Immediate Actions:**")
                st.write("- Reduce pump speed")
                st.write("- Increase suction pressure")
                st.write("- Check for blockages")
            elif npsh_available < 6.0:
                st.warning("⚠️ Marginal NPSH - monitor closely")
            else:
                st.success("✅ Adequate NPSH available")
    
    elif issue_category == "Model Convergence Issues":
        st.write("### 🔄 SWMM Convergence Troubleshooting")
        
        st.write("**Common Convergence Problems:**")
        
        with st.expander("1. Time Step Issues"):
            st.write("**Problem:** Model becomes unstable")
            st.write("**Solution:** Reduce time step")
            st.code("""
[OPTIONS]
VARIABLE_STEP     0.25
LENGTHENING_STEP  0
MIN_SURFAREA      1.14
            """)
        
        with st.expander("2. Force Main Oscillations"):
            st.write("**Problem:** Flow oscillates in force mains")
            st.write("**Solution:** Add damping or smaller time step")
            st.code("""
[OPTIONS]
VARIABLE_STEP     0.10
FORCE_MAIN_EQUATION   D-W
            """)
        
        with st.expander("3. Pump Cycling"):
            st.write("**Problem:** Pump rapidly starts/stops")
            st.write("**Solution:** Adjust wet well size or pump curve")
            
            st.write("**Wet Well Sizing Guide:**")
            pump_flow = st.number_input("Pump Flow Rate (m³/s)", value=0.15)
            cycle_time = st.number_input("Desired Cycle Time (min)", value=10.0)
            
            # Calculate required volume
            required_volume = pump_flow * cycle_time * 60 / 4  # Rule of thumb: 1/4 of pump volume per cycle
            
            st.metric("Recommended Wet Well Volume", f"{required_volume:.1f} m³")
            
            # Suggest dimensions
            depth_range = st.slider("Operating Depth Range (m)", 0.5, 3.0, 1.5)
            area_required = required_volume / depth_range
            
            st.metric("Required Surface Area", f"{area_required:.1f} m²")
            st.metric("Equivalent Diameter", f"{np.sqrt(4*area_required/np.pi):.1f} m")
    
    # Generate diagnostic report
    st.subheader("Generate Diagnostic Report")
    
    if st.button("Run System Diagnostics"):
        with st.spinner("Analyzing system..."):
            # Simulate diagnostic checks
            checks = [
                {"item": "Force Main Full Flow", "status": "✅ PASS", "details": "d/D ratio > 0.95"},
                {"item": "Velocity Range", "status": "⚠️ WARNING", "details": "Velocity = 0.45 m/s (recommend > 0.6 m/s)"},
                {"item": "Pressure Adequacy", "status": "✅ PASS", "details": "Minimum pressure = 15.2 m"},
                {"item": "NPSH Available", "status": "✅ PASS", "details": "NPSH = 8.1 m (> 3.0 m required)"},
                {"item": "System Efficiency", "status": "✅ PASS", "details": "Operating at 78% efficiency"},
                {"item": "Pump Curve Match", "status": "❌ FAIL", "details": "Operating outside optimal range"}
            ]
            
            st.write("**System Diagnostic Results:**")
            
            for check in checks:
                if "✅" in check["status"]:
                    st.success(f"{check['item']}: {check['status']} - {check['details']}")
                elif "⚠️" in check["status"]:
                    st.warning(f"{check['item']}: {check['status']} - {check['details']}")
                else:
                    st.error(f"{check['item']}: {check['status']} - {check['details']}")
            
            # Generate recommendations
            st.write("**Recommended Actions:**")
            st.write("1. 🔧 Increase minimum flow or reduce pipe diameter to achieve v > 0.6 m/s")
            st.write("2. 📊 Review pump selection - consider variable speed drive")
            st.write("3. 🔍 Verify pump curve data matches actual installation")
            st.write("4. 📋 Schedule quarterly performance monitoring")

if __name__ == "__main__":
    main()
