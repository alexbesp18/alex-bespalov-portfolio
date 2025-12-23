# Prompts Directory

This directory contains all LLM prompt templates used by the analysis pipeline. 
Prompts are stored as Markdown files with YAML frontmatter for easy editing.

## Directory Structure

```
prompts/
├── README.md                    # This file
├── topics/
│   └── extraction.md            # Topic extraction from transcript chunks
├── business/
│   ├── idea_generation.md       # Core 24-hour business idea generation
│   ├── lead_gen.md              # First 100 customers strategy
│   ├── niche_validation.md      # SaaS/AI budget validation
│   └── competitor_check.md      # Competitive landscape analysis
└── investment/
    ├── base_thesis.md           # Core investment thesis extraction
    └── lenses/
        ├── gavin_baker.md       # Growth at reasonable price lens
        ├── jordi_visser.md      # Macro flows and positioning lens
        ├── leopold_aschenbrenner.md  # AI compute scaling lens
        ├── karpathy.md          # Technical AI feasibility lens
        └── dwarkesh.md          # Long-term civilizational lens
```

## Prompt File Format

Each prompt file uses YAML frontmatter for metadata followed by Markdown sections:

```markdown
---
name: Human Readable Name
version: 1.0
parameters:
  - transcript
  - num_ideas
temperature: 0.7
max_tokens: 2000
---
# System Prompt

You are an expert analyst...

# User Prompt

Analyze this transcript:
{transcript}

Generate {num_ideas} ideas.
```

## Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | No | Human-readable name (defaults to filename) |
| `version` | No | Version string for tracking changes |
| `parameters` | No | List of required template parameters (auto-detected if not specified) |
| `temperature` | No | LLM temperature override |
| `max_tokens` | No | Max tokens override |

## Template Parameters

Use `{parameter_name}` syntax for dynamic values:

- `{transcript}` - The full or partial transcript text
- `{num_ideas}` - Number of ideas to generate
- `{time_horizon}` - Investment time horizon
- `{chunk_index}` - Current chunk number
- `{start_time}` - Chunk start timestamp
- `{end_time}` - Chunk end timestamp

Use `{{double_braces}}` for literal braces in JSON examples.

## Creating New Prompts

1. Create a new `.md` file in the appropriate directory
2. Add frontmatter with at minimum the `name` field
3. Write your system prompt under `# System Prompt`
4. Write your user prompt under `# User Prompt`
5. Use `{parameters}` for dynamic content
6. Test with the pipeline

## Best Practices

1. **Be specific**: Clearly define what you want the LLM to extract/generate
2. **Use examples**: Include JSON output format examples with `{{escaped_braces}}`
3. **Quote requirements**: Always require VERBATIM quotes from transcript
4. **Version your prompts**: Increment version when making changes
5. **Test changes**: Run on a sample transcript before production use

## Loading Prompts in Code

```python
from src.prompts import PromptLoader

loader = PromptLoader()
template = loader.load("business/idea_generation.md")

# Format with parameters
system, user = template.format(transcript="...", num_ideas=3)

# List available lenses
lenses = loader.list_lenses()  # ["gavin_baker", "karpathy", ...]
```

