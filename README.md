# Your Messenger Chat Wrapped 2024

Messenger Chat Wrapped 2024 is a locally deployed Streamlit app that generates insightful summary statistics for a selected Facebook Messenger chat. Inspired by Spotify Wrapped, this project aims to visualize some simple summary statistics of chat activity as a webapp.

## Features
- **Total Messages Overview**: Displays the total messages exchanged and the average daily messages in the chat.
- **Messages by Person**: Bar chart highlighting the most active participants in the conversation.
- **Most Used Words**: Analysis of frequently used words within the chat.
- **Reaction Champions**:
  - *Most Reactions Received*: Shows who received the most reactions.
  - *Most Reactions Given*: Highlights the most generous reactors.
- **Chat Activity Over Time**: Line graph showcasing activity trends throughout the year.
- **Peak Chatting Hours**: Radial plot that visualizes the chat's most active hours.

## Getting Started

### Prerequisites
- Python 3.8+
- Streamlit library
- Facebook chat export file in JSON format

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/victorwctsang/messenger_wrapped.git
   cd chat-wrapped-2024
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Usage
1. Export your Facebook chat data from the Messenger website.
2. Place the exported JSON file in the project directory.
3. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```
4. Input the folder with all your message data (e.g. `data/messages/inbox`) through the app interface.
5. Select a chat of interest (they're sorted in descending order of number of messages).
6. Explore the visualized chat statistics!

## Example Output (TODO)

## Future Improvements
* Add tests and more detailed error handling.
* Add a debug mode for easier development.
* Add an "upload file" version of this app, so users can upload individual files/folders.
* Deploy this as a webapp (currently this only works locally, since streamlit doesn't currently support folder selection).
* Adapt this into a Facebook app, so users can load their chats without downloading from facebook.
* Introduce an API option for data loading, so users can load their chats without downloading from facebook.

## Contributing
Contributions are welcome! Feel free to open issues or submit pull requests to enhance the app.

### Steps to Contribute
1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes and commit them:
   ```bash
   git commit -m "Add your message here"
   ```
4. Push to your branch:
   ```bash
   git push origin feature/your-feature-name
   ```
5. Open a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments
- Inspired by Spotify Wrapped.
- Built with [Streamlit](https://streamlit.io/).

## Contact
For any questions or feedback, please open an issue!

---
Thanks for using Chat Wrapped 2024 to relive your chat memories!
