# LLM_RAG_RESUME

A project for leveraging Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG) techniques to process and analyze resume data.

## Features

- Resume ingestion and parsing using docling library
- chucking with ExperimentalMarkdownSyntaxTextSplitter from langchain
- store vector database on pinecone and using llama-text-embed-v2 for embedding content
- Retrieval-augmented Q&A over resume by gemma3:4b in ollama with RAG
- Supports multiple input formats

## Getting Started

### Prerequisites

- Python 3.12+
- pip install uv
- uv pip install torch torchvision --index-url [https://download.pytorch.org/whl/cu126](https://pytorch.org/get-started/locally/)
- GPU nividia

### Installation

Clone the repository:

```bash
git clone https://github.com/sittikornnn/LLM_RAG_RESUME.git
cd LLM_RAG_RESUME
```

Install dependencies:

```bash
uv pip install -r requirements.txt
```

create .env for api key
```bash
PINECONE_API_KEY = 
PINECONE_INDEX_NAME = 
CHAT_MODEL = gemma3:4b
```

### Usage

Run the main script:

```bash
python llm_rag.ipynb
```

## Configuration

You can configure your settings in `config.py` or via environment variables. Refer to the documentation for details.

## Example

1. Place your resume files in the `data/` directory.
2. Run the script and follow the prompts to analyze a resume.

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Contact

For questions or feedback, open an issue or contact sittikornnn.
