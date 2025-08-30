import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd

class HydraulicVisualizer:
    """
    Create hydraulic visualizations for force main systems
    """
    
    def __init__(self):
        self.default_colors = {
            'pipe_invert': '#8B4513',
            'pipe_crown': '#A0522D',
            'hgl': '#0066CC',
            'pressure': '#FF6B35',
            'velocity': '#28A745',
            'flow': '#6F42C1'
        }
    
    def plot_hydraulic_profile(self, stations, elevations, hgl, pipe_diameter, title="Hydraulic Profile"):
        """
        Create hydraulic grade line profile plot
        
        Parameters:
        stations: Array of station points along pipe (m)
        elevations: Array of pipe invert elevations (m)
        hgl: Array of hydraulic grade line elevations (m)
        pipe_diameter: Pipe diameter (m)
        title: Plot title
        
        Returns:
        plotly figure object
        """
        # Calculate pipe crown
        pipe_crown = elevations + pipe_diameter
        
        fig = go.Figure()
        
        # Ground surface (estimated as 2m above pipe crown)
        ground_surface = pipe_crown + 2.0
        
        # Add ground surface
        fig.add_trace(go.Scatter(
            x=stations, y=ground_surface,
            mode='lines',
            name='Ground Surface',
            line=dict(color='brown', width=1, dash='dot'),
            fill='tonexty',
            fillcolor='rgba(139, 69, 19, 0.3)'
        ))
        
        # Add pipe invert
        fig.add_trace(go.Scatter(
            x=stations, y=elevations,
            mode='lines',
            name='Pipe Invert',
            line=dict(color=self.default_colors['pipe_invert'], width=3)
        ))
        
        # Add pipe crown
        fig.add_trace(go.Scatter(
            x=stations, y=pipe_crown,
            mode='lines',
            name='Pipe Crown',
            line=dict(color=self.default_colors['pipe_crown'], width=2, dash='dash')
        ))
        
        # Add hydraulic grade line
        fig.add_trace(go.Scatter(
            x=stations, y=hgl,
            mode='lines',
            name='Hydraulic Grade Line',
            line=dict(color=self.default_colors['hgl'], width=4),
            fill='tonexty',
            fillcolor='rgba(0, 102, 204, 0.2)'
        ))
        
        # Calculate pressure head
        pressure_head = hgl - pipe_crown
        
        # Add annotations for critical points
        min_pressure_idx = np.argmin(pressure_head)
        max_pressure_idx = np.argmax(pressure_head)
        
        fig.add_annotation(
            x=stations[min_pressure_idx],
            y=hgl[min_pressure_idx],
            text=f"Min Pressure: {pressure_head[min_pressure_idx]:.1f}m",
            showarrow=True,
            arrowhead=2,
            arrowcolor="red"
        )
        
        fig.add_annotation(
            x=stations[max_pressure_idx],
            y=hgl[max_pressure_idx],
            text=f"Max Pressure: {pressure_head[max_pressure_idx]:.1f}m",
            showarrow=True,
            arrowhead=2,
            arrowcolor="blue"
        )
        
        fig.update_layout(
            title=title,
            xaxis_title="Distance (m)",
            yaxis_title="Elevation (m)",
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=500
        )
        
        return fig
    
    def plot_pump_system_curves(self, pump_curve_data, system_curve_data, operating_point=None):
        """
        Plot pump curve and system curve intersection
        
        Parameters:
        pump_curve_data: List of (flow, head) tuples for pump curve
        system_curve_data: List of (flow, head) tuples for system curve
        operating_point: (flow, head) tuple for operating point
        
        Returns:
        plotly figure object
        """
        fig = go.Figure()
        
        # Pump curve
        pump_flows = [point[0] for point in pump_curve_data]
        pump_heads = [point[1] for point in pump_curve_data]
        
        fig.add_trace(go.Scatter(
            x=pump_flows, y=pump_heads,
            mode='lines+markers',
            name='Pump Curve',
            line=dict(color='blue', width=3),
            marker=dict(size=6)
        ))
        
        # System curve
        system_flows = [point[0] for point in system_curve_data]
        system_heads = [point[1] for point in system_curve_data]
        
        fig.add_trace(go.Scatter(
            x=system_flows, y=system_heads,
            mode='lines',
            name='System Curve',
            line=dict(color='red', width=3)
        ))
        
        # Operating point
        if operating_point:
            fig.add_trace(go.Scatter(
                x=[operating_point[0]], y=[operating_point[1]],
                mode='markers',
                name='Operating Point',
                marker=dict(size=12, color='green', symbol='star')
            ))
            
            fig.add_annotation(
                x=operating_point[0],
                y=operating_point[1],
                text=f"Operating Point<br>Q: {operating_point[0]:.3f} m³/s<br>H: {operating_point[1]:.1f} m",
                showarrow=True,
                arrowhead=2,
                bgcolor="white",
                bordercolor="green"
            )
        
        fig.update_layout(
            title="Pump and System Characteristic Curves",
            xaxis_title="Flow Rate (m³/s)",
            yaxis_title="Head (m)",
            hovermode='closest',
            height=500
        )
        
        return fig
    
    def plot_velocity_profile(self, stations, velocities, min_velocity=0.6, max_velocity=3.0):
        """
        Plot velocity along force main with recommended limits
        
        Parameters:
        stations: Array of station points (m)
        velocities: Array of velocities (m/s)
        min_velocity: Minimum recommended velocity (m/s)
        max_velocity: Maximum recommended velocity (m/s)
        
        Returns:
        plotly figure object
        """
        fig = go.Figure()
        
        # Velocity profile
        fig.add_trace(go.Scatter(
            x=stations, y=velocities,
            mode='lines',
            name='Velocity',
            line=dict(color=self.default_colors['velocity'], width=3)
        ))
        
        # Recommended velocity limits
        fig.add_hline(
            y=min_velocity,
            line_dash="dash",
            line_color="orange",
            annotation_text=f"Min Recommended: {min_velocity} m/s"
        )
        
        fig.add_hline(
            y=max_velocity,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Max Recommended: {max_velocity} m/s"
        )
        
        # Fill areas for velocity ranges
        x_fill = np.concatenate([stations, stations[::-1]])
        y_fill_low = np.concatenate([np.full_like(stations, 0), np.full_like(stations, min_velocity)][::-1])
        y_fill_high = np.concatenate([np.full_like(stations, max_velocity), np.full_like(stations, 10)][::-1])
        
        fig.add_trace(go.Scatter(
            x=x_fill, y=y_fill_low,
            fill='toself',
            fillcolor='rgba(255, 0, 0, 0.1)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Too Low',
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=x_fill, y=y_fill_high,
            fill='toself',
            fillcolor='rgba(255, 0, 0, 0.1)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Too High',
            showlegend=False
        ))
        
        fig.update_layout(
            title="Velocity Profile Along Force Main",
            xaxis_title="Distance (m)",
            yaxis_title="Velocity (m/s)",
            hovermode='x unified',
            height=400
        )
        
        return fig
    
    def plot_pressure_analysis(self, stations, pressure_heads, pipe_class_pressure=None):
        """
        Plot pressure analysis with pipe class limits
        
        Parameters:
        stations: Array of station points (m)
        pressure_heads: Array of pressure heads (m)
        pipe_class_pressure: Maximum allowable pressure for pipe class (m)
        
        Returns:
        plotly figure object
        """
        fig = go.Figure()
        
        # Pressure profile
        fig.add_trace(go.Scatter(
            x=stations, y=pressure_heads,
            mode='lines',
            name='Pressure Head',
            line=dict(color=self.default_colors['pressure'], width=3)
        ))
        
        # Pipe class limit
        if pipe_class_pressure:
            fig.add_hline(
                y=pipe_class_pressure,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Pipe Class Limit: {pipe_class_pressure} m"
            )
        
        # Zero pressure line
        fig.add_hline(
            y=0,
            line_dash="solid",
            line_color="black",
            line_width=1,
            annotation_text="Zero Pressure"
        )
        
        # Highlight negative pressure areas
        negative_pressure = pressure_heads < 0
        if np.any(negative_pressure):
            fig.add_trace(go.Scatter(
                x=stations[negative_pressure],
                y=pressure_heads[negative_pressure],
                mode='markers',
                name='Negative Pressure',
                marker=dict(color='red', size=8, symbol='x')
            ))
        
        # Statistics
        min_pressure = np.min(pressure_heads)
        max_pressure = np.max(pressure_heads)
        
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            text=f"Min: {min_pressure:.1f}m<br>Max: {max_pressure:.1f}m",
            showarrow=False,
            bgcolor="white",
            bordercolor="gray"
        )
        
        fig.update_layout(
            title="Pressure Analysis Along Force Main",
            xaxis_title="Distance (m)",
            yaxis_title="Pressure Head (m)",
            hovermode='x unified',
            height=400
        )
        
        return fig
    
    def plot_network_schematic(self, nodes_data, links_data, pumps_data=None):
        """
        Create network schematic diagram
        
        Parameters:
        nodes_data: Dictionary of node data
        links_data: Dictionary of link data
        pumps_data: Dictionary of pump data (optional)
        
        Returns:
        plotly figure object
        """
        fig = go.Figure()
        
        # Plot links first (so they appear behind nodes)
        for link_id, link in links_data.items():
            from_node = nodes_data[link['from']]
            to_node = nodes_data[link['to']]
            
            # Use elevation as y-coordinate
            x_coords = [from_node.get('x', 0), to_node.get('x', 1)]
            y_coords = [from_node.get('elevation', from_node.get('invert', 0)), 
                       to_node.get('elevation', to_node.get('invert', 0))]
            
            fig.add_trace(go.Scatter(
                x=x_coords, y=y_coords,
                mode='lines',
                name=f'Link {link_id}',
                line=dict(width=6, color='blue'),
                showlegend=False,
                hovertemplate=f"Link: {link_id}<br>Diameter: {link.get('diameter', 'N/A')}m<br>Flow: {link.get('flow', 0):.3f} m³/s"
            ))
        
        # Plot pumps
        if pumps_data:
            for pump_id, pump in pumps_data.items():
                from_node = nodes_data[pump['from']]
                to_node = nodes_data[pump['to']]
                
                x_coords = [from_node.get('x', 0), to_node.get('x', 1)]
                y_coords = [from_node.get('elevation', from_node.get('invert', 0)), 
                           to_node.get('elevation', to_node.get('invert', 0))]
                
                fig.add_trace(go.Scatter(
                    x=x_coords, y=y_coords,
                    mode='lines',
                    name=f'Pump {pump_id}',
                    line=dict(width=8, color='red'),
                    showlegend=False,
                    hovertemplate=f"Pump: {pump_id}<br>Flow: {pump.get('flow', 0):.3f} m³/s<br>Head: {pump.get('head', 0):.1f} m"
                ))
        
        # Plot nodes
        for node_id, node in nodes_data.items():
            x_pos = node.get('x', 0)
            y_pos = node.get('elevation', node.get('invert', 0))
            
            if node['type'] == 'wet_well':
                marker_symbol = 'square'
                marker_color = 'red'
                marker_size = 15
            elif node['type'] == 'outfall':
                marker_symbol = 'triangle-down'
                marker_color = 'green'
                marker_size = 15
            else:
                marker_symbol = 'circle'
                marker_color = 'blue'
                marker_size = 12
            
            fig.add_trace(go.Scatter(
                x=[x_pos], y=[y_pos],
                mode='markers+text',
                name=f'{node["type"].title()} {node_id}',
                marker=dict(
                    symbol=marker_symbol,
                    size=marker_size,
                    color=marker_color,
                    line=dict(width=2, color='black')
                ),
                text=[node_id],
                textposition="top center",
                showlegend=False,
                hovertemplate=f"Node: {node_id}<br>Type: {node['type']}<br>Elevation: {y_pos:.1f}m<br>Head: {node.get('head', 'N/A')}"
            ))
        
        fig.update_layout(
            title="Force Main Network Schematic",
            xaxis_title="Horizontal Distance",
            yaxis_title="Elevation (m)",
            hovermode='closest',
            height=500,
            showlegend=False
        )
        
        return fig
    
    def plot_time_series(self, time_data, flow_data, pressure_data=None, velocity_data=None):
        """
        Plot time series data for system performance
        
        Parameters:
        time_data: Array of time values
        flow_data: Array of flow rates
        pressure_data: Array of pressure values (optional)
        velocity_data: Array of velocity values (optional)
        
        Returns:
        plotly figure object with subplots
        """
        # Determine number of subplots
        n_plots = 1 + (pressure_data is not None) + (velocity_data is not None)
        
        fig = make_subplots(
            rows=n_plots, cols=1,
            subplot_titles=['Flow Rate', 'Pressure Head', 'Velocity'][:n_plots],
            vertical_spacing=0.1
        )
        
        # Flow rate plot
        fig.add_trace(
            go.Scatter(x=time_data, y=flow_data, name='Flow Rate', line=dict(color='blue')),
            row=1, col=1
        )
        
        row = 2
        
        # Pressure plot
        if pressure_data is not None:
            fig.add_trace(
                go.Scatter(x=time_data, y=pressure_data, name='Pressure Head', line=dict(color='red')),
                row=row, col=1
            )
            row += 1
        
        # Velocity plot
        if velocity_data is not None:
            fig.add_trace(
                go.Scatter(x=time_data, y=velocity_data, name='Velocity', line=dict(color='green')),
                row=row, col=1
            )
        
        # Update y-axis labels
        fig.update_yaxes(title_text="Flow Rate (m³/s)", row=1, col=1)
        if pressure_data is not None:
            fig.update_yaxes(title_text="Pressure Head (m)", row=2, col=1)
        if velocity_data is not None:
            fig.update_yaxes(title_text="Velocity (m/s)", row=n_plots, col=1)
        
        fig.update_xaxes(title_text="Time", row=n_plots, col=1)
        
        fig.update_layout(
            title="System Performance Over Time",
            height=150 * n_plots + 100,
            showlegend=False
        )
        
        return fig
    
    def create_friction_comparison_chart(self, flow_range, hw_losses, dw_losses):
        """
        Create comparison chart for Hazen-Williams vs Darcy-Weisbach friction losses
        
        Parameters:
        flow_range: Array of flow rates
        hw_losses: Array of H-W head losses
        dw_losses: Array of D-W head losses
        
        Returns:
        plotly figure object
        """
        fig = go.Figure()
        
        # Hazen-Williams curve
        fig.add_trace(go.Scatter(
            x=flow_range, y=hw_losses,
            mode='lines',
            name='Hazen-Williams',
            line=dict(color='blue', width=3)
        ))
        
        # Darcy-Weisbach curve
        fig.add_trace(go.Scatter(
            x=flow_range, y=dw_losses,
            mode='lines',
            name='Darcy-Weisbach',
            line=dict(color='red', width=3)
        ))
        
        # Difference area
        fig.add_trace(go.Scatter(
            x=np.concatenate([flow_range, flow_range[::-1]]),
            y=np.concatenate([hw_losses, dw_losses[::-1]]),
            fill='toself',
            fillcolor='rgba(128, 128, 128, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Difference',
            showlegend=False
        ))
        
        # Calculate and display statistics
        avg_diff = np.mean(np.abs(np.array(dw_losses) - np.array(hw_losses)))
        max_diff = np.max(np.abs(np.array(dw_losses) - np.array(hw_losses)))
        
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            text=f"Avg Difference: {avg_diff:.3f}m<br>Max Difference: {max_diff:.3f}m",
            showarrow=False,
            bgcolor="white",
            bordercolor="gray"
        )
        
        fig.update_layout(
            title="Friction Loss Method Comparison",
            xaxis_title="Flow Rate (m³/s)",
            yaxis_title="Head Loss (m)",
            hovermode='x unified',
            height=500
        )
        
        return fig
