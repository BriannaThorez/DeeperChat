import os
import re
from datetime import datetime
from typing import List, Dict, Optional
import chromadb
from chromadb.utils import embedding_functions
from utilities.setup_config import ensure_config
import nltk
from nltk import word_tokenize
from nltk.util import ngrams

class ResponseHandler:
    def __init__(self):
        self.config = ensure_config()
        self.user_name = self.config.get('user_name', 'User')
        self.assistant_name = "Assistant"
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection = self.client.get_or_create_collection(
            name="chat_responses",
            embedding_function=self.sentence_transformer_ef,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Chunking configuration
        self.sentence_window = 3  # Number of sentences per chunk
        self.sentence_overlap = 1  # Number of overlapping sentences between chunks

        # Download NLTK data if not already present
        nltk.download('punkt', quiet=True)

    def _extract_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex."""
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', text)
        return [s.strip() for s in sentences if s.strip()]

    def _create_chunks(self, sentences: List[str]) -> List[str]:
        """Create chunks with overlapping sentences."""
        chunks = []
        i = 0
        while i < len(sentences):
            chunk = ' '.join(sentences[i:i+self.sentence_window])
            chunks.append(chunk)
            i += (self.sentence_window - self.sentence_overlap)
        return chunks

    def _generate_timestamp(self) -> str:
        """Generate ISO format timestamp."""
        return datetime.now().isoformat()

    def _calculate_ngram_similarity(self, text1: str, text2: str, n: int = 2) -> float:
        """Calculate ngram similarity between two texts."""
        tokens1 = word_tokenize(text1.lower())
        tokens2 = word_tokenize(text2.lower())
        
        ngrams1 = set(ngrams(tokens1, n))
        ngrams2 = set(ngrams(tokens2, n))
        
        if not ngrams1 or not ngrams2:
            return 0.0
            
        intersection = len(ngrams1.intersection(ngrams2))
        union = len(ngrams1.union(ngrams2))
        
        return intersection / union
    def store_response(self, user_name: str, assistant_name: str, prompt: str, response: str) -> None:
            """
            Process and store both the user prompt and the assistant response
            as separate chunks in ChromaDB, associating the correct speaker
            (user or assistant) with each chunk in the metadata.
            """
            # Note: We use the user_name and assistant_name passed as arguments.
            # The self.user_name and self.assistant_name from __init__ are not directly used here
            # unless passed in the function call from the main script.

            turn_timestamp = self._generate_timestamp() # Common timestamp for this prompt/response pair

            all_documents = []
            all_metadatas = []
            all_ids = []

            # --- Process and Store User Prompt ---
            if prompt and prompt.strip(): # Check if prompt exists and is not just whitespace
                prompt_sentences = self._extract_sentences(prompt)
                prompt_chunks = self._create_chunks(prompt_sentences)
                num_prompt_chunks = len(prompt_chunks)
                for i, chunk in enumerate(prompt_chunks):
                    # Metadata for prompt chunk
                    metadata = {
                        "timestamp": turn_timestamp,    # Link prompt and response from the same turn
                        "speaker": user_name,           # Identify the speaker as the user
                        "content_type": "prompt",       # Mark the type of content
                        "chunk_index": i,
                        "total_chunks": num_prompt_chunks
                        # "original_prompt" metadata doesn't make sense for the prompt itself
                    }
                    # Unique ID for the prompt chunk
                    doc_id = f"{turn_timestamp}_prompt_{i}"

                    all_documents.append(chunk)
                    all_metadatas.append(metadata)
                    all_ids.append(doc_id)

            # --- Process and Store Assistant Response ---
            if response and response.strip(): # Check if response exists and is not just whitespace
                response_sentences = self._extract_sentences(response)
                response_chunks = self._create_chunks(response_sentences)
                num_response_chunks = len(response_chunks)

                for i, chunk in enumerate(response_chunks):
                    # Metadata for response chunk
                    metadata = {
                        "timestamp": turn_timestamp,    # Link prompt and response from the same turn
                        "speaker": assistant_name,      # Identify the speaker as the assistant
                        "content_type": "response",     # Mark the type of content
                        "original_prompt": prompt[:200], # Keep context for the response
                        "chunk_index": i,
                        "total_chunks": num_response_chunks
                    }
                    # Unique ID for the response chunk
                    doc_id = f"{turn_timestamp}_response_{i}"

                    all_documents.append(chunk)
                    all_metadatas.append(metadata)
                    all_ids.append(doc_id)

            # --- Store combined chunks in ChromaDB ---
            if all_documents:
                try:
                    self.collection.add(
                        documents=all_documents,
                        metadatas=all_metadatas,
                        ids=all_ids
                    )
                    # Optional: Add a print statement for confirmation/debugging
                    # print(f"[Storage] Added {len(prompt_chunks) if prompt and prompt.strip() else 0} prompt and {len(response_chunks) if response and response.strip() else 0} response chunks for turn {turn_timestamp}.")
                except Exception as e:
                    print(f"[Storage Error] Failed to add documents for turn {turn_timestamp}: {e}")
                    # Consider logging more details if errors occur frequently
    def recall_memory(self, query_text: str, max_results: int = 3, min_similarity: float = 0.2) -> List[Dict]:
        """
        Recalls relevant memories from ChromaDB.

        Modifies the 'content' field in results to be:
        'speaker[timestamp]: original_content'

        Args:
            query_text: The text to search for.
            max_results: Maximum number of results to return.
            min_similarity: Minimum similarity score (0-1) for results.

        Returns:
            List of dictionaries containing formatted content, metadata, and similarity score.
        """

        if not query_text.strip():
            return []

        # Get initial results
        initial_results = self.collection.query(
            query_texts=[query_text],
            n_results=max(10, max_results * 3) # Fetch extra for filtering
        )

        # Handle cases where query returns nothing or malformed results
        if not initial_results or not initial_results.get('ids') or not initial_results['ids'][0]:
            return []

        # Process and filter results
        filtered_results = []

        for i in range(len(initial_results['ids'][0])):
            original_content = initial_results['documents'][0][i]
            metadata = initial_results['metadatas'][0][i]
            distance = initial_results['distances'][0][i]
            similarity = 1.0 - distance # Convert distance to similarity

            # Filter by similarity score
            if similarity < min_similarity:
                continue

            # --- Augment retrievals with metadata: username and timestamp ---
            # Retrieve user_name and timestamp with defaults
            speaker = metadata.get('speaker', 'UnknownUser')
            # Use a clearer default for missing timestamp
            timestamp = metadata.get('timestamp', 'NoTimestamp')

            # Format the content string as requested
            formatted_content = f"{speaker}[{timestamp}]: {original_content}"
            # --- Augment End ---

            # Check for duplicates based on the *original* content
            is_duplicate = False
            for existing_result in filtered_results:
                # Access original content stored temporarily for comparison
                content_to_compare = existing_result['metadata'].get('_original_content_for_dedup', '')
                if self._calculate_ngram_similarity(original_content, content_to_compare) > 0.7: # High threshold for near-exact match
                    is_duplicate = True
                    break

            if not is_duplicate:
                result_data = {
                    'content': formatted_content, # Store the newly formatted string
                    'metadata': metadata.copy(), # Use a copy to avoid modifying original dict if needed elsewhere
                    'score': similarity
                }
                # Store original content temporarily within this result's metadata for future duplicate checks
                result_data['metadata']['_original_content_for_dedup'] = original_content

                filtered_results.append(result_data)

                # Stop if we have enough results
                if len(filtered_results) >= max_results:
                    break

        # Clean up the temporary key used for deduplication before returning
        for res in filtered_results:
            res['metadata'].pop('_original_content_for_dedup', None)

        # Sort results by score (highest similarity first) before returning
        filtered_results.sort(key=lambda x: x['score'], reverse=True)

        # Return only the requested number of results
        return filtered_results[:max_results]

    def query_responses(self, query_text: str, n_results: int = 5) -> List[Dict]:
        """Alias for recall_memory for backward compatibility"""
        # Update the call if you change recall_memory's signature significantly
        return self.recall_memory(query_text, max_results=n_results)