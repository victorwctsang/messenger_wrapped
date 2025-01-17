from typing import Dict
import streamlit as st
import altair as alt
import pandas as pd
from analysis.analysis import ChatStats, MessengerAnalyzer
from utils.data_loader import MessengerDataLoader
import math
from dotenv import load_dotenv
import os

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    # Set page config
    st.set_page_config(
        page_title="Your Chat Wrapped 2024",
        page_icon="💬"
    )

    # Custom CSS for animations and styling
    st.markdown("""
        <style>
        .big-number {
            font-size: 72px;
            font-weight: bold;
            text-align: center;
        }
        .stat-label {
            font-size: 24px;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    if 'loader' not in st.session_state:
        st.session_state.loader = None
    if 'messages' not in st.session_state:
        st.session_state.messages = None
    if 'chat_stats' not in st.session_state:
        st.session_state.chat_stats = None
    if 'current_chat' not in st.session_state:
        st.session_state.current_chat = None
    if 'data_dir' not in st.session_state:
        st.session_state.data_dir = None

def load_data(data_dir: str):
    """Load data and update session state."""
    if (st.session_state.loader is None or 
        st.session_state.data_dir != data_dir):
        
        st.session_state.loader = MessengerDataLoader(data_dir)
        st.session_state.data_dir = data_dir

def process_chat(chat_title: str):
    """Process selected chat and update session state."""
    if (st.session_state.current_chat != chat_title or 
        st.session_state.messages is None):
        
        st.session_state.messages = st.session_state.loader.process_chat_folder(
            chat_title, 
            remove_reactions=True
        )
        st.session_state.current_chat = chat_title
        
        # Perform analysis
        analyser = MessengerAnalyzer(st.session_state.messages)
        st.session_state.chat_stats = analyser.analyze()

def create_wrapped_presentation(chat_stats: ChatStats):

    # Introduction
    st.title("Your Chat Wrapped 2024 🎁")

    show_total_messages(chat_stats.num_messages)
    show_average_messages_per_day(chat_stats.avg_messages_per_day)
    show_top_chatters(chat_stats.person_stats)
    show_most_used_words(chat_stats.word_counts)
    st.markdown("---")
    st.subheader("Reaction Champions 🏆")
    with st.spinner():
        col1, col2 = st.columns(2)

        with col1:
            show_most_received_reactions(chat_stats.received_reaction_stats)
        with col2:
            show_most_sent_reactions(chat_stats.sent_reaction_stats)
    show_messages_per_day(chat_stats.messages_by_user_by_day)
    show_messages_per_hour(chat_stats.hourly_stats)

    # Final Message
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; padding: 50px;'>
            <h2>Thanks for being part of the conversation! 🎉</h2>
            <p>Here's to many more messages in the coming year! 🚀</p>
        </div>
    """, unsafe_allow_html=True)

    return None

def show_total_messages(num_messages: int):
    # Total Messages
    st.markdown("<div class='stat-label'>This year, you exchanged</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='big-number'>{num_messages:,}</div>", unsafe_allow_html=True)
    st.markdown("<div class='stat-label'>messages</div>", unsafe_allow_html=True)
    return None

def show_average_messages_per_day(avg_messages_per_day: int):
    # Average Messages Per Day
    st.markdown("---")
    st.markdown("<div class='stat-label'>That's an average of</div>", unsafe_allow_html=True)
    with st.spinner():
        st.markdown(f"<div class='big-number'>{avg_messages_per_day}</div>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>messages per day!</div>", unsafe_allow_html=True)    
    return None

def show_top_chatters(person_stats: pd.DataFrame):
    # Top Chatters
    st.markdown("---")
    st.subheader("Messages Sent by Person 👑")
    
    with st.spinner():
        chart = alt.Chart(person_stats).mark_bar(color='#1DB954').encode(
            x=alt.X('messages_sent:Q', title='Messages Sent'),
            y=alt.Y('sender_name:N', sort='-x', title=''),
            tooltip=['sender_name', 'messages_sent']
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
    return None

def show_most_used_words(word_counts: Dict):
    # Most Used Words
    st.markdown("---")
    st.subheader("Your Most Used Words 💭")
    with st.spinner():
        # Convert word counts to DataFrame and get top 10
        word_df = pd.DataFrame.from_dict(word_counts, orient='index', columns=['count'])
        word_df = word_df.nlargest(10, 'count')
        word_df.index.name = 'word'
        word_df = word_df.reset_index()

        word_cloud = alt.Chart(word_df).mark_bar(color='#1DB954').encode(
            x=alt.X('count:Q', title='Times Used'),
            y=alt.Y('word:N', sort='-x', title=''),
            tooltip=['word', 'count']
        ).properties(height=400)
        st.altair_chart(word_cloud, use_container_width=True)
    return None

def show_most_received_reactions(received_reaction_stats: pd.DataFrame):
    st.markdown("### Most Reactions Received")
    reaction_stats_top5_melted = received_reaction_stats.iloc[1:,:-1].head().reset_index().melt(id_vars=['emoji'])
    received_chart = alt.Chart(reaction_stats_top5_melted).mark_bar(color='#1DB954').encode(
        x=alt.X('value:Q', title='Reactions Received'),
        y=alt.Y('recipient:N', sort='-x', title=''),
        tooltip=['recipient', 'value']
    ).properties(height=400)
    st.altair_chart(received_chart, use_container_width=True)
    return None

def show_most_sent_reactions(sent_reaction_stats: pd.DataFrame):
    st.markdown("### Most Reactions Given")
    sent_stats_top5_melted = sent_reaction_stats.iloc[1:,:-1].head().reset_index().melt(id_vars=['emoji'])
    sent_chart = alt.Chart(sent_stats_top5_melted).mark_bar(color='#1DB954').encode(
        x=alt.X('value:Q', title='Reactions Given'),
        y=alt.Y('reactor:N', sort='-x', title=''),
        tooltip=['reactor', 'value']
    ).properties(height=400)
    st.altair_chart(sent_chart, use_container_width=True)
    return None

def show_messages_per_day(messages_by_user_by_day: pd.DataFrame):
    # Activity Over Time
    st.markdown("---")
    st.subheader("Your Chat Activity Throughout the Year 📅")
    with st.spinner():
        messages_by_user_by_day_melted = messages_by_user_by_day.reset_index().melt(id_vars=['date'])
        timeline = alt.Chart(messages_by_user_by_day_melted).mark_line(
            interpolate='monotone',
            opacity=0.5
        ).encode(
            x=alt.X('date:T', title='Date'),
            y=alt.Y('value:Q', title='Number of Messages'),
            color='sender_name',
            tooltip=['date', 'sender_name', 'value']
        ).properties(height=300)
        st.altair_chart(timeline, use_container_width=True)
    return None

def show_messages_per_hour(hourly_stats: pd.DataFrame):
    # Most Active Hours Visualization
    st.markdown("---")
    st.subheader("Your Peak Chatting Hours 🕒")
    with st.spinner():
        max_messages = hourly_stats['All'].max()
        # Round up to nearest 100 for axis rings
        max_ring = math.ceil(max_messages / 100) * 100
        ring_step = max(max_ring // 5, 100)  # Ensure we don't have too many rings
        
        # Create the circular axis rings
        axis_rings = alt.Chart(
            pd.DataFrame({"ring": range(ring_step, max_ring + ring_step, ring_step)})
        ).mark_arc(stroke='lightgrey', fill=None).encode(
            theta=alt.value(2 * math.pi),
            radius=alt.Radius('ring').stack(False)
        )
        
        # Labels for the rings
        axis_rings_labels = axis_rings.mark_text(
            color='grey', 
            radiusOffset=5, 
            align='left'
        ).encode(
            text="ring",
            theta=alt.value(math.pi / 4)
        )
        
        # Time axis lines
        axis_lines = alt.Chart(pd.DataFrame({
            "radius": max_ring,
            "theta": math.pi / 2,
            'hour': ['00:00', '06:00', '12:00', '18:00']
        })).mark_arc(stroke='lightgrey', fill=None).encode(
            theta=alt.Theta('theta').stack(True),
            radius=alt.Radius('radius'),
            radius2=alt.datum(1),
        )
        
        # Labels for time axis
        axis_lines_labels = axis_lines.mark_text(
            color='grey',
            radiusOffset=5,
            thetaOffset=-math.pi / 4,
            align=alt.expr('datum.hour == "18:00" ? "right" : datum.hour == "06:00" ? "left" : "center"'),
            baseline=alt.expr('datum.hour == "00:00" ? "bottom" : datum.hour == "12:00" ? "top" : "middle"'),
        ).encode(text="hour")
        
        # Main polar bars
        polar_bars = alt.Chart(hourly_stats).mark_arc(
            stroke='white',
            tooltip=True,
            fill='#1DB954'
        ).encode(
            theta=alt.Theta("hour:O"),
            radius=alt.Radius('All').scale(type='linear'),
            radius2=alt.datum(1),
            tooltip=['hour', 'All']
        )
        
        # Combine all layers
        hourly_chart = alt.layer(
            axis_rings,
            polar_bars,
            axis_rings_labels,
            axis_lines,
            axis_lines_labels,
            title=['Message Activity Throughout the Day', '']
        ).properties(
            width=400,
            height=400
        )
        
        st.altair_chart(hourly_chart, use_container_width=True)
        return None

def main():
    # Load environment variables from the .env file (if present)
    load_dotenv()

    # Access environment variables as if they came from the actual environment
    DEFAULT_MESSAGE_DIRECTORY = os.getenv('DEFAULT_MESSAGE_DIRECTORY')

    # Initialize session state
    initialize_session_state()
    
    # Input for data directory
    message_dir = st.text_input(
        label="Path to all messages",
        key="message_dir_input",
        value=DEFAULT_MESSAGE_DIRECTORY
    )

    if message_dir and message_dir != "Example: '/home/username/data/'":
        try:
            # Load data if needed
            load_data(message_dir)
            
            st.write(f"{len(st.session_state.loader.chat_names):,} chats loaded!")
            # Dropdown based on chat_names
            chat_title = st.selectbox(
                label="Which chat do you want to analyse?",
                options=st.session_state.loader.chat_names,
                key="chat_selector"
            )

            if chat_title:
                # Process chat if needed
                process_chat(chat_title)
                
                # Create visualization
                if st.session_state.chat_stats is not None:
                    create_wrapped_presentation(st.session_state.chat_stats)
                    
        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()