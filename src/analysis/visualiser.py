# messenger_analysis/visualizer.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict
import numpy as np

class MessengerVisualizer:
    def __init__(self, chat_stats):
        """
        Initialize visualizer with ChatStats object.
        
        Args:
            chat_stats: ChatStats object containing analyzed message data
        """
        self.stats = chat_stats
        self._setup_style()
    
    def _setup_style(self):
        """Set up the plotting style."""
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (10, 6)
    
    def plot_message_distribution(self) -> plt.Figure:
        """Create bar plot of messages per sender."""
        fig, ax = plt.subplots()
        sns.barplot(
            x=self.stats.message_ranks.values,
            y=self.stats.message_ranks.index,
            ax=ax
        )
        ax.set_title("Messages Sent by User")
        ax.set_xlabel("Number of Messages")
        return fig
    
    def plot_word_clouds(self) -> Dict[str, plt.Figure]:
        """Create word clouds for overall chat and per user."""
        # Implementation depends on wordcloud package
        pass
    
    def plot_activity_heatmap(self) -> plt.Figure:
        """Create heatmap of activity by hour and day of week."""
        fig, ax = plt.subplots()
        sns.heatmap(
            self.stats.hourly_patterns,
            cmap="YlOrRd",
            ax=ax
        )
        ax.set_title("Message Activity Heatmap")
        return fig
    
    def plot_reaction_network(self) -> plt.Figure:
        """Create network graph of reactions between users."""
        fig, ax = plt.subplots()
        # Implementation depends on networkx package
        return fig
    
    def plot_activity_timeline(self) -> plt.Figure:
        """Create timeline of chat activity."""
        fig, ax = plt.subplots()
        daily_messages = pd.Series(self.stats.activity_stats['monthly_pattern'])
        daily_messages.plot(ax=ax)
        ax.set_title("Chat Activity Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Number of Messages")
        return fig
    
    def plot_radar_charts(self) -> plt.Figure:
        """Create radar charts of hourly activity patterns per user."""
        hours = self.stats.hourly_patterns.columns
        angles = np.linspace(0, -2 * np.pi, len(hours), endpoint=False).tolist()
        angles += angles[:1]

        fig, axes = plt.subplots(
            nrows=int(np.ceil(len(self.stats.hourly_patterns) / 3)),
            ncols=3,
            subplot_kw=dict(polar=True),
            figsize=(15, 15)
        )
        
        for idx, (sender, row) in enumerate(self.stats.hourly_patterns.iterrows()):
            ax = axes.flat[idx]
            values = row.tolist()
            values += values[:1]
            
            ax.plot(angles, values)
            ax.fill(angles, values, alpha=0.25)
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels([f"{hour}:00" for hour in hours])
            ax.set_title(sender)

        # Remove empty subplots
        for idx in range(len(self.stats.hourly_patterns), len(axes.flat)):
            fig.delaxes(axes.flat[idx])

        fig.suptitle("Hourly Activity Patterns by User")
        return fig
    
    def generate_report(self, output_dir: str):
        """Generate a complete visual report with all plots."""
        plots = {
            'message_distribution': self.plot_message_distribution(),
            'activity_heatmap': self.plot_activity_heatmap(),
            'activity_timeline': self.plot_activity_timeline(),
            'radar_charts': self.plot_radar_charts()
        }
        
        for name, fig in plots.items():
            fig.savefig(f"{output_dir}/{name}.png")
            plt.close(fig)