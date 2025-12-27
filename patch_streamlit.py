import re

# Read the file
with open('streamlit_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the sidebar section to add consumer restart
old_section = '''        
        st.markdown("---")
        
        # Auto-refresh toggle'''

new_section = '''        
        st.markdown("---")
        st.header("Data Consumer")
        
        # Show consumer status
        if st.session_state.consumer_running:
            st.success("Consumer: RUNNING")
            if hasattr(st.session_state, 'consumer_instance'):
                msg_count = st.session_state.consumer_instance.message_count
                st.metric("Messages Received", msg_count)
        else:
            st.warning("Consumer: NOT RUNNING")
        
        # Restart consumer button
        if st.button("Restart Consumer", help="Restart to read ALL messages from Kafka"):
            if hasattr(st.session_state, 'consumer_instance') and st.session_state.consumer_instance:
                st.session_state.consumer_instance.stop()
            st.session_state.consumer_running = False
            st.session_state.response_stream.clear()
            st.session_state.metrics_data.clear()
            st.info("Restarting consumer...")
            time.sleep(1)
            st.rerun()
        
        st.markdown("---")
        
        # Auto-refresh toggle'''

# Replace
content = content.replace(old_section, new_section)

# Write back
with open('streamlit_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("File updated successfully!")
