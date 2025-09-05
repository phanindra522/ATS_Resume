# LLM Integration Setup

This ATS system now supports intelligent job description parsing using Large Language Models (LLMs). The system is designed to be provider-agnostic, allowing you to switch between different LLM providers without changing any code.

## Supported Providers

- **OpenAI** (GPT-3.5, GPT-4)
- **Google Gemini** (Gemini Pro)
- **Anthropic** (Claude) - Ready for future implementation
- **Local Models** - Ready for future implementation

## Quick Setup

### 1. Create .env File

Create a `.env` file in the backend directory with your configuration:

```bash
# LLM Configuration
LLM_PROVIDER=openai  # Options: openai, gemini, anthropic, local
LLM_PROVIDER_API_KEY=your_api_key_here
LLM_EMBEDDING_MODEL=text-embedding-ada-002

# Other required settings
SECRET_KEY=your_secret_key_here
```

### 2. Choose Your LLM Provider

Edit the `.env` file and set your preferred provider:

```bash
# For OpenAI (default)
LLM_PROVIDER=openai
LLM_PROVIDER_API_KEY=sk-your-openai-api-key-here

# For Google Gemini
LLM_PROVIDER=gemini
LLM_PROVIDER_API_KEY=your-gemini-api-key-here
```

### 3. Install Required Packages

#### For OpenAI:
```bash
pip install openai
```

#### For Google Gemini:
```bash
pip install google-generativeai
```

## Usage

### Automatic Job Parsing

When you upload a job description file (PDF, DOCX, TXT), the system will:

1. **Extract text** from the file
2. **Use LLM** to intelligently parse the content
3. **Auto-fill** the form with extracted information
4. **Fallback** to rule-based parsing if LLM fails

### API Endpoints

#### Check LLM Configuration
```bash
GET /api/jobs/llm-config
```

#### Test LLM Parsing
```bash
POST /api/jobs/test-llm
Content-Type: application/json

{
  "text": "Software Engineer at Tech Corp. Requirements: 5+ years Python experience."
}
```

#### Extract from File
```bash
POST /api/jobs/extract
Content-Type: multipart/form-data

file: [your job description file]
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider to use | `openai` |
| `LLM_PROVIDER_API_KEY` | API key for the selected provider | - |
| `LLM_EMBEDDING_MODEL` | Embedding model to use | `text-embedding-ada-002` |

### Switching Providers

To switch from OpenAI to Gemini:

1. Edit your `.env` file:
   ```bash
   LLM_PROVIDER=gemini
   LLM_PROVIDER_API_KEY=your_gemini_key
   ```

2. Restart the server - no code changes needed!

## Features

### Intelligent Parsing
- **Context Understanding**: LLM understands job descriptions in any format
- **Smart Extraction**: Accurately identifies job titles, companies, skills, requirements
- **Flexible Input**: Works with PDF, DOCX, TXT files
- **Structured Output**: Returns consistent JSON format

### Fallback System
- **Graceful Degradation**: Falls back to rule-based parsing if LLM fails
- **Error Handling**: Comprehensive error handling and logging
- **Reliability**: System continues to work even without LLM

### Provider Flexibility
- **No Code Changes**: Switch providers via environment variables
- **Unified Interface**: Same API regardless of provider
- **Easy Extension**: Add new providers by implementing the `LLMService` interface

## Example Output

```json
{
  "title": "Senior Software Engineer",
  "company": "Tech Corp Inc.",
  "description": "We are looking for a Senior Software Engineer...",
  "requirements": [
    "5+ years of software development experience",
    "Bachelor's degree in Computer Science",
    "Experience with cloud platforms"
  ],
  "skills": ["Python", "JavaScript", "React", "AWS", "Docker"],
  "experience_level": "Senior Level",
  "location": "San Francisco, CA",
  "salary_range": "$120,000 - $160,000"
}
```

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Ensure environment variables are set correctly
   - Check API key validity

2. **Import Errors**
   - Install required packages for your chosen provider
   - Check Python environment

3. **Parsing Failures**
   - System automatically falls back to rule-based parsing
   - Check server logs for detailed error messages

### Debug Endpoints

Use `/api/jobs/llm-config` to check your configuration status.

## Future Enhancements

- Support for more LLM providers (Anthropic Claude, local models)
- Custom prompt templates
- Batch processing capabilities
- Advanced error recovery
- Performance optimization
