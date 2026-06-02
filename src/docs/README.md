# Documentation Guide

Welcome to the Block 1 system documentation. This folder contains comprehensive guides designed for understanding, modifying, and extending the codebase.

## For Different Audiences

### I want to understand how the system works
Start here:
1. [ARCHITECTURE.md](ARCHITECTURE.md) - System design and components
2. [DATA_MODELS.md](DATA_MODELS.md) - Data structures and formats
3. [WORKFLOWS.md](WORKFLOWS.md) - End-to-end examples

### I need to modify or extend the code
Use these in order:
1. [ARCHITECTURE.md](ARCHITECTURE.md) - Understand current design
2. [DATA_MODELS.md](DATA_MODELS.md) - Know what data you're working with
3. [SERVICES.md](SERVICES.md) - How components interact
4. [SCRIPTS.md](SCRIPTS.md) - What each file does
5. [API_SPEC.md](API_SPEC.md) - If modifying endpoints

### I'm setting up a more powerful agent to modify the codebase
Use the complete set:
1. [ARCHITECTURE.md](ARCHITECTURE.md) - System design
2. [DATA_MODELS.md](DATA_MODELS.md) - Data contracts
3. [SCRIPTS.md](SCRIPTS.md) - Script purposes
4. [API_SPEC.md](API_SPEC.md) - API contract
5. [SERVICES.md](SERVICES.md) - Service interactions
6. [WORKFLOWS.md](WORKFLOWS.md) - Complete scenarios

These documents provide clear contracts and expectations that agents can understand and follow.

### I'm implementing a new feature
1. Check [SERVICES.md](SERVICES.md) for where it fits
2. Review [DATA_MODELS.md](DATA_MODELS.md) for required data structures
3. See [WORKFLOWS.md](WORKFLOWS.md) for similar features
4. Update [API_SPEC.md](API_SPEC.md) if adding endpoints

## Document Structure

### ARCHITECTURE.md
**What**: System design and component overview
**Contains**:
- System overview and principles
- Architecture diagram
- Component responsibilities
- Data flow patterns
- File organization
- Configuration
- Deployment modes
- Performance targets
- Security considerations
- Error handling

**Use when**: You need to understand the big picture or add a new component

### DATA_MODELS.md
**What**: All data structures and their expected formats
**Contains**:
- Core system models (Mode, TranscriptChunk, SystemState, etc.)
- API request/response models
- File formats (JSON, Markdown)
- Service integration points
- Data validation rules

**Use when**: You're reading/writing data or creating new data structures

### SCRIPTS.md
**What**: Purpose and expected output of each Python script
**Contains**:
- What each script does
- How to invoke it
- Expected console output
- Files it creates/modifies
- Example commands
- Summary table

**Use when**: You're running scripts or understanding what output to expect

### API_SPEC.md
**What**: Complete REST API specification
**Contains**:
- All endpoints (health, data, processing, progress)
- Request formats
- Response formats
- Error responses
- Status codes
- cURL examples
- Python examples
- Rate limiting notes
- Authentication (planned)
- Future enhancements

**Use when**: You're building a client or modifying endpoints

### SERVICES.md
**What**: How services interact with each other
**Contains**:
- Service dependency graph
- Component interactions
- Data flow scenarios
- Error handling flow
- Service lifetimes
- Consistency & race conditions
- Performance characteristics
- Concurrency limits
- Future enhancement points

**Use when**: You're adding a new service or fixing inter-component bugs

### WORKFLOWS.md
**What**: Complete end-to-end workflows
**Contains**:
- Phone recording auto-processing (detailed breakdown)
- Laptop API upload workflow
- Interactive CLI usage
- Remote client access
- Error recovery scenarios
- Batch processing
- Mode switching
- Decision trees

**Use when**: You want to understand what a real user sees or test an integration

## How to Use These Documents

### Reading the Code

**Workflow**:
1. Identify what you need to understand
2. Find relevant section in documentation
3. Read the "what" and "how" sections
4. Look at example code/commands
5. Navigate to actual code files

**Example**: "What does FileWatcher do?"
```
1. Search for "FileWatcher" in SCRIPTS.md
2. Read purpose and what it does
3. Check SERVICES.md for how it interacts with other components
4. Look at src/file_watcher.py with documentation as guide
```

### Modifying Code

