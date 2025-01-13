# messenger_analysis/analyzer.py

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass 
from pytz import timezone
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
from collections import Counter

@dataclass
class ChatStats:
    num_messages: int
    num_words: int
    avg_messages_per_day: int
    person_stats: pd.DataFrame
    hourly_stats: pd.DataFrame
    word_counts: Dict[str, int]
    received_reaction_stats: pd.DataFrame
    sent_reaction_stats: pd.DataFrame
    messages_by_user_by_day: pd.DataFrame

class MessengerAnalyzer:
    def __init__(self, messages_df: pd.DataFrame):
        """
        Initialize the analyzer with a DataFrame containing message data.
        
        Args:
            messages_df: DataFrame with columns: sender_name, content, timestamp, 
                        is_reaction, photos, num_reactions
        """
        self.messages = messages_df[~messages_df['is_reaction']].copy()
        self.messages['shouted_words'] = self.messages['content'].apply(
            self._count_shouted_words
        )
        self.reactions = self._extract_reactions()
        self.photos = self.messages[self.messages['photos'].notna()].copy()
        
    def _get_person_stats(self) -> pd.DataFrame:
        message_stats = self.messages.groupby('sender_name', as_index=False).agg(
            messages_sent = ('message_id', 'size'),
            words_sent = ('num_words', 'sum'),
            words_shouted = ('shouted_words', 'sum'))

        message_stats['shouting_percentage'] = (
                message_stats['words_shouted'] / message_stats['words_sent'] * 100
            ).round(2)

        reaction_stats = self._analyze_reactions()
        return message_stats.merge(reaction_stats, on='sender_name')

    def _extract_reactions(self) -> pd.DataFrame:
        """
        Extracts the reactions from a chat dataframe. One row for each reaction.

        `message_id` acts as a key to join back to the messages.

        Returns:
            pd.DataFrame: Reactions dataframe.
        """
        messages_with_reactions = self.messages[~self.messages['reactions'].isna()]
        reactions = messages_with_reactions[['message_id', 'sender_name', 'reactions', 'timestamp']].explode('reactions').copy()
        reactions = reactions.rename(columns={'reactions': 'reaction', 'timestamp': 'message_timestamp'})
        reactions['recipient'] = reactions['sender_name']
        reactions['emoji'] = reactions['reaction'].apply(lambda x: x['reaction'])
        reactions['reactor'] = reactions['reaction'].apply(lambda x: x['actor'])
        reactions['reaction_timestamp_ms'] = reactions['reaction'].apply(lambda x: x.get('timestamp'))
        reactions['reaction_timestamp'] = pd.to_datetime(reactions['reaction_timestamp_ms'], unit='s').dt.tz_localize('UTC').dt.tz_convert(timezone('Australia/Sydney'))
        reactions['reaction_timedelta_sec'] = (reactions['reaction_timestamp'] - reactions['message_timestamp']).dt.seconds
        reactions['pair'] = reactions.apply(lambda row: tuple(sorted([row['reactor'], row['recipient']])), axis=1)
        return reactions

    def _clean_word(self, word):
        # Convert to lowercase and remove punctuation
        word = re.sub(r'[^\w\s]', '', word.lower())
        return word

    def _get_word_counts(self, min_word_length=3) -> Dict[str, int]:
        # Download required NLTK data
        nltk.download('punkt_tab', quiet=True)
        nltk.download('stopwords', quiet=True)

        # Get English stop words from NLTK
        stop_words = set(stopwords.words('english'))
        
        words = []
        for message in self.messages['content']:
            if isinstance(message, str):
                # Tokenize and clean each word
                tokens = word_tokenize(message.lower())
                # Filter out stop words, empty strings, short words, and non-alphabetic tokens
                message_words = [self._clean_word(word) for word in tokens]
                message_words = [word for word in message_words 
                            if word 
                            and len(word) >= min_word_length 
                            and word not in stop_words
                            and word.isalpha()]
                words.extend(message_words)
        
        # Get word counts
        word_counts = Counter(words)
        # Return top N words and their counts
        return dict(sorted(word_counts.items(), key=lambda x: x[1], reverse=True))

    def _count_shouted_words(self, text: str) -> int:
        """Count words in all caps in a text string."""
        if pd.isna(text):
            return 0
        words = text.split()
        return sum(1 for word in words if word.isupper() and len(word) > 1)

    def _get_top_shouting_messages(self, n: int = 5) -> pd.DataFrame:
        """Get the top N messages with most shouting."""
        return (self.messages[self.messages['shouted_words'] > 0]
                .sort_values('shouted_words', ascending=False)
                .head(n))

    def _analyze_reactions(self) -> pd.DataFrame:
        """Analyze reaction patterns."""
        reacts_received = self.reactions.groupby('sender_name').size()
        reacts_sent = self.reactions.groupby('reactor').size()
        
        reaction_stats = pd.merge(
            left=reacts_sent.reset_index(),
            right=reacts_received.reset_index(),
            how='outer',
            left_on='reactor',
            right_on='sender_name'
        ).fillna(0)
        reaction_stats = reaction_stats.drop(columns=['sender_name'])
        reaction_stats.columns = ['sender_name', 'reactions_sent', 'reactions_received']
        reaction_stats['reactions_receive_sent_ratio'] = (
            (reaction_stats['reactions_received'] / (reaction_stats['reactions_sent'] + reaction_stats['reactions_received']))
        ).round(2)
        
        return reaction_stats.sort_values('reactions_received', ascending=False)

    def _analyze_reactions_received(self) -> pd.DataFrame:
        received_reactions_stats = self.reactions.groupby(
            ['emoji', 'recipient'],
            as_index=False
        ).agg(
            num_reacts = ('reaction_timestamp', 'size')
        ).pivot_table(
            index = 'emoji',
            columns = 'recipient',
            values = 'num_reacts',
            margins=True,
            aggfunc='sum',
            fill_value=0
        ).sort_values(
            by='All',
            ascending=False
        )
        return received_reactions_stats

    def _analyze_reactions_sent(self) -> pd.DataFrame:
        sent_reactions_stats = self.reactions.groupby(
            ['emoji', 'reactor'],
            as_index=False
        ).agg(
            num_reacts = ('reaction_timestamp', 'size')
        ).pivot_table(
            index = 'emoji',
            columns = 'reactor',
            values = 'num_reacts',
            margins=True,
            aggfunc='sum',
            fill_value=0
        ).sort_values(
            by='All',
            ascending=False
        )
        return sent_reactions_stats

    def _analyze_photos(self) -> pd.DataFrame:
        """Analyze photo sharing patterns."""
        return (self.photos.groupby('sender_name')
                .agg(
                    total_photos=('num_photos', 'sum'),
                    most_reactions=('num_reactions', 'max')
                )
                .sort_values('total_photos', ascending=False))

    def _analyze_activity_patterns(self) -> Dict:
        """Analyze temporal activity patterns."""
        messages_by_person_by_date = self.messages.groupby(
            ['date', 'sender_name']
        ).agg(
            num_messages = ('date', 'size')
        ).rolling(7).mean().reset_index().pivot_table(
            index='date',
            columns='sender_name',
            values='num_messages',
            fill_value=0,
            margins=True,
            aggfunc='sum'
        ).iloc[:-1, :]
        
        return messages_by_person_by_date

    def _analyze_hourly_patterns(self) -> pd.DataFrame:
        """Analyze hourly activity patterns."""
        hourly_stats_by_person = (
            self.messages.groupby(['sender_name', 'hour'])
            .size()
            .unstack(fill_value=0)).T
        hourly_stats_by_person['All'] = hourly_stats_by_person.sum(axis=1)
        return hourly_stats_by_person.reset_index()

    def get_streak_info(self) -> Tuple[int, str, str]:
        """Find the longest streak of consecutive days with messages."""
        dates = sorted(self.messages['date'].unique())
        max_streak = current_streak = 1
        max_start = max_end = start_date = dates[0]
        
        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]).days == 1:
                current_streak += 1
                if current_streak > max_streak:
                    max_streak = current_streak
                    max_start = start_date
                    max_end = dates[i]
            else:
                current_streak = 1
                start_date = dates[i]
        
        return max_streak, max_start.strftime('%Y-%m-%d'), max_end.strftime('%Y-%m-%d')

    def analyze(self) -> ChatStats:
        """Perform complete analysis of the chat history."""
        
        # Basic message counts
        num_messages = self.messages.shape[0]
        num_words = self.messages['num_words'].sum()
        avg_messages_per_day = self.messages.groupby('date').size().mean().round(1)
        person_stats = self._get_person_stats()
        
        # Word analysis
        word_counts = self._get_word_counts(min_word_length=3)
        
        # Words per sender stats
        words_per_sender = {}
        for user in self.messages['sender_name'].unique():
            user_messages = self.messages[
                self.messages['sender_name'] == user
            ]['content']
            words_per_sender[user] = {
                'total_words': user_messages.str.split().str.len().sum(),
                'avg_words_per_message': user_messages.str.split().str.len().mean()
            }
        
        # Total messages by time
        messages_by_user_by_day = self._analyze_activity_patterns()
        hourly_totals = self._analyze_hourly_patterns()
        
        # Received Reactions
        received_reaction_stats = self._analyze_reactions_received()
        
        # Sent Reactions
        sent_reaction_stats = self._analyze_reactions_sent()
        return ChatStats(
            num_messages=num_messages,
            num_words=num_words,
            avg_messages_per_day=avg_messages_per_day,
            person_stats=person_stats,
            hourly_stats=hourly_totals,
            word_counts=word_counts,
            received_reaction_stats=received_reaction_stats,
            sent_reaction_stats=sent_reaction_stats,
            messages_by_user_by_day = messages_by_user_by_day
        )