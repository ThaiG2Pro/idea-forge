# Idea Forge - AI-Powered Idea Brainstorming Tool

Idea Forge is a locally-hosted web application that helps you generate, evaluate, and refine ideas using AI. Perfect for entrepreneurs, students, and creators looking to develop their concepts.

## Features

- Input a keyword or concept to start the ideation process
- Choose the number of iterations (2-5) for idea refinement
- AI-powered brainstorming and evaluation
- Evaluation based on practical criteria:
  - Solving a Real Problem
  - Market Potential
  - Feasibility for individual implementation
- Easy-to-read conversation format
- Summary of the ideation process
- Export results as PDF
- Clean, minimal, and responsive UI

## Requirements

- Python 3.8+
- API key for one of the supported LLM providers:
  - Groq
  - OpenAI
  - Google AI
  - Anthropic

## Setup

1. Clone the repository:
```
git clone https://github.com/ThaiG2Pro/idea-forge.git
cd idea-forge
```

2. Create a virtual environment and install dependencies:
```
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your API credentials:
```
# Choose one of the following providers and add your API key
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Set your preferred model (optional)
LLM_MODEL=llama3-70b-8192  # Example for Groq
```

4. Start the application:
```
python app.py
```

5. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. Enter a keyword or concept in the text field
2. Select the number of iterations (2-5)
3. Click "Start New Idea"
4. Follow the AI-guided brainstorming process
5. View the final summary
6. Download the results as PDF or start a new session

## Sample Keywords

- Online education platform
- Food delivery service
- Personal finance app
- Smart home device
- Health tracking tool

## License

MIT 