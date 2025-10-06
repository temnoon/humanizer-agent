# Madhyamaka CLI

Command-line interface for Buddhist philosophy-based language analysis using Nagarjuna's Madhyamaka (Middle Path) philosophy.

## Installation

```bash
cd /Users/tem/humanizer-agent/backend/cli
./install.sh
```

By default, installs to `~/.local/bin/madhyamaka`. Specify custom directory:

```bash
./install.sh /usr/local/bin
```

## Quick Start

```bash
# Health check
madhyamaka health

# Detect eternalism (reification)
madhyamaka detect eternalism "Everyone must always meditate"

# Detect nihilism
madhyamaka detect nihilism "Nothing matters, everything is meaningless"

# Check middle path proximity
madhyamaka detect middle-path-proximity "For some people, meditation can be helpful"

# Transform text toward middle path
madhyamaka transform alternatives "You must always be mindful" --num 5 --stage 2

# Generate contemplative practice
madhyamaka contemplate neti-neti --target self --depth progressive

# Get teachings
madhyamaka teach list
madhyamaka teach situation --extreme nihilism
```

## Command Structure

### Detection Commands

**Detect Eternalism** (reification, absolutist language):
```bash
madhyamaka detect eternalism "text to analyze"
madhyamaka detect eternalism < file.txt
echo "text" | madhyamaka detect eternalism
```

Output: JSON with confidence score, severity, indicators, reified concepts

**Detect Nihilism** (denial of conventional truth):
```bash
madhyamaka detect nihilism "text to analyze"
```

Output: JSON with confidence score, severity, indicators, warnings

**Detect Middle Path Proximity**:
```bash
madhyamaka detect middle-path-proximity "text to analyze"
```

Output: JSON with score (0-1), proximity level (far/approaching/close/very_close)

**Detect Clinging** (attachment to views):
```bash
madhyamaka detect clinging --conversation conversation.json
cat conversation.json | madhyamaka detect clinging
```

Conversation JSON format:
```json
[
  {"role": "user", "content": "message 1"},
  {"role": "assistant", "content": "response 1"},
  {"role": "user", "content": "message 2"}
]
```

### Transformation Commands

**Generate Middle Path Alternatives**:
```bash
madhyamaka transform alternatives "text" --num 5 --stage 3
```

Options:
- `--num N`: Number of alternatives (default: 5)
- `--stage N`: User journey stage 1-5 (default: 1)

**Reveal Dependent Origination**:
```bash
madhyamaka transform dependent-origination "text"
```

Shows how concepts depend on conditions, not inherent essence.

### Contemplative Practice Commands

**Neti Neti** (not this, not that):
```bash
madhyamaka contemplate neti-neti \
  --target self \
  --depth progressive \
  --stage 3
```

Options:
- `--target`: self, thought, emotion, consciousness
- `--depth`: simple, progressive, deep
- `--stage`: 1-5 (user journey stage)

**Two Truths Contemplation**:
```bash
madhyamaka contemplate two-truths --phenomenon anger
```

Holds conventional and ultimate truths simultaneously.

**Dependent Origination Inquiry**:
```bash
madhyamaka contemplate dependent-origination \
  --starting-point self \
  --no-backward \
  --no-forward
```

Options:
- `--starting-point TEXT`: Concept to investigate
- `--no-backward`: Skip backward trace
- `--no-forward`: Skip forward trace

### Teaching Commands

**Get Teaching for Situation**:
```bash
madhyamaka teach situation --extreme nihilism
madhyamaka teach situation --extreme eternalism
madhyamaka teach situation --clinging
```

Returns relevant Nagarjuna quote with explanation.

**List All Teachings**:
```bash
madhyamaka teach list
```

## Input/Output

### Input Formats

**Command-line argument:**
```bash
madhyamaka detect eternalism "text to analyze"
```

**Standard input:**
```bash
echo "text to analyze" | madhyamaka detect eternalism
madhyamaka detect eternalism < file.txt
```

**JSON file:**
```bash
madhyamaka detect clinging --conversation conversation.json
```

### Output Format

All commands output JSON to stdout for easy parsing:

```bash
# Pretty print with jq
madhyamaka detect eternalism "text" | jq

# Extract specific fields
madhyamaka detect eternalism "text" | jq '.confidence'

# Save to file
madhyamaka detect eternalism "text" > result.json
```

## Examples

### Analyze Your Own Writing

```bash
cat my_essay.txt | madhyamaka detect eternalism > analysis.json
```

### Transform Absolutist Claims

```bash
madhyamaka transform alternatives "Everyone needs meditation" --num 3
```

Output:
```json
{
  "original": "Everyone needs meditation",
  "alternatives": [
    {
      "text": "For some people, meditation might benefit from helpful",
      "score": 0.88,
      "type": "conditional_softening"
    }
  ]
}
```

### Generate Daily Practice

```bash
madhyamaka contemplate neti-neti \
  --target thought \
  --depth simple \
  > daily_practice.json

# Format for reading
cat daily_practice.json | jq -r '.instructions.stages[].contemplation'
```

### Conversation Analysis

Create `conversation.json`:
```json
[
  {"role": "user", "content": "I KNOW emptiness is the only truth!"},
  {"role": "assistant", "content": "Tell me more"},
  {"role": "user", "content": "Most people just don't GET IT!"}
]
```

Analyze:
```bash
madhyamaka detect clinging --conversation conversation.json
```

Output shows clinging patterns (defensive assertion, spiritual superiority).

### Batch Processing

```bash
# Analyze multiple texts
for file in essays/*.txt; do
  echo "Analyzing $file..."
  madhyamaka detect middle-path-proximity < "$file" > "analysis_$(basename $file .txt).json"
done

# Get proximity scores
for file in analysis_*.json; do
  score=$(jq -r '.middle_path_score' "$file")
  echo "$file: $score"
done
```

## Philosophy

Based on Nagarjuna's Madhyamaka (Middle Path) Buddhism:

- **Eternalism**: Treating concepts as having inherent, fixed existence (reification)
- **Nihilism**: Denying conventional function, confusing emptiness with nothingness
- **Middle Path**: Neither extreme - things function conventionally while being empty of essence
- **Two Truths**: Conventional (things work) & Ultimate (things are empty) - both valid
- **Dependent Origination**: Meaning arises from conditions, not inherent nature

## Architecture

The CLI is a **pure parameter-passing wrapper** with zero business logic:
- Argument parsing via argparse
- Direct calls to `services.madhyamaka` modules
- JSON input/output only
- No data transformation or interpretation

All functionality resides in:
- `services/madhyamaka/detector.py` - Pattern detection
- `services/madhyamaka/transformer.py` - Language transformation
- `services/madhyamaka/contemplative.py` - Practice generation
- `services/madhyamaka/constants.py` - Teachings database

## Troubleshooting

**Command not found:**
```bash
# Check installation
which madhyamaka

# Check PATH
echo $PATH | grep -o "$HOME/.local/bin"

# Add to PATH if missing
echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.zshrc
source ~/.zshrc
```

**Import errors:**
```bash
# CLI expects backend code at:
# /Users/tem/humanizer-agent/backend

# Update path in madhyamaka_cli.py line 31 if different
```

**Python version:**
```bash
# Requires Python 3.11
python3.11 --version

# Install if missing
brew install python@3.11
```

## API Mapping

CLI command structure mirrors REST API routes:

| CLI | API Endpoint |
|-----|--------------|
| `detect eternalism` | `POST /api/madhyamaka/detect/eternalism` |
| `detect nihilism` | `POST /api/madhyamaka/detect/nihilism` |
| `detect middle-path-proximity` | `POST /api/madhyamaka/detect/middle-path-proximity` |
| `detect clinging` | `POST /api/madhyamaka/detect/clinging` |
| `transform alternatives` | `POST /api/madhyamaka/transform/middle-path-alternatives` |
| `transform dependent-origination` | `POST /api/madhyamaka/transform/dependent-origination` |
| `contemplate neti-neti` | `POST /api/madhyamaka/contemplate/neti-neti` |
| `contemplate two-truths` | `POST /api/madhyamaka/contemplate/two-truths` |
| `contemplate dependent-origination` | `POST /api/madhyamaka/contemplate/dependent-origination` |
| `teach situation` | `POST /api/madhyamaka/teach/situation` |
| `teach list` | `GET /api/madhyamaka/teachings` |
| `health` | `GET /api/madhyamaka/health` |

## License

Part of the Humanizer Agent project.
