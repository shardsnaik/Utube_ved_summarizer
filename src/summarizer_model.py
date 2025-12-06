import logging
from typing import List
from llama_cpp import Llama
from config import AppConfig

logger = logging.getLogger(__name__)
configs = AppConfig().config

class OfflineSummarizer:
    '''
    Docstring for OfflineSummarizer
    '''
    def __init__(self,
                 model_path:str = configs.summarizer_model.summarizer_model_path,
                 max_context: int = configs.summarizer_model.summarizer_max_context,
                 temperature:int = 0.2,
                 gpu_layers:int = configs.summarizer_model.gpu_layers):
         '''
         Args:
            model_path: Path to Quantized .gguf model
            max_context: LLaMA context window
            gpu_layers: Layers to offload to GPU (for speed). Set 0 for CPU-only.
         '''
         logger.info(f'Loading rthe quantised model:{model_path}')
         
         self.llm = Llama(
              model_path = model_path,
               n_ctx=max_context,
            n_threads=8,          # Auto adjust based on CPU
            n_gpu_layers=gpu_layers,
            verbose=False
         )
         self.max_context = max_context
         self.temperature = temperature
        #  self.top_p = top_p
         logger.info('Model Loaded Successfully')
    
    def _generate(self, prompt:str, max_tokens:int= 512)-> str:
         '''
         Generate txt from mdoel with deterministic settings
         '''

         response= self.llm(
              prompt,
              max_tokens = max_tokens,
              temperature = self.temperature,
              repeat_penalty = 1.1,
              stop = ["<end>", "</summary>", "###"]
,         )
         return response['choices'][0]['text'].strip()
    

    def chunk_text(self, text:str, max_words:int=configs.summarizer_model.max_words)->List[str]:
         """
        Splits text into readable chunks while preserving sentences.
        """

         import re
         sentences = re.split(r'(?<=[.!?]) +', text)
         chunks = []
         current = ""
 
         for sent in sentences:
             if len(current.split()) + len(sent.split()) > max_words:
                 chunks.append(current)
                 current = sent
             else:
                 current += " " + sent
 
         if current:
             chunks.append(current)
 
         logger.info(f"Text split into {len(chunks)} chunks.")
         return chunks


    def summarize_chunk(self, chunk: str) -> str:
        prompt = f"""
You are an expert summarizer. Summarize the following transcript chunk
in clear bullet points. Remove filler words. Preserve key ideas.

Transcript Chunk:
\"\"\"{chunk}\"\"\"

Summary:
"""

        return self._generate(prompt, max_tokens=300)


    def summarize_final(self, all_chunk_summaries: str) -> str:
        prompt = f"""
You are a professional long-form summarizer.

Your task:
- Convert distributed chunk summaries into ONE clean final summary.
- Keep it structured.
- Include all important ideas.
- Remove duplication.

Chunk Summaries:
\"\"\"{all_chunk_summaries}\"\"\"

FINAL SUMMARY:
"""

        return self._generate(prompt, max_tokens=600)

    # ----------------------------------------------------------
    #  🔥 MAIN SUMMARIZATION PIPELINE
    # ----------------------------------------------------------
    def summarize(self, text: str) -> str:
        """
        Complete hierarchical summarization for long YouTube transcripts.
        """

        if not text.strip():
            raise ValueError("Empty transcript given to summarizer")

        logger.info("Starting summarization...")

        # 1. Split transcript into sentence-aware chunks
        chunks = self.chunk_text(text, max_words=800)

        # 2. Summarize each chunk
        mini_summaries = []
        for i, chunk in enumerate(chunks, start=1):
            logger.info(f"Summarizing chunk {i}/{len(chunks)}...")
            mini_sum = self.summarize_chunk(chunk)
            mini_summaries.append(mini_sum)

        # 3. Combine all mini summaries and produce final summary
        combined = "\n".join(mini_summaries)

        logger.info("Generating final summary...")
        final_summary = self.summarize_final(combined)

        logger.info("Summary complete.")
        return final_summary.strip()


# ----------------------------------------------------------
#  OPTIONAL: CLI TEST
# # ----------------------------------------------------------
# if __name__ == "__main__":
#     summarizer = OfflineSummarizer(
#         model_path="models/Phi-4-mini-instruct-Q4_K_M.gguf",
#         gpu_layers=0  # CPU-only test
#     )

#     text = "This is a long transcript ... (paste sample here)"
#     print(summarizer.summarize(text))
         
