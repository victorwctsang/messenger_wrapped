from collections import Counter
import pandas as pd
import re
from pytz import timezone
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
# Download required NLTK data
nltk.download('punkt_tab')
nltk.download('stopwords')

def clean_word(word):
    # Convert to lowercase and remove punctuation
    word = re.sub(r'[^\w\s]', '', word.lower())
    return word

def get_word_counts(messages, min_word_length=3, top_n=20):
    # Get English stop words from NLTK
    stop_words = set(stopwords.words('english'))
    
    words = []
    for message in messages:
        if isinstance(message, str):
            # Tokenize and clean each word
            tokens = word_tokenize(message.lower())
            # Filter out stop words, empty strings, short words, and non-alphabetic tokens
            message_words = [clean_word(word) for word in tokens]
            message_words = [word for word in message_words 
                           if word 
                           and len(word) >= min_word_length 
                           and word not in stop_words
                           and word.isalpha()]
            words.extend(message_words)
    
    # Get word counts
    word_counts = Counter(words)
    
    # Return top N words and their counts
    return dict(sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:top_n])

def is_shouting(word):
    # Check if word is all caps and at least 2 characters long
    # We check length to avoid counting single-letter words or abbreviations like "I" or "OK"
    return word.isupper() and len(word) > 1

# Create a function to count shouted words in a message
def count_shouted_words(message):
    if not isinstance(message, str):
        return 0
    words = message.split()
    return sum(is_shouting(word) for word in words)


def find_longest_active_streak(df: pd.DataFrame) -> (int, str, str):
    """
    Calculate the longest active streak of consecutive days in a chat.
    
    Args:
        df (pd.DataFrame): Chat DataFrame with a 'date' column (datetime format)
        
    Returns:
        tuple: (length of the longest streak, start date, end date)
    """
    # Ensure the 'date' column is in datetime format
    df['date'] = pd.to_datetime(df['date'])
    
    # Extract unique dates when messages were sent
    unique_dates = df['date'].dt.date.unique()
    unique_dates = sorted(unique_dates)  # Sort dates chronologically
    
    # Initialize variables to track the longest streak
    longest_streak = 1
    current_streak = 1
    longest_start = unique_dates[0]
    longest_end = unique_dates[0]
    current_start = unique_dates[0]
    
    for i in range(1, len(unique_dates)):
        # Check if the current date is consecutive to the previous date
        if (unique_dates[i] - unique_dates[i - 1]).days == 1:
            current_streak += 1
        else:
            # Update the longest streak if the current streak is longer
            if current_streak > longest_streak:
                longest_streak = current_streak
                longest_start = current_start
                longest_end = unique_dates[i - 1]
            # Reset current streak
            current_streak = 1
            current_start = unique_dates[i]
    
    # Final check for the last streak
    if current_streak > longest_streak:
        longest_streak = current_streak
        longest_start = current_start
        longest_end = unique_dates[-1]
    
    return longest_streak, str(longest_start), str(longest_end)

def count_rows_by_grouping_keys(df: pd.DataFrame, grouping_keys: list) -> pd.DataFrame:
    """
    Wrapper for boilerplate code counting rows in a dataframe meeting a criteria.
    
    Args:
        df (pd.DataFrame): DataFrame
        grouping_keys (list): List of grouping keys. Keys must be found in DataFrame.
    
    Returns:
        pd.DataFrame: A dataframe containing the grouped data. Always returns in descending order.
    """
    grouped_data = df.groupby(grouping_keys).size().sort_values(ascending=False)
    return grouped_data

def count_pairwise_reactions(reaction_df: pd.DataFrame, index: str, column: str) -> pd.DataFrame:
    return pd.pivot_table(
        reaction_df, 
        index=index, 
        columns=column, 
        aggfunc='size', 
        fill_value=0
    )

def calculate_pairwise_reaction_imbalance(reaction_matrix: pd.DataFrame) -> pd.DataFrame:
    return reaction_matrix - reaction_matrix.T