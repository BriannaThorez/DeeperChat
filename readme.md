# DeeperChat - Terminal AI Assistant
DeeperChat is a powerful terminal-based chatbot that leverages the DeepSeek API to deliver intelligent conversations right in your command line. Designed for developers, researchers, and power users who prefer working in the terminal.
*"The terminal is my home - now my AI assistant lives there too."*  
**<u>Note: Requires DeepSeek API key (free tier available)</u>**
#### ✨ TL;DR Quirks

- Lightweight (API calls)
- Easy programming output & copy
- Foundation for future self-writing and rewriting code expansion
- Roadmap for cognitive retention via vector DB
  
<div style="display: flex; overflow-x: auto; gap: 16px; padding: 16px 0;">
  <div style="flex: 0 0 auto; min-width: 300px; text-align: left;">
    <img src="https://github.com/user-attachments/assets/56bf1b40-db72-499f-9ee6-70a6174d0b9f" style="height: 400px; border-radius: 8px;">
    <p> </p>
  </div>
</div>
## ✨ Key Features

**💬 Smart Terminal Chat**  
- Natural conversations with DeepSeek's advanced AI  
- Streamed responses for real-time interaction  
- Customizable user/assistant names  

**📋 Code Block Recognition**  
- Beautiful syntax highlighting (with Rich if available)  
- One-key copy functionality (just press the block number)  
- Plain-text fallback when Rich isn't available  

**🔄 Dynamic Module System**  
- Hot-swappable modules without restarting  
- "Expansive" directory for experimental versions of its own foundation code 
- Automatic fallback to stable versions  

**🔒 Secure Configuration**  
- Interactive first-time setup wizard  
- API key validation and protection  
- User profile management  

## 🚀 Roadmap

**📚 Chat With Your Documents**  
- Ingest and query your personal files  
- Smart chunking to maintain context  
- Vector database integration  

####🔍 Smarter Context Understanding  
- **Coreference resolution**
    Better contextual continuity via tracking "it", "they" across messages, replacing with proper nouns for superior contextual handling even from chunks of larger data.  
- **VectorDB Context metadata**
    Better conversation continuity and improved long-context handling using timestamps, usernames, and other contextual gamechangers in vectorDB metadata

**⚙️ Enhanced Module System**  
- Versioned module updates  
- Dependency management  
- Safe rollback capabilities  

## 🛠️ Installation

```bash
git clone https://github.com/yourusername/DeeperChat.git
cd DeeperChat
pip install -r requirements.txt
python main.py
```
(First run will guide you through setup)

**🌟 Why Choose DeeperChat?**
- Privacy-focused: Your data stays local
- Keyboard-optimized: Built for terminal lovers
- Extensible: Ready for your custom modules
- Lightweight: No heavy GUI dependencies

Perfect for:
- Quick coding help without context switching
- Research assistance during development
- Learning new concepts interactively