**Workflow**:
1. Understand current design (ARCHITECTURE.md)
2. Identify which data structures change (DATA_MODELS.md)
3. Check service interactions (SERVICES.md)
4. Review affected workflows (WORKFLOWS.md)
5. Plan your changes
6. Implement
7. Update documentation if contracts changed

**Example**: "I want to add retry logic for transcription failures"
```
1. Read SERVICES.md → TranscriptionService section
2. Check WORKFLOWS.md → Workflow 5 (Error Recovery)
3. Understand current failure handling
4. Modify src/transcription_service.py
5. Update DATA_MODELS.md if task structure changes
6. Update SERVICES.md with new retry flow
7. Update WORKFLOWS.md with new error handling scenario
```

### Using with Agents

These documents are designed for AI agents to:
1. Understand the system thoroughly
2. Know what outputs to expect
3. Understand data structures and contracts
4. See complete workflows (real vs edge cases)
5. Make informed modifications

**Agent Prompt Template**:
```
You are modifying the Block 1 system. Read these documents first:
- ARCHITECTURE.md (understand design)
- DATA_MODELS.md (understand data structures)
- SCRIPTS.md (understand what each file does)
- SERVICES.md (understand interactions)
- API_SPEC.md (if modifying APIs)
- WORKFLOWS.md (understand real workflows)

Your task: [specific modification]

Constraints:
- Follow the existing patterns shown in SERVICES.md
- Maintain the data structure contracts in DATA_MODELS.md
- Don't break the workflows in WORKFLOWS.md
- Update documentation if you change any contracts
```

## Updating These Documents

### When to Update

- [ ] Adding a new endpoint → Update API_SPEC.md
- [ ] Adding a new service → Update SERVICES.md, ARCHITECTURE.md
- [ ] Changing data models → Update DATA_MODELS.md
- [ ] Changing a workflow → Update WORKFLOWS.md
- [ ] Creating a new script → Update SCRIPTS.md
- [ ] Major architectural change → Update ARCHITECTURE.md

### How to Update

1. **Identify what changed**: Which document(s) are affected?
2. **Update the document**: Add/modify the relevant section
3. **Check for consistency**: Does the change affect other sections?
4. **Test understanding**: Can you explain the change to someone else?
5. **Commit**: "Docs: describe what changed"

### Example: Adding a new endpoint

**File**: `API_SPEC.md`

**Addition**: New section under appropriate heading
```markdown
### POST /my-new-endpoint

**Purpose**: Brief description

**Request**:
```http
POST /my-new-endpoint HTTP/1.1
...
```

**Response** (200 OK):
```json
{
  "field": "value"
}
```

**Use Case**: When you'd use this

**cURL Example**:
```bash
curl -X POST http://dgx:8001/my-new-endpoint
```
```

**Also update**:
- SERVICES.md if it calls other services
- WORKFLOWS.md if it affects any workflows
- ARCHITECTURE.md if it's a significant addition

## Document Format

All documents use:
- **Markdown** for structure and formatting
- **Code blocks** with language (bash, python, json, http)
- **Clear headings** for easy navigation
- **Examples** showing real usage
- **Tables** for structured data
- **Diagrams** using ASCII art
- **Links** to related sections
- **Consistent terminology** across docs

## Key Concepts to Understand

### Atomic Operations
State changes use temp file + rename to prevent corruption.
See: ARCHITECTURE.md, SERVICES.md

### Task Tracking
Every recording gets a task_id that tracks it through the pipeline.
See: DATA_MODELS.md, WORKFLOWS.md

### Hybrid Processing
Try Claude API first, fall back to DGX LLM.
See: SERVICES.md → SemanticEngine

### Mode Switching
System can be in CREATIVE or DISTILLATION mode.
See: WORKFLOWS.md → Workflow 7

### OneDrive as Hub
All devices upload to same OneDrive folder.
See: ARCHITECTURE.md, WORKFLOWS.md → Workflow 1

## Contact & Updates

These documents should stay synchronized with the code. If you notice:
- Documentation is out of date → Update it
- Documentation is unclear → Clarify it
- Code doesn't match docs → Align them
- Missing documentation → Add it

The goal is that agents reading these docs can understand and modify the system without reading raw code.

## Related Resources

- **README.md** (root): User-facing documentation
- **DATA_TRANSFER_ARCHITECTURE.md** (root): Data transfer specifically
- **Starting Spec.md** (root): Original system specification
- **Source code**: `../src/` - The actual implementation

---

**Last Updated**: 2026-06-02
**Documentation Version**: 1.0
**Code Version**: Matches current src/ directory
