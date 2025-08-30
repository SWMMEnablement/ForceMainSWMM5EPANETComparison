import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.optimize import fsolve
import pandas as pd

class ForceMainNetwork:
    """
    Solve complex force main networks using Hardy Cross method
    and Newton-Raphson iteration
    """
    
    def __init__(self):
        self.nodes = {}
        self.links = {}
        self.pumps = {}
        self.tolerance = 0.001
        self.max_iterations = 100
        self.gravity = 9.81
        
    def add_wet_well(self, id, invert, max_depth, init_depth, area):
        """Add wet well to network"""
        self.nodes[id] = {
            'type': 'wet_well',
            'invert': invert,
            'max_depth': max_depth,
            'depth': init_depth,
            'area': area,
            'head': invert + init_depth,
            'demand': 0
        }
    
    def add_junction(self, id, invert, surcharge_depth=0, demand=0):
        """Add junction chamber to network"""
        self.nodes[id] = {
            'type': 'junction',
            'invert': invert,
            'surcharge_depth': surcharge_depth,
            'depth': 0,
            'head': invert,
            'demand': demand
        }
    
    def add_outfall(self, id, invert, stage=None):
        """Add outfall boundary condition"""
        self.nodes[id] = {
            'type': 'outfall',
            'invert': invert,
            'stage': stage or invert,
            'head': stage or invert,
            'demand': 0
        }
    
    def add_force_main(self, id, from_node, to_node, diameter, length, roughness, method='HW'):
        """Add force main link"""
        self.links[id] = {
            'type': 'force_main',
            'from': from_node,
            'to': to_node,
            'diameter': diameter,
            'length': length,
            'roughness': roughness,
            'method': method,  # 'HW' or 'DW'
            'flow': 0.1,  # Initial flow estimate
            'velocity': 0
        }
    
    def add_pump(self, id, from_node, to_node, curve_data, control=None):
        """Add pump to network"""
        self.pumps[id] = {
            'from': from_node,
            'to': to_node,
            'curve': curve_data,  # List of (flow, head) points
            'control': control,
            'flow': 0.1,
            'head': 0,
            'status': 'ON'
        }
    
    def interpolate_pump_curve(self, pump_id, flow):
        """Interpolate pump head from curve"""
        curve = self.pumps[pump_id]['curve']
        flows = [point[0] for point in curve]
        heads = [point[1] for point in curve]
        
        # Linear interpolation
        head = np.interp(flow, flows, heads)
        return max(head, 0)  # Prevent negative head
    
    def calculate_pipe_resistance(self, link_id, flow):
        """Calculate pipe resistance coefficient"""
        link = self.links[link_id]
        D = link['diameter']
        L = link['length']
        
        if link['method'] == 'HW':
            # Hazen-Williams: hf = K * Q^1.852
            C = link['roughness']
            K = 10.67 * L / (C**1.852 * D**4.87)
            n = 1.852
        else:
            # Darcy-Weisbach (simplified with constant f)
            # For full analysis, would need iterative solution
            f = 0.02  # Assumed friction factor
            K = f * L / (D * 2 * self.gravity) * 8 / (np.pi**2 * D**4)
            n = 2.0
        
        return K, n
    
    def calculate_head_loss(self, link_id, flow):
        """Calculate head loss for a link"""
        K, n = self.calculate_pipe_resistance(link_id, flow)
        
        # Handle direction
        if flow >= 0:
            return K * (flow**n)
        else:
            return -K * (abs(flow)**n)
    
    def calculate_head_loss_derivative(self, link_id, flow):
        """Calculate derivative of head loss with respect to flow"""
        K, n = self.calculate_pipe_resistance(link_id, flow)
        
        if abs(flow) < 1e-10:
            return K * n * (1e-10**(n-1))  # Avoid division by zero
        
        if flow >= 0:
            return K * n * (flow**(n-1))
        else:
            return K * n * (abs(flow)**(n-1))
    
    def build_jacobian_matrix(self):
        """Build Jacobian matrix for Newton-Raphson solution"""
        node_list = list(self.nodes.keys())
        n_nodes = len(node_list)
        
        # Exclude fixed head nodes (outfalls)
        free_nodes = [node for node in node_list if self.nodes[node]['type'] != 'outfall']
        n_free = len(free_nodes)
        
        if n_free == 0:
            return np.eye(1), np.zeros(1)
        
        A = np.zeros((n_free, n_free))
        b = np.zeros(n_free)
        
        # Build continuity equations
        for i, node_id in enumerate(free_nodes):
            node = self.nodes[node_id]
            flow_sum = -node['demand']  # Negative because demand is outflow
            
            # Add pipe flows
            for link_id, link in self.links.items():
                if link['from'] == node_id:
                    # Outflow
                    flow_sum -= link['flow']
                    j = free_nodes.index(link['to']) if link['to'] in free_nodes else -1
                    
                    # Add derivative terms
                    dh_dq = self.calculate_head_loss_derivative(link_id, link['flow'])
                    A[i, i] += dh_dq
                    if j >= 0:
                        A[i, j] -= dh_dq
                        
                elif link['to'] == node_id:
                    # Inflow
                    flow_sum += link['flow']
                    j = free_nodes.index(link['from']) if link['from'] in free_nodes else -1
                    
                    # Add derivative terms
                    dh_dq = self.calculate_head_loss_derivative(link_id, link['flow'])
                    A[i, i] += dh_dq
                    if j >= 0:
                        A[i, j] -= dh_dq
            
            # Add pump flows
            for pump_id, pump in self.pumps.items():
                if pump['status'] == 'OFF':
                    continue
                    
                if pump['from'] == node_id:
                    flow_sum -= pump['flow']
                elif pump['to'] == node_id:
                    flow_sum += pump['flow']
            
            b[i] = flow_sum
        
        return A, b
    
    def update_flows_from_heads(self):
        """Update link flows based on current head distribution"""
        for link_id, link in self.links.items():
            from_head = self.nodes[link['from']]['head']
            to_head = self.nodes[link['to']]['head']
            
            # Calculate flow from head difference
            dh = from_head - to_head
            
            # Use iterative method to find flow that produces this head loss
            def head_balance(q):
                return self.calculate_head_loss(link_id, q) - dh
            
            try:
                flow = fsolve(head_balance, link['flow'])[0]
                link['flow'] = flow
                
                # Update velocity
                area = np.pi * link['diameter']**2 / 4
                link['velocity'] = flow / area
                
            except:
                # If solver fails, use previous flow
                pass
    
    def update_pump_flows(self):
        """Update pump flows based on operating conditions"""
        for pump_id, pump in self.pumps.items():
            if pump['status'] == 'OFF':
                pump['flow'] = 0
                pump['head'] = 0
                continue
            
            from_head = self.nodes[pump['from']]['head']
            to_head = self.nodes[pump['to']]['head']
            required_head = to_head - from_head
            
            # Find intersection of system curve and pump curve
            def find_operating_point(q):
                pump_head = self.interpolate_pump_curve(pump_id, q)
                return pump_head - required_head
            
            try:
                flow = fsolve(find_operating_point, pump['flow'])[0]
                pump['flow'] = max(flow, 0)  # No negative pump flow
                pump['head'] = self.interpolate_pump_curve(pump_id, pump['flow'])
            except:
                # Keep previous values if solver fails
                pass
    
    def solve_network(self):
        """
        Solve network using Newton-Raphson method
        
        Returns:
        tuple: (converged, iterations, results)
        """
        iteration = 0
        converged = False
        
        # Initialize heads
        for node_id, node in self.nodes.items():
            if node['type'] == 'outfall':
                node['head'] = node['stage']
            elif node['type'] == 'wet_well':
                node['head'] = node['invert'] + node['depth']
            else:
                node['head'] = node['invert']
        
        convergence_history = []
        
        while not converged and iteration < self.max_iterations:
            # Store previous heads
            prev_heads = {node_id: node['head'] for node_id, node in self.nodes.items()}
            
            # Update flows from current heads
            self.update_flows_from_heads()
            self.update_pump_flows()
            
            # Build and solve matrix system
            try:
                A, b = self.build_jacobian_matrix()
                
                if A.size > 0:
                    delta_H = np.linalg.solve(A, -b)
                    
                    # Update heads for free nodes
                    free_nodes = [node for node in self.nodes.keys() 
                                if self.nodes[node]['type'] != 'outfall']
                    
                    for i, node_id in enumerate(free_nodes):
                        if i < len(delta_H):
                            self.nodes[node_id]['head'] += delta_H[i]
                
                # Check convergence
                max_change = 0
                for node_id in self.nodes.keys():
                    if self.nodes[node_id]['type'] != 'outfall':
                        change = abs(self.nodes[node_id]['head'] - prev_heads[node_id])
                        max_change = max(max_change, change)
                
                convergence_history.append(max_change)
                converged = max_change < self.tolerance
                
            except np.linalg.LinAlgError:
                # Matrix is singular, try to continue
                converged = False
            
            iteration += 1
        
        # Compile results
        results = {
            'nodes': dict(self.nodes),
            'links': dict(self.links),
            'pumps': dict(self.pumps),
            'converged': converged,
            'iterations': iteration,
            'convergence_history': convergence_history
        }
        
        return converged, iteration, results
    
    def calculate_system_curve(self, pump_id, flow_range):
        """
        Calculate system curve for pump analysis
        
        Parameters:
        pump_id: ID of pump to analyze
        flow_range: Array of flow rates to analyze
        
        Returns:
        tuple: (flows, system_heads)
        """
        pump = self.pumps[pump_id]
        from_node = pump['from']
        to_node = pump['to']
        
        system_heads = []
        
        for flow in flow_range:
            # Set pump flow
            original_flow = pump['flow']
            pump['flow'] = flow
            
            # Calculate system head requirement
            static_head = self.nodes[to_node]['invert'] - self.nodes[from_node]['invert']
            
            # Add friction losses in downstream pipes
            friction_head = 0
            for link_id, link in self.links.items():
                if link['from'] == to_node or link['to'] == to_node:
                    friction_head += self.calculate_head_loss(link_id, flow)
            
            total_head = static_head + friction_head
            system_heads.append(total_head)
            
            # Restore original flow
            pump['flow'] = original_flow
        
        return flow_range, system_heads
    
    def validate_network(self):
        """
        Validate network configuration
        
        Returns:
        dict: Validation results with warnings and errors
        """
        warnings = []
        errors = []
        
        # Check node connectivity
        connected_nodes = set()
        for link in self.links.values():
            connected_nodes.add(link['from'])
            connected_nodes.add(link['to'])
        for pump in self.pumps.values():
            connected_nodes.add(pump['from'])
            connected_nodes.add(pump['to'])
        
        for node_id in self.nodes.keys():
            if node_id not in connected_nodes:
                warnings.append(f"Node {node_id} is not connected to any links")
        
        # Check for outfalls
        outfall_count = sum(1 for node in self.nodes.values() if node['type'] == 'outfall')
        if outfall_count == 0:
            errors.append("Network must have at least one outfall")
        
        # Check velocities
        for link_id, link in self.links.items():
            if abs(link['velocity']) > 3.0:
                warnings.append(f"High velocity in {link_id}: {link['velocity']:.2f} m/s")
            elif abs(link['velocity']) < 0.6:
                warnings.append(f"Low velocity in {link_id}: {link['velocity']:.2f} m/s")
        
        # Check pump operations
        for pump_id, pump in self.pumps.items():
            if pump['flow'] < 0:
                warnings.append(f"Pump {pump_id} has negative flow - check system design")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'is_valid': len(errors) == 0
        }
