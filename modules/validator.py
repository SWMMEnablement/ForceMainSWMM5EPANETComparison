import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any

class ModelConsistencyChecker:
    """
    Validate consistency between SWMM5 and EPANET models
    Following rules from "Rules for Modeling a Force Main in SWMM5 and EPANET"
    """
    
    def __init__(self):
        self.issues = []
        self.tolerance = 0.1  # 10% tolerance for acceptable differences
        
    def check_physical_parameters(self, swmm_config: Dict, epanet_config: Dict) -> List[Dict]:
        """
        Rule 1: Verify physical parameters match between models
        """
        self.issues = []
        
        # Check diameter
        swmm_diam = swmm_config['force_main']['diameter']
        epanet_diam = epanet_config['force_main']['diameter']
        if abs(swmm_diam - epanet_diam) / swmm_diam > 0.001:
            self.issues.append({
                'rule': 'Rule 1 - Physical Parameters',
                'severity': 'HIGH',
                'parameter': 'Diameter',
                'swmm_value': f"{swmm_diam:.4f} m",
                'epanet_value': f"{epanet_diam:.4f} m",
                'issue': 'Pipe diameters do not match between SWMM5 and EPANET'
            })
        
        # Check length
        swmm_length = swmm_config['force_main']['length']
        epanet_length = epanet_config['force_main']['length']
        if abs(swmm_length - epanet_length) / swmm_length > 0.001:
            self.issues.append({
                'rule': 'Rule 1 - Physical Parameters',
                'severity': 'HIGH',
                'parameter': 'Length',
                'swmm_value': f"{swmm_length:.2f} m",
                'epanet_value': f"{epanet_length:.2f} m",
                'issue': 'Pipe lengths do not match between SWMM5 and EPANET'
            })
        
        # Check roughness
        swmm_rough = swmm_config['force_main']['roughness']
        epanet_rough = epanet_config['force_main']['roughness']
        if abs(swmm_rough - epanet_rough) / max(swmm_rough, 0.001) > 0.001:
            self.issues.append({
                'rule': 'Rule 1 - Physical Parameters',
                'severity': 'HIGH',
                'parameter': 'Roughness',
                'swmm_value': f"{swmm_rough:.4f}",
                'epanet_value': f"{epanet_rough:.4f}",
                'issue': 'Roughness coefficients do not match between SWMM5 and EPANET'
            })
        
        return self.issues
    
    def check_pump_curves(self, swmm_pump: Dict, epanet_pump: Dict) -> List[Dict]:
        """
        Rule 6 & 8: Verify pump curves are identical
        """
        swmm_curve = swmm_pump.get('curve_data', [])
        epanet_curve = epanet_pump.get('curve_data', [])
        
        if len(swmm_curve) != len(epanet_curve):
            self.issues.append({
                'rule': 'Rule 6/8 - Pump Curves',
                'severity': 'HIGH',
                'parameter': 'Pump Curve Points',
                'swmm_value': f"{len(swmm_curve)} points",
                'epanet_value': f"{len(epanet_curve)} points",
                'issue': 'Pump curves have different number of points'
            })
            return self.issues
        
        # Check each point
        for i, (swmm_pt, epanet_pt) in enumerate(zip(swmm_curve, epanet_curve)):
            swmm_flow, swmm_head = swmm_pt
            epanet_flow, epanet_head = epanet_pt
            
            if abs(swmm_flow - epanet_flow) / max(swmm_flow, 0.001) > 0.01:
                self.issues.append({
                    'rule': 'Rule 6/8 - Pump Curves',
                    'severity': 'HIGH',
                    'parameter': f'Pump Curve Point {i+1} - Flow',
                    'swmm_value': f"{swmm_flow:.4f} m³/s",
                    'epanet_value': f"{epanet_flow:.4f} m³/s",
                    'issue': f'Pump curve flow rates differ at point {i+1}'
                })
            
            if abs(swmm_head - epanet_head) / max(swmm_head, 0.1) > 0.01:
                self.issues.append({
                    'rule': 'Rule 6/8 - Pump Curves',
                    'severity': 'HIGH',
                    'parameter': f'Pump Curve Point {i+1} - Head',
                    'swmm_value': f"{swmm_head:.2f} m",
                    'epanet_value': f"{epanet_head:.2f} m",
                    'issue': f'Pump curve head values differ at point {i+1}'
                })
        
        return self.issues
    
    def check_boundary_conditions(self, swmm_config: Dict, epanet_config: Dict) -> List[Dict]:
        """
        Rule 3: Verify boundary conditions alignment
        """
        # Check wet well elevations
        swmm_ww_elev = swmm_config['wet_well'].get('invert', 0)
        epanet_ww_elev = epanet_config['wet_well'].get('invert', 0)
        
        if abs(swmm_ww_elev - epanet_ww_elev) > 0.01:
            self.issues.append({
                'rule': 'Rule 3 - Boundary Conditions',
                'severity': 'MEDIUM',
                'parameter': 'Wet Well Elevation',
                'swmm_value': f"{swmm_ww_elev:.2f} m",
                'epanet_value': f"{epanet_ww_elev:.2f} m",
                'issue': 'Wet well elevations do not match'
            })
        
        # Check discharge elevations
        swmm_dn_elev = swmm_config['discharge_node'].get('elevation', 0)
        epanet_dn_elev = epanet_config['discharge_node'].get('elevation', 0)
        
        if abs(swmm_dn_elev - epanet_dn_elev) > 0.01:
            self.issues.append({
                'rule': 'Rule 3 - Boundary Conditions',
                'severity': 'MEDIUM',
                'parameter': 'Discharge Elevation',
                'swmm_value': f"{swmm_dn_elev:.2f} m",
                'epanet_value': f"{epanet_dn_elev:.2f} m",
                'issue': 'Discharge elevations do not match'
            })
        
        return self.issues
    
    def generate_consistency_report(self, swmm_config: Dict, epanet_config: Dict) -> Dict:
        """
        Generate complete consistency report between SWMM5 and EPANET models
        """
        all_issues = []
        
        # Check all rules
        all_issues.extend(self.check_physical_parameters(swmm_config, epanet_config))
        all_issues.extend(self.check_pump_curves(
            swmm_config.get('pump', {}), 
            epanet_config.get('pump', {})
        ))
        all_issues.extend(self.check_boundary_conditions(swmm_config, epanet_config))
        
        # Categorize by severity
        high_severity = [i for i in all_issues if i['severity'] == 'HIGH']
        medium_severity = [i for i in all_issues if i['severity'] == 'MEDIUM']
        
        report = {
            'total_issues': len(all_issues),
            'high_severity': len(high_severity),
            'medium_severity': len(medium_severity),
            'all_issues': all_issues,
            'is_consistent': len(high_severity) == 0,
            'summary': f"Found {len(all_issues)} consistency issues " +
                      f"({len(high_severity)} high, {len(medium_severity)} medium)"
        }
        
        return report

class TroubleshootingAssistant:
    """
    Diagnose and fix common force main modeling issues in SWMM5
    """
    
    def __init__(self):
        self.issues = []
        self.recommendations = []
        self.gravity = 9.81
        self.min_velocity = 0.6  # m/s - minimum to prevent settling
        self.max_velocity = 3.0  # m/s - maximum to prevent excessive wear
        self.min_pressure_head = 3.0  # m - minimum to prevent cavitation
        
    def reset_diagnostics(self):
        """Clear previous diagnostic results"""
        self.issues = []
        self.recommendations = []
    
    def check_force_main_full_flow(self, depth_diameter_ratio: float, location: str = "force_main"):
        """
        Check if force main maintains full flow condition
        
        Parameters:
        depth_diameter_ratio: Ratio of flow depth to pipe diameter
        location: Identifier for the location being checked
        """
        if depth_diameter_ratio < 0.95:
            self.issues.append({
                'severity': 'HIGH',
                'category': 'Hydraulic Performance',
                'issue': f'Force main not flowing full at {location}',
                'details': f'd/D ratio = {depth_diameter_ratio:.3f} (should be ≥ 0.95)',
                'location': location,
                'priority': 1
            })
            
            self.add_full_flow_recommendations()
    
    def check_velocity_range(self, velocity: float, diameter: float, location: str = "force_main"):
        """
        Check if velocity is within acceptable range
        
        Parameters:
        velocity: Flow velocity (m/s)
        diameter: Pipe diameter (m)
        location: Identifier for the location being checked
        """
        if velocity < self.min_velocity:
            self.issues.append({
                'severity': 'MEDIUM',
                'category': 'Solids Transport',
                'issue': f'Low velocity may cause solids settling',
                'details': f'Velocity = {velocity:.2f} m/s (minimum recommended: {self.min_velocity} m/s)',
                'location': location,
                'priority': 2
            })
            
            self.add_velocity_recommendations(velocity, diameter, 'low')
            
        elif velocity > self.max_velocity:
            self.issues.append({
                'severity': 'MEDIUM',
                'category': 'Pipe Wear',
                'issue': f'High velocity may cause excessive pipe wear',
                'details': f'Velocity = {velocity:.2f} m/s (maximum recommended: {self.max_velocity} m/s)',
                'location': location,
                'priority': 2
            })
            
            self.add_velocity_recommendations(velocity, diameter, 'high')
    
    def check_pressure_adequacy(self, pressure_head: float, location: str = "force_main"):
        """
        Check if pressure is adequate throughout system
        
        Parameters:
        pressure_head: Pressure head (m)
        location: Identifier for the location being checked
        """
        if pressure_head < 0:
            self.issues.append({
                'severity': 'CRITICAL',
                'category': 'Pressure',
                'issue': f'Negative pressure detected - risk of air entrainment',
                'details': f'Pressure head = {pressure_head:.2f} m',
                'location': location,
                'priority': 1
            })
            
            self.add_negative_pressure_recommendations()
            
        elif pressure_head < self.min_pressure_head:
            self.issues.append({
                'severity': 'HIGH',
                'category': 'Pressure',
                'issue': f'Low pressure - risk of cavitation',
                'details': f'Pressure head = {pressure_head:.2f} m (minimum recommended: {self.min_pressure_head} m)',
                'location': location,
                'priority': 1
            })
            
            self.add_low_pressure_recommendations()
    
    def check_pump_operating_point(self, pump_flow: float, pump_head: float, 
                                  curve_data: List[Tuple[float, float]], pump_id: str = "pump"):
        """
        Check if pump is operating within acceptable range of its curve
        
        Parameters:
        pump_flow: Current pump flow rate (m³/s)
        pump_head: Current pump head (m)
        curve_data: List of (flow, head) tuples defining pump curve
        pump_id: Pump identifier
        """
        flows = [point[0] for point in curve_data]
        heads = [point[1] for point in curve_data]
        
        min_flow = min(flows)
        max_flow = max(flows)
        
        # Check if operating outside flow range
        if pump_flow < min_flow * 0.7 or pump_flow > max_flow * 1.1:
            self.issues.append({
                'severity': 'HIGH',
                'category': 'Pump Performance',
                'issue': f'Pump {pump_id} operating outside recommended range',
                'details': f'Current flow: {pump_flow:.3f} m³/s, Curve range: {min_flow:.3f} - {max_flow:.3f} m³/s',
                'location': pump_id,
                'priority': 1
            })
            
            self.add_pump_curve_recommendations(pump_flow, min_flow, max_flow)
        
        # Check efficiency (simplified - assumes best efficiency at mid-range)
        optimal_flow = (min_flow + max_flow) / 2
        efficiency_factor = 1 - abs(pump_flow - optimal_flow) / optimal_flow
        
        if efficiency_factor < 0.7:
            self.issues.append({
                'severity': 'MEDIUM',
                'category': 'Energy Efficiency',
                'issue': f'Pump {pump_id} operating at low efficiency',
                'details': f'Estimated efficiency factor: {efficiency_factor:.2f}',
                'location': pump_id,
                'priority': 2
            })
    
    def check_npsh_available(self, suction_pressure: float, vapor_pressure: float,
                           velocity_head: float, suction_losses: float, 
                           npsh_required: float = 3.0, location: str = "pump_suction"):
        """
        Check Net Positive Suction Head Available vs Required
        
        Parameters:
        suction_pressure: Absolute pressure at pump suction (m)
        vapor_pressure: Vapor pressure of liquid (m)
        velocity_head: Velocity head at suction (m)
        suction_losses: Total suction line losses (m)
        npsh_required: Required NPSH for pump (m)
        location: Location identifier
        """
        npsh_available = suction_pressure - vapor_pressure - velocity_head - suction_losses
        
        if npsh_available < npsh_required:
            self.issues.append({
                'severity': 'CRITICAL',
                'category': 'Cavitation',
                'issue': f'Insufficient NPSH - cavitation risk',
                'details': f'NPSH Available: {npsh_available:.2f} m, Required: {npsh_required:.2f} m',
                'location': location,
                'priority': 1
            })
            
            self.add_npsh_recommendations(npsh_available, npsh_required)
        
        elif npsh_available < npsh_required * 1.5:
            self.issues.append({
                'severity': 'MEDIUM',
                'category': 'Cavitation',
                'issue': f'Marginal NPSH - monitor closely',
                'details': f'NPSH Available: {npsh_available:.2f} m, Required: {npsh_required:.2f} m',
                'location': location,
                'priority': 2
            })
    
    def check_wet_well_sizing(self, wet_well_volume: float, pump_flow: float,
                             cycle_time_min: float = 10.0, wet_well_id: str = "wet_well"):
        """
        Check if wet well is properly sized for pump cycling
        
        Parameters:
        wet_well_volume: Available storage volume between start/stop levels (m³)
        pump_flow: Pump flow rate (m³/s)
        cycle_time_min: Desired minimum cycle time (minutes)
        wet_well_id: Wet well identifier
        """
        required_volume = pump_flow * cycle_time_min * 60 / 4  # Rule of thumb: 1/4 pump volume per cycle
        
        if wet_well_volume < required_volume * 0.8:
            self.issues.append({
                'severity': 'HIGH',
                'category': 'Pump Cycling',
                'issue': f'Wet well {wet_well_id} may cause excessive pump cycling',
                'details': f'Available volume: {wet_well_volume:.1f} m³, Recommended: {required_volume:.1f} m³',
                'location': wet_well_id,
                'priority': 1
            })
            
            self.add_wet_well_sizing_recommendations(wet_well_volume, required_volume)
    
    def add_full_flow_recommendations(self):
        """Add recommendations for achieving full flow in force mains"""
        self.recommendations.extend([
            {
                'priority': 1,
                'category': 'Hydraulic Design',
                'action': 'Add Break Node at Discharge',
                'description': 'Install a manhole or junction at force main outlet with surcharge capability',
                'implementation': 'Set surcharge depth = 1.5 × pipe diameter to maintain backpressure',
                'swmm_code': '''[JUNCTIONS]
BreakNode    105.0  3.0  0  1.5  0

[CONDUITS]  
FM_Outlet    BreakNode  Outfall  50  0.013  0  0  0  0''',
                'expected_result': 'Maintains full pipe flow by preventing free discharge'
            },
            {
                'priority': 2,
                'category': 'Hydraulic Design',
                'action': 'Install Air Release Valve',
                'description': 'Add automatic air release valves at high points',
                'implementation': 'Use combination air valves sized for 2× design flow',
                'swmm_code': '''[OUTLETS]
AirValve     HighPoint  Atmosphere  TABULAR/HEAD  AirCurve''',
                'expected_result': 'Prevents air accumulation and maintains full flow'
            },
            {
                'priority': 3,
                'category': 'System Modifications',
                'action': 'Increase Discharge Head',
                'description': 'Modify system to provide higher discharge head',
                'implementation': 'Raise pump curve, add booster pump, or reduce friction losses',
                'swmm_code': '''[CURVES]
NewPumpCurve  PUMP4  0.000  55.0
NewPumpCurve  PUMP4  0.100  52.0
NewPumpCurve  PUMP4  0.200  45.0''',
                'expected_result': 'Provides sufficient head to overcome system resistance'
            }
        ])
    
    def add_velocity_recommendations(self, velocity: float, diameter: float, condition: str):
        """Add recommendations based on velocity issues"""
        if condition == 'low':
            self.recommendations.extend([
                {
                    'priority': 1,
                    'category': 'Velocity Enhancement',
                    'action': 'Reduce Pipe Diameter',
                    'description': f'Consider smaller diameter to increase velocity from {velocity:.2f} m/s',
                    'implementation': f'Reduce from {diameter:.3f}m to {diameter*0.8:.3f}m diameter',
                    'swmm_code': f'''[XSECTIONS]
ForceMeain   FORCE_MAIN  {diameter*0.8:.3f}  0  0  0  1''',
                    'expected_result': f'Increase velocity to approximately {velocity/0.64:.2f} m/s'
                },
                {
                    'priority': 2,
                    'category': 'Operational',
                    'action': 'Increase Minimum Flow',
                    'description': 'Modify pump controls to maintain higher minimum flow',
                    'implementation': 'Adjust pump start/stop levels or add minimum flow bypass',
                    'swmm_code': '''[CONTROLS]
RULE MinFlow
IF PUMP P1 STATUS = OFF AND NODE WW1 DEPTH > 0.5
THEN PUMP P1 STATUS = ON''',
                    'expected_result': 'Maintains minimum velocity for solids transport'
                }
            ])
        
        elif condition == 'high':
            self.recommendations.extend([
                {
                    'priority': 1,
                    'category': 'Velocity Reduction',
                    'action': 'Increase Pipe Diameter',
                    'description': f'Increase diameter to reduce velocity from {velocity:.2f} m/s',
                    'implementation': f'Increase from {diameter:.3f}m to {diameter*1.2:.3f}m diameter',
                    'swmm_code': f'''[XSECTIONS]
ForceMeain   FORCE_MAIN  {diameter*1.2:.3f}  0  0  0  1''',
                    'expected_result': f'Reduce velocity to approximately {velocity/1.44:.2f} m/s'
                },
                {
                    'priority': 2,
                    'category': 'System Design',
                    'action': 'Install Parallel Force Main',
                    'description': 'Add parallel pipe to split flow and reduce velocities',
                    'implementation': 'Install second force main with flow splitting',
                    'swmm_code': '''[CONDUITS]
ForceMeain2  WetWell  Discharge  1000  0.013  0  0  0  0

[XSECTIONS]
ForceMeain2  FORCE_MAIN  {diameter:.3f}  0  0  0  1''',
                    'expected_result': 'Reduces velocity in each pipe by approximately 50%'
                }
            ])
    
    def add_negative_pressure_recommendations(self):
        """Add recommendations for negative pressure issues"""
        self.recommendations.extend([
            {
                'priority': 1,
                'category': 'Emergency Action',
                'action': 'Install Air Inlet Valves',
                'description': 'Immediately install air inlet valves to prevent pipe collapse',
                'implementation': 'Install at high points and locations with negative pressure',
                'swmm_code': '''[OUTLETS]
AirInlet     HighPoint  Atmosphere  TABULAR/HEAD  InletCurve''',
                'expected_result': 'Prevents pipe collapse and allows air entry during negative pressure'
            },
            {
                'priority': 2,
                'category': 'System Redesign',
                'action': 'Increase Pump Head',
                'description': 'Modify pump selection to provide higher discharge head',
                'implementation': 'Select pump with higher head curve or add booster pump',
                'swmm_code': '''[CURVES]
HighHeadPump  PUMP4  0.000  75.0
HighHeadPump  PUMP4  0.100  70.0
HighHeadPump  PUMP4  0.200  60.0''',
                'expected_result': 'Eliminates negative pressure throughout system'
            }
        ])
    
    def add_low_pressure_recommendations(self):
        """Add recommendations for low pressure issues"""
        self.recommendations.extend([
            {
                'priority': 1,
                'category': 'Pressure Enhancement',
                'action': 'Reduce System Losses',
                'description': 'Minimize friction losses in force main system',
                'implementation': 'Clean pipes, replace fittings, optimize routing',
                'swmm_code': '''[CONDUITS]
ForceMeain   WetWell  Discharge  1000  0.011  0  0  0  0  ; Reduced roughness''',
                'expected_result': 'Increases available pressure head'
            },
            {
                'priority': 2,
                'category': 'Monitoring',
                'action': 'Install Pressure Monitoring',
                'description': 'Add pressure sensors at critical points',
                'implementation': 'Monitor minimum pressure locations during operation',
                'swmm_code': '''# Add pressure monitoring points in SWMM model
# Monitor nodes with minimum pressure heads''',
                'expected_result': 'Early warning of cavitation conditions'
            }
        ])
    
    def add_pump_curve_recommendations(self, current_flow: float, min_flow: float, max_flow: float):
        """Add recommendations for pump curve issues"""
        self.recommendations.extend([
            {
                'priority': 1,
                'category': 'Pump Selection',
                'action': 'Optimize Pump Selection',
                'description': f'Current operation at {current_flow:.3f} m³/s outside optimal range',
                'implementation': f'Select pump with curve range {current_flow*0.8:.3f} - {current_flow*1.5:.3f} m³/s',
                'swmm_code': '''[CURVES]
OptimalPump  PUMP4  {:.3f}  50.0
OptimalPump  PUMP4  {:.3f}  45.0
OptimalPump  PUMP4  {:.3f}  35.0'''.format(current_flow*0.8, current_flow, current_flow*1.2),
                'expected_result': 'Improved efficiency and reduced operating costs'
            },
            {
                'priority': 2,
                'category': 'Variable Speed',
                'action': 'Consider Variable Speed Drive',
                'description': 'Install VFD to optimize pump operation across flow range',
                'implementation': 'VFD allows pump curve adjustment for varying conditions',
                'swmm_code': '''[CONTROLS]
RULE VFD_Control
IF NODE WetWell DEPTH > 2.5
THEN PUMP MainPump SETTING = 1.0
ELSE PUMP MainPump SETTING = 0.7''',
                'expected_result': 'Maintains optimal efficiency across operating range'
            }
        ])
    
    def add_npsh_recommendations(self, npsh_available: float, npsh_required: float):
        """Add recommendations for NPSH issues"""
        deficit = npsh_required - npsh_available
        
        self.recommendations.extend([
            {
                'priority': 1,
                'category': 'Suction Design',
                'action': 'Reduce Suction Losses',
                'description': f'Increase NPSH available by {deficit:.2f}m minimum',
                'implementation': 'Enlarge suction piping, reduce fittings, shorten suction line',
                'swmm_code': '''[CONDUITS]
SuctionLine  WetWell  Pump  10  0.009  0  0  0  0  ; Larger, smoother pipe''',
                'expected_result': f'Increases NPSH available by reducing suction losses'
            },
            {
                'priority': 2,
                'category': 'Pump Modification',
                'action': 'Lower Pump Position',
                'description': 'Reduce pump elevation to increase suction head',
                'implementation': 'Lower pump installation to increase static suction head',
                'swmm_code': '''[JUNCTIONS]
PumpNode  {:.1f}  2.0  0  0  0  ; Lowered pump elevation'''.format(95.0 - deficit),
                'expected_result': 'Increases NPSH available through higher suction pressure'
            }
        ])
    
    def add_wet_well_sizing_recommendations(self, current_volume: float, required_volume: float):
        """Add recommendations for wet well sizing issues"""
        self.recommendations.extend([
            {
                'priority': 1,
                'category': 'Wet Well Design',
                'action': 'Increase Storage Volume',
                'description': f'Increase storage from {current_volume:.1f}m³ to {required_volume:.1f}m³',
                'implementation': 'Deepen wet well or increase surface area',
                'swmm_code': f'''[STORAGE]
WetWell  95.0  {required_volume/50:.1f}  1.0  FUNCTIONAL  50.0  0  0  0''',
                'expected_result': 'Reduces pump cycling frequency to acceptable levels'
            },
            {
                'priority': 2,
                'category': 'Control Strategy',
                'action': 'Adjust Pump Controls',
                'description': 'Optimize start/stop levels to maximize effective volume',
                'implementation': 'Increase differential between start and stop levels',
                'swmm_code': '''[CONTROLS]
RULE PumpStart
IF NODE WetWell DEPTH > 2.5
THEN PUMP MainPump STATUS = ON

RULE PumpStop  
IF NODE WetWell DEPTH < 0.5
THEN PUMP MainPump STATUS = OFF''',
                'expected_result': 'Maximizes effective storage volume for pump cycling'
            }
        ])
    
    def generate_diagnostic_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive diagnostic report
        
        Returns:
        Dictionary containing complete diagnostic results
        """
        # Sort issues by priority and severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        sorted_issues = sorted(self.issues, 
                             key=lambda x: (severity_order.get(x['severity'], 4), x['priority']))
        
        # Sort recommendations by priority
        sorted_recommendations = sorted(self.recommendations, key=lambda x: x['priority'])
        
        # Generate summary statistics
        issue_counts = {}
        for issue in self.issues:
            severity = issue['severity']
            issue_counts[severity] = issue_counts.get(severity, 0) + 1
        
        category_counts = {}
        for issue in self.issues:
            category = issue['category']
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Determine overall system status
        if any(issue['severity'] == 'CRITICAL' for issue in self.issues):
            overall_status = 'CRITICAL'
            status_message = 'Immediate attention required - system has critical issues'
        elif any(issue['severity'] == 'HIGH' for issue in self.issues):
            overall_status = 'WARNING'
            status_message = 'High priority issues detected - schedule repairs soon'
        elif any(issue['severity'] == 'MEDIUM' for issue in self.issues):
            overall_status = 'CAUTION'
            status_message = 'Medium priority issues - monitor and plan improvements'
        else:
            overall_status = 'GOOD'
            status_message = 'System operating within acceptable parameters'
        
        return {
            'overall_status': overall_status,
            'status_message': status_message,
            'summary': {
                'total_issues': len(self.issues),
                'total_recommendations': len(self.recommendations),
                'issue_counts': issue_counts,
                'category_counts': category_counts
            },
            'issues': sorted_issues,
            'recommendations': sorted_recommendations,
            'generated_at': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def validate_swmm_model_setup(self, nodes: Dict, links: Dict, pumps: Dict) -> Dict[str, Any]:
        """
        Validate SWMM model setup for common configuration errors
        
        Parameters:
        nodes: Dictionary of node configurations
        links: Dictionary of link configurations
        pumps: Dictionary of pump configurations
        
        Returns:
        Dictionary with validation results
        """
        self.reset_diagnostics()
        
        # Check for required components
        wet_wells = [n for n, data in nodes.items() if data.get('type') == 'wet_well']
        outfalls = [n for n, data in nodes.items() if data.get('type') == 'outfall']
        force_mains = [l for l, data in links.items() if data.get('type') == 'force_main']
        
        if not wet_wells:
            self.issues.append({
                'severity': 'CRITICAL',
                'category': 'Model Setup',
                'issue': 'No wet well defined in model',
                'details': 'Force main systems require at least one wet well',
                'location': 'model',
                'priority': 1
            })
        
        if not outfalls:
            self.issues.append({
                'severity': 'HIGH',
                'category': 'Model Setup',
                'issue': 'No outfall defined in model',
                'details': 'Model needs boundary condition for discharge',
                'location': 'model',
                'priority': 1
            })
        
        if not force_mains:
            self.issues.append({
                'severity': 'HIGH',
                'category': 'Model Setup',
                'issue': 'No force mains defined',
                'details': 'Model should include pressurized conduits',
                'location': 'model',
                'priority': 1
            })
        
        if not pumps:
            self.issues.append({
                'severity': 'HIGH',
                'category': 'Model Setup',
                'issue': 'No pumps defined in model',
                'details': 'Force main systems require pumps for operation',
                'location': 'model',
                'priority': 1
            })
        
        # Check connectivity
        connected_nodes = set()
        for link_data in links.values():
            connected_nodes.add(link_data.get('from'))
            connected_nodes.add(link_data.get('to'))
        for pump_data in pumps.values():
            connected_nodes.add(pump_data.get('from'))
            connected_nodes.add(pump_data.get('to'))
        
        for node_id in nodes.keys():
            if node_id not in connected_nodes:
                self.issues.append({
                    'severity': 'MEDIUM',
                    'category': 'Connectivity',
                    'issue': f'Node {node_id} is not connected',
                    'details': 'Isolated nodes may cause convergence issues',
                    'location': node_id,
                    'priority': 2
                })
        
        return self.generate_diagnostic_report()
