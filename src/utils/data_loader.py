import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple
import re
from pytz import timezone
from functools import partial

class MessengerDataLoader:
    def __init__(self, parent_dir: str = "data"):
        """
        Initialize with a parent directory containing chat folders.
        
        Args:
            parent_dir (str): Path to the parent directory containing chat folders
        """
        self.parent_dir = Path(parent_dir)
        if not self.parent_dir.exists():
            self.parent_dir.mkdir(parents=True)
            
        # Facebook JSON fix for encoding issues
        self.fix_mojibake_escapes = partial(
            re.compile(rb'\\u00([\da-f]{2})').sub,
            lambda m: bytes.fromhex(m[1].decode()),
        )
        
        # Initialize mappings
        self._initialize_chat_mappings()
        
    def _initialize_chat_mappings(self):
        """
        Initialize private mappings between folder names and chat titles by reading
        the first JSON file in each folder. Also computes message counts for sorting.
        """
        self._folder_title_map = {}
        self._title_folder_map = {}
        self._chat_sizes = {}
        
        for folder in self.parent_dir.iterdir():
            if not folder.is_dir():
                continue
                
            # Get all JSON files in the folder
            json_files = list(folder.glob('*.json'))
            if not json_files:
                continue
            
            total_messages = 0
            chat_title = None
            
            # Read all JSON files to get total message count
            for json_file in json_files:
                try:
                    with open(json_file, 'rb') as binary_data:
                        repaired = self.fix_mojibake_escapes(binary_data.read())
                        data = json.loads(repaired)
                        
                        # Get the chat title from first file if not set
                        if chat_title is None and 'title' in data:
                            chat_title = data['title']
                            
                        # Add message count
                        if 'messages' in data:
                            total_messages += len(data['messages'])
                            
                except (json.JSONDecodeError, KeyError, IOError):
                    continue
            
            if chat_title:
                self._folder_title_map[folder.name] = chat_title
                self._title_folder_map[chat_title] = folder.name
                self._chat_sizes[chat_title] = total_messages
    
    @property
    def folder_to_title(self) -> Dict[str, str]:
        """
        Get the mapping of folder names to chat titles.
        
        Returns:
            Dict[str, str]: Mapping of folder names to their chat titles
        """
        return self._folder_title_map.copy()
    
    @property
    def title_to_folder(self) -> Dict[str, str]:
        """
        Get the mapping of chat titles to folder names.
        
        Returns:
            Dict[str, str]: Mapping of chat titles to their folder names
        """
        return self._title_folder_map.copy()
    
    @property
    def chat_sizes(self) -> Dict[str, int]:
        """
        Get the mapping of chat titles to their total message counts.
        
        Returns:
            Dict[str, int]: Mapping of chat titles to message counts
        """
        return self._chat_sizes.copy()
    
    @property
    def chat_names(self) -> List[str]:
        """
        Get list of chat titles sorted by total message count in descending order.
        
        Returns:
            List[str]: List of chat titles
        """
        return sorted(self._title_folder_map.keys(), 
                     key=lambda x: self._chat_sizes[x],
                     reverse=True)
    
    def _get_folder_name(self, chat_title: str) -> str:
        """
        Get the folder name for a given chat title.
        
        Args:
            chat_title (str): Title of the chat
            
        Returns:
            str: Corresponding folder name
        """
        if chat_title not in self._title_folder_map:
            raise ValueError(f"Chat '{chat_title}' not found")
        return self._title_folder_map[chat_title]

    def get_chat_files(self, chat_title: str) -> List[str]:
        """
        Get list of JSON files in a specific chat folder.
        
        Args:
            chat_title (str): Title of the chat
            
        Returns:
            List[str]: List of JSON filenames in the chat folder
        """
        folder_name = self._get_folder_name(chat_title)
        chat_dir = self.parent_dir / folder_name
        
        return [
            file.name for file in chat_dir.iterdir()
            if file.is_file() and file.suffix.lower() == '.json'
        ]

    def load_chat(self, chat_title: str, filename: str) -> Dict[str, Any]:
        """
        Load a Facebook Messenger chat JSON file from a specific chat folder.
        
        Args:
            chat_title (str): Title of the chat
            filename (str): Name of the JSON file to load
            
        Returns:
            Dict containing the chat data
        """
        folder_name = self._get_folder_name(chat_title)
        file_path = self.parent_dir / folder_name / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Chat file not found: {file_path}")
        
        with open(file_path, 'rb') as binary_data:
            repaired = self.fix_mojibake_escapes(binary_data.read())
            data = json.loads(repaired)
        return data
    
    def load_all_chat_files(self, chat_title: str) -> List[Dict[str, Any]]:
        """
        Load all JSON files from a specific chat folder.
        
        Args:
            chat_title (str): Title of the chat
            
        Returns:
            List[Dict[str, Any]]: List of loaded JSON data from all files
        """
        chat_files = self.get_chat_files(chat_title)
        return [
            self.load_chat(chat_title, filename)
            for filename in chat_files
        ]

    def to_dataframe(self, chat_data: Dict[str, Any], remove_reactions: bool = True) -> pd.DataFrame:
        """
        Convert chat data to a pandas DataFrame with proper timestamps in Australian timezone.
        Assumes that every chat data dict contains at least the timestamp_ms and content columns.
        
        Args:
            chat_data (Dict): Raw chat data from JSON
            remove_reactions (bool): Whether to remove reaction messages
            
        Returns:
            pd.DataFrame: Processed chat data
        """
        # Load messages into a DataFrame
        messages = chat_data['messages']
        df = pd.DataFrame(messages)
        
        # Convert timestamps to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp_ms'], unit='ms')
        
        # Convert to Australian timezone with daylight savings
        aus_timezone = timezone('Australia/Sydney')
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert(aus_timezone)

        # Create Reactions and Photos columns if not exists.
        if 'reactions' not in df.columns:
            df['reactions'] = None
        if 'photos' not in df.columns:
            df['photos'] = None

        # Simple data transformation
        df['date'] = df['timestamp'].dt.date
        df['month'] = df['timestamp'].dt.month
        df['hour'] = df['timestamp'].dt.hour
        df['num_words'] = df['content'].str.split().str.len()
        df['num_characters'] = df['content'].str.replace(' ', '').str.len()
        df['is_reaction'] = df['content'].fillna('').str.contains(r'reacted .* to your message', case=False, regex=True)
        df['num_reactions'] = df['reactions'].fillna('').str.len() 
        df['num_photos'] = df['photos'].fillna('').str.len()

        # Drop the original timestamp_ms column
        df = df.drop('timestamp_ms', axis=1)

        # Remove reaction records if required
        if remove_reactions:
            df = df.drop(df[df['is_reaction']].index)
        
        return df

    def combine_chats(self, chats: list, remove_reactions: bool = True) -> pd.DataFrame:
        """
        Converts a list of chats to a pandas DataFrame with proper timestamps.
        
        Args:
            chats (list): A list of raw chat data from JSON
            remove_reactions (bool): Whether to remove reaction messages
            
        Returns:
            pd.DataFrame: Processed chat data
        """
        df = pd.concat([self.to_dataframe(chat, remove_reactions) for chat in chats], axis=0)
        df = df.sort_values('timestamp')
        df = df.reset_index(drop=True)
        df = df.reset_index(names='message_id')
        return df
    
    def process_chat_folder(self, chat_title: str, remove_reactions: bool = True) -> pd.DataFrame:
        """
        Process all JSON files in a chat folder and combine them into a single DataFrame.
        
        Args:
            chat_title (str): Title of the chat
            remove_reactions (bool): Whether to remove reaction messages
            
        Returns:
            pd.DataFrame: Combined and processed chat data
        """
        chat_data = self.load_all_chat_files(chat_title)
        return self.combine_chats(chat_data, remove_reactions)