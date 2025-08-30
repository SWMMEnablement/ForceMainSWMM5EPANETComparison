import numpy as np
import scipy.optimize as opt
from scipy.special import lambertw

class ForceMainCalculator:
    """
    Calculate hydraulic parameters for force mains using various methods
    """
    
    def __init__(self):
        self.gravity = 9.81  # m/s^2
        self.water_density = 998.2  # kg/m^3 at 20°C
        self.kinematic_viscosity = 1.004e-6  # m^2/s at 20°C
        self.dynamic_viscosity = 1.002e-3  # Pa·s at 20°C
    
    def hazen_williams_loss(self, Q, D, L, C):
        """
        Calculate head loss using Hazen-Williams equation
        
        Parameters:
        Q: Flow rate (m³/s)
        D: Pipe diameter (m)
        L: Pipe length (m)
        C: Hazen-Williams coefficient (dimensionless)
        
        Returns:
        hf: Friction head loss (m)
        """
        # For SI units - corrected formula
        hf = 10.67 * (Q**1.852) * L / (C**1.852 * D**4.87)
        return hf
    
    def darcy_weisbach_loss(self, Q, D, L, e):
        """
        Calculate head loss using Darcy-Weisbach equation
        
        Parameters:
        Q: Flow rate (m³/s)
        D: Pipe diameter (m)
        L: Pipe length (m)
        e: Absolute roughness (m)
        
        Returns:
        hf: Friction head loss (m)
        """
        A = np.pi * D**2 / 4
        V = Q / A
        Re = V * D / self.kinematic_viscosity
        
        # Swamee-Jain approximation for friction factor
        if Re > 4000:  # Turbulent flow
            f = 0.25 / (np.log10(e/(3.7*D) + 5.74/Re**0.9))**2
        else:  # Laminar flow
            f = 64 / Re
        
        hf = f * L * V**2 / (D * 2 * self.gravity)
        return hf
    
    def colebrook_white_friction(self, Re, e_D):
        """
        Solve Colebrook-White equation for friction factor
        
        Parameters:
        Re: Reynolds number
        e_D: Relative roughness (e/D)
        
        Returns:
        f: Friction factor
        """
        def colebrook_eq(f):
            return 1/np.sqrt(f) + 2*np.log10(e_D/3.7 + 2.51/(Re*np.sqrt(f)))
        
        # Initial guess using Swamee-Jain
        f_init = 0.25 / (np.log10(e_D/3.7 + 5.74/Re**0.9))**2
        
        try:
            f_solution = opt.fsolve(colebrook_eq, f_init)[0]
            return f_solution
        except:
            # Fallback to Swamee-Jain
            return f_init
    
    def manning_to_hazen_williams(self, n, D, S):
        """
        Convert Manning's n to Hazen-Williams C
        
        Parameters:
        n: Manning's roughness coefficient
        D: Pipe diameter (m)
        S: Slope (m/m)
        
        Returns:
        C: Hazen-Williams coefficient
        """
        # Empirical conversion formula
        C = 1.067 / (n * (D / S)**0.04)
        return max(C, 80)  # Minimum realistic value
    
    def check_full_flow_condition(self, pump_head, static_head, friction_loss):
        """
        Verify if force main will flow full
        
        Parameters:
        pump_head: Available pump head (m)
        static_head: Static elevation difference (m)
        friction_loss: Total friction loss (m)
        
        Returns:
        tuple: (is_full_flow, head_surplus)
        """
        available_head = pump_head - static_head
        surplus = available_head - friction_loss
        
        return surplus > 0, surplus
    
    def calculate_velocity(self, Q, D):
        """
        Calculate flow velocity
        
        Parameters:
        Q: Flow rate (m³/s)
        D: Pipe diameter (m)
        
        Returns:
        V: Velocity (m/s)
        """
        A = np.pi * D**2 / 4
        return Q / A
    
    def calculate_reynolds_number(self, V, D):
        """
        Calculate Reynolds number
        
        Parameters:
        V: Velocity (m/s)
        D: Pipe diameter (m)
        
        Returns:
        Re: Reynolds number
        """
        return V * D / self.kinematic_viscosity
    
    def minimum_transport_velocity(self, D):
        """
        Calculate minimum velocity to prevent solids settling
        Based on empirical formulas for wastewater
        
        Parameters:
        D: Pipe diameter (m)
        
        Returns:
        V_min: Minimum transport velocity (m/s)
        """
        # Simplified formula for wastewater force mains
        # V_min = 0.5 to 0.6 m/s for most applications
        return max(0.6, 0.8 * np.sqrt(D))  # Conservative approach
    
    def air_valve_sizing(self, Q, D, L, elevation_profile):
        """
        Size air release valves for force main
        
        Parameters:
        Q: Design flow rate (m³/s)
        D: Pipe diameter (m)
        L: Pipe length (m)
        elevation_profile: List of elevations along pipe
        
        Returns:
        dict: Air valve sizing recommendations
        """
        # Find high points
        high_points = []
        elevations = np.array(elevation_profile)
        
        for i in range(1, len(elevations)-1):
            if elevations[i] > elevations[i-1] and elevations[i] > elevations[i+1]:
                high_points.append(i)
        
        # Air release valve sizing (simplified)
        air_flow_rate = Q * 0.001  # 0.1% of water flow as air
        valve_size = np.sqrt(air_flow_rate * 4 / np.pi) * 1000  # mm
        
        return {
            'high_points': len(high_points),
            'recommended_valve_size_mm': max(valve_size, 25),  # Minimum 25mm
            'valve_locations': high_points
        }
    
    def water_hammer_analysis(self, Q, D, L, c, valve_closure_time):
        """
        Simplified water hammer analysis
        
        Parameters:
        Q: Flow rate (m³/s)
        D: Pipe diameter (m)
        L: Pipe length (m)
        c: Wave speed (m/s) - typically 1000-1400 m/s
        valve_closure_time: Time to close valve (s)
        
        Returns:
        dict: Water hammer analysis results
        """
        V = self.calculate_velocity(Q, D)
        
        # Critical time (2L/c)
        tc = 2 * L / c
        
        if valve_closure_time < tc:
            # Rapid closure - Joukowsky formula
            dH = c * V / self.gravity
        else:
            # Slow closure
            dH = (c * V / self.gravity) * (tc / valve_closure_time)
        
        return {
            'critical_time_s': tc,
            'pressure_rise_m': dH,
            'is_rapid_closure': valve_closure_time < tc,
            'recommendation': 'Install surge protection' if dH > 50 else 'Acceptable'
        }
    
    def npsh_calculation(self, suction_pressure, vapor_pressure, velocity_head, suction_loss):
        """
        Calculate Net Positive Suction Head Available
        
        Parameters:
        suction_pressure: Absolute pressure at suction (m)
        vapor_pressure: Vapor pressure of liquid (m)
        velocity_head: Velocity head at suction (m)
        suction_loss: Losses in suction line (m)
        
        Returns:
        NPSHA: Net Positive Suction Head Available (m)
        """
        NPSHA = suction_pressure - vapor_pressure - velocity_head - suction_loss
        return NPSHA
    
    def equivalent_length_fittings(self, fittings_dict, D):
        """
        Calculate equivalent length of fittings
        
        Parameters:
        fittings_dict: Dictionary of fittings {'elbow_90': 2, 'valve_gate': 1, ...}
        D: Pipe diameter (m)
        
        Returns:
        Le: Equivalent length (m)
        """
        # K values for common fittings
        k_values = {
            'elbow_90': 30,
            'elbow_45': 16,
            'tee_branch': 60,
            'tee_through': 20,
            'valve_gate': 8,
            'valve_globe': 340,
            'valve_ball': 3,
            'entrance_sharp': 0.5,
            'entrance_rounded': 0.04,
            'exit': 1.0
        }
        
        total_k = 0
        for fitting, count in fittings_dict.items():
            if fitting in k_values:
                total_k += k_values[fitting] * count
        
        # Convert K to equivalent length
        Le = total_k * D
        return Le
    
    def pump_affinity_laws(self, Q1, H1, N1, N2):
        """
        Apply pump affinity laws for speed changes
        
        Parameters:
        Q1, H1: Original flow and head
        N1, N2: Original and new speeds (rpm)
        
        Returns:
        tuple: (Q2, H2, P2_ratio) - new flow, head, and power ratio
        """
        speed_ratio = N2 / N1
        
        Q2 = Q1 * speed_ratio
        H2 = H1 * speed_ratio**2
        P2_ratio = speed_ratio**3  # Power ratio
        
        return Q2, H2, P2_ratio
