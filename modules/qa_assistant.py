import os
from openai import OpenAI

class QAAssistant:
    """AI-powered Q&A assistant for SWMM5 and EPANET questions"""
    
    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
        # do not change this unless explicitly requested by the user
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-5"
        
        # Context about the app and its capabilities
        self.system_context = """You are an expert assistant for the SWMM5 Force Mains Modeling App. 
You help users with questions about:

1. **SWMM5 (Storm Water Management Model):**
   - Force main modeling with FORCE_MAIN cross-sections
   - Dynamic/unsteady flow analysis
   - Wet well and storage node modeling
   - Pump controls and curves
   - DYNWAVE routing method
   - Surcharge depth requirements (minimum 100 for force main nodes)
   - Hazen-Williams C coefficients for force mains (typically 120)
   - Time-dependent simulations and real-time controls

2. **EPANET:**
   - Steady-state pressure network analysis
   - Water distribution system modeling
   - Tank and reservoir modeling
   - Pump curves and optimization
   - Hazen-Williams and Darcy-Weisbach equations
   - Network hydraulics and pressure analysis

3. **This App's Features:**
   - **Force Main Designer**: Interactive tool for sizing force mains with real-time hydraulic analysis
   - **Friction Loss Calculator**: Compare Hazen-Williams vs Darcy-Weisbach methods
   - **Network Analyzer**: Analyze complex force main networks with Hardy Cross method
   - **SWMM Input Generator**: Generate properly formatted SWMM5 input files
   - **EPANET Input Generator**: Generate EPANET input files for force main systems
   - **Results Visualizer**: Create hydraulic grade line profiles and pressure plots
   - **EPANET vs SWMM5 Comparison**: Decision matrix and feature comparison
   - **Troubleshooting Assistant**: Diagnose common force main issues
   - **Source Code Explorer**: View app architecture and implementation

**Key Technical Details:**
- SWMM5 requires surcharge depth ≥ 100 for force main nodes
- FORCE_MAIN XSECTIONS use Hazen-Williams C coefficient (Geom2), not Manning's n
- Typical HW C value for force mains is 120
- Force mains should operate under full pressure conditions
- Recommended velocity range: 0.6-3.0 m/s
- The app uses both Hazen-Williams and Darcy-Weisbach equations
- Network analysis uses Hardy Cross method with Newton-Raphson iteration

## SOURCE CODE REFERENCE

**Module: calculator.py** - ForceMainCalculator class
- hazen_williams_loss(Q, D, L, C): hf = 10.67 * Q^1.852 * L / (C^1.852 * D^4.87)
- darcy_weisbach_loss(Q, D, L, e): Uses Swamee-Jain friction factor
- calculate_velocity(Q, D), calculate_reynolds_number(V, D)
- Properties: gravity=9.81, kinematic_viscosity=1.004e-6

**Module: network.py** - ForceMainNetwork class (Hardy Cross/Newton-Raphson)
- add_wet_well, add_junction, add_outfall, add_force_main, add_pump
- solve_network(): Returns (converged, iterations, results)
- Tolerance=0.001, max_iterations=100

**Module: swmm_writer.py** - SWMMInputGenerator
- create_force_main_system(config): Generates complete SWMM5 .inp file
- CRITICAL: XSECTIONS Geom2 uses HW C (auto-converts if roughness < 1 to 120)
- CRITICAL: Surcharge depth minimum 100 for force main nodes
- OPTIONS: DYNWAVE routing, H-W equation, SLOT surcharge method

**Module: epanet_writer.py** - EPANETInputGenerator  
- create_force_main_system(config): Wet well as TANK, force main as PIPE
- Minor losses: entrance 0.5 + exit 1.0 = 1.5
- OPTIONS: H-W headloss, SI units, 40 trials

**Module: validator.py** - ModelConsistencyChecker & TroubleshootingAssistant
- check_physical_parameters, check_pump_curves, check_boundary_conditions
- check_force_main_full_flow(d/D ≥ 0.95), check_velocity_range(0.6-3.0 m/s)
- check_pressure_adequacy(> 3.0 m), check_pump_operating_point

**Module: visualizer.py** - HydraulicVisualizer
- plot_hydraulic_profile, plot_pump_system_curves, plot_velocity_profile
- plot_pressure_analysis, plot_network_schematic
- Uses Plotly for interactive visualizations

Provide clear, accurate answers. Reference specific classes, methods, and code when asked about implementation. 
If asked how code works, explain from the actual source. Guide users to appropriate tools."""

    def ask_question(self, question: str, conversation_history: list | None = None) -> str:
        """
        Ask a question and get an AI-generated response
        
        Args:
            question: User's question
            conversation_history: Optional list of previous messages for context
            
        Returns:
            AI-generated response text
        """
        try:
            # Build messages array
            messages = [{"role": "system", "content": self.system_context}]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current question
            messages.append({"role": "user", "content": question})
            
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=2048,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "insufficient_quota" in error_msg.lower():
                return "⚠️ **OpenAI API Quota Exceeded**\n\nThe AI Assistant has reached its usage limit. This happens when:\n- Your OpenAI account has insufficient credits\n- You've exceeded your plan's rate limits\n\n**To resolve this:**\n1. Check your OpenAI account billing at https://platform.openai.com/account/billing\n2. Add credits or upgrade your plan\n3. Wait a few minutes if you've hit rate limits\n\nIn the meantime, you can still use all other features of this app!"
            else:
                return f"Sorry, I encountered an error: {error_msg}"
    
    def ask_question_stream(self, question: str, conversation_history: list | None = None):
        """
        Ask a question and get a streaming response
        
        Args:
            question: User's question
            conversation_history: Optional list of previous messages for context
            
        Yields:
            Chunks of AI-generated response text
        """
        try:
            # Build messages array
            messages = [{"role": "system", "content": self.system_context}]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current question
            messages.append({"role": "user", "content": question})
            
            # Get streaming response from OpenAI
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=2048,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "insufficient_quota" in error_msg.lower():
                yield "⚠️ **OpenAI API Quota Exceeded**\n\nThe AI Assistant has reached its usage limit. This happens when:\n- Your OpenAI account has insufficient credits\n- You've exceeded your plan's rate limits\n\n**To resolve this:**\n1. Check your OpenAI account billing at https://platform.openai.com/account/billing\n2. Add credits or upgrade your plan\n3. Wait a few minutes if you've hit rate limits\n\nIn the meantime, you can still use all other features of this app!"
            else:
                yield f"Sorry, I encountered an error: {error_msg}"
