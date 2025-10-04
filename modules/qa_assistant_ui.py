import streamlit as st
from modules.qa_assistant import QAAssistant

def ai_assistant():
    """AI Assistant page for Q&A about SWMM5, EPANET, and the app"""
    st.header("🤖 AI Assistant")
    st.markdown("Ask questions about SWMM5, EPANET, and how to use this app")
    
    # Initialize QA Assistant
    try:
        if 'qa_assistant' not in st.session_state:
            st.session_state.qa_assistant = QAAssistant()
        
        assistant = st.session_state.qa_assistant
        
    except ValueError as e:
        st.error("❌ OpenAI API key not configured. Please contact the administrator.")
        st.info("💡 The AI Assistant requires an OpenAI API key to function.")
        return
    except Exception as e:
        st.error(f"❌ Error initializing AI Assistant: {str(e)}")
        return
    
    # Initialize conversation history in session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    # Quick action buttons
    st.markdown("### 💡 Quick Questions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📚 SWMM5 Best Practices", use_container_width=True):
            st.session_state.quick_question = "What are the best practices for modeling force mains in SWMM5?"
    
    with col2:
        if st.button("⚖️ SWMM5 vs EPANET", use_container_width=True):
            st.session_state.quick_question = "When should I use SWMM5 vs EPANET for force main modeling?"
    
    with col3:
        if st.button("🔧 How to Use This App", use_container_width=True):
            st.session_state.quick_question = "How do I generate a SWMM5 input file using this app?"
    
    # Display conversation history
    st.markdown("### 💬 Conversation")
    
    # Container for chat history
    chat_container = st.container()
    
    with chat_container:
        for msg in st.session_state.conversation_history:
            if msg["role"] == "user":
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
                    padding: 0.75rem;
                    border-radius: 10px;
                    margin: 0.5rem 0;
                    border-left: 4px solid #667eea;
                ">
                    <strong>You:</strong> {msg["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                    padding: 0.75rem;
                    border-radius: 10px;
                    margin: 0.5rem 0;
                    border-left: 4px solid #10b981;
                ">
                    <strong>🤖 AI Assistant:</strong><br>{msg["content"]}
                </div>
                """, unsafe_allow_html=True)
    
    # Question input
    st.markdown("### ❓ Ask a Question")
    
    # Check if there's a quick question
    default_question = ""
    if 'quick_question' in st.session_state:
        default_question = st.session_state.quick_question
        del st.session_state.quick_question
    
    # Text input for question
    question = st.text_area(
        "Your question:",
        value=default_question,
        placeholder="Example: What are the key differences between SWMM5 and EPANET for modeling force mains?",
        height=100,
        key="question_input"
    )
    
    col_ask, col_clear = st.columns([3, 1])
    
    with col_ask:
        ask_button = st.button("🚀 Ask Question", type="primary", use_container_width=True)
    
    with col_clear:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.conversation_history = []
            st.rerun()
    
    # Process question
    if ask_button and question.strip():
        # Add user question to history
        st.session_state.conversation_history.append({
            "role": "user",
            "content": question
        })
        
        # Show thinking indicator
        with st.spinner("🤔 Thinking..."):
            try:
                # Get response from AI
                response = assistant.ask_question(
                    question,
                    conversation_history=st.session_state.conversation_history[:-1]
                )
                
                # Add AI response to history
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })
                
                # Rerun to display new messages
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error getting response: {str(e)}")
    
    elif ask_button and not question.strip():
        st.warning("⚠️ Please enter a question first.")
    
    # Help section
    with st.expander("ℹ️ How to Use the AI Assistant", expanded=False):
        st.markdown("""
        **What can I ask?**
        - Questions about SWMM5 modeling concepts and best practices
        - Questions about EPANET modeling and analysis
        - How to use specific features in this app
        - Comparisons between SWMM5 and EPANET
        - Troubleshooting force main modeling issues
        
        **Tips for better answers:**
        - Be specific in your questions
        - Include relevant details (e.g., pipe diameter, flow rate)
        - Ask one question at a time for clarity
        - Use the quick question buttons for common topics
        
        **Examples:**
        - "What surcharge depth should I use for force main nodes in SWMM5?"
        - "How do I calculate friction loss using the Hazen-Williams equation?"
        - "What's the difference between dynamic and steady-state analysis?"
        - "How do I use the Network Analyzer tool to model multiple pumps?"
        """)
