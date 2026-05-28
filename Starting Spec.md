## **Block 1 — Research Ideation & Distillation System Specification** 

## **1. Purpose** 

Block 1 is a dual-phase semantic planning system designed for research-driven workflows. 

Its purpose is to transform: 

- raw voice/text ideation into: 

- structured evolving specifications for downstream coding agents and experimentation systems. 

The system supports: 

- exploratory thinking 

- hypothesis generation 

- conceptual planning 

- ambiguity management 

- structured consolidation 

The system does NOT perform: 

- code execution 

- autonomous implementation planning 

- orchestration 

- scheduling 

- direct implementation 

The system IS: 

a semantic planning and specification engine that sits between research ideation and downstream execution systems. 

## **2. Core Design Philosophy** 

The architecture separates: 

1 

## **A. Exploration (Creative Mode)** 

High-entropy thinking: 

- uncertainty • divergence • competing ideas 

- speculative reasoning 

- conceptual experimentation 

from: 

## **B. Consolidation (Distillation Mode)** 

Low-entropy structuring: 

- requirement extraction 

- conceptual stabilisation 

- ambiguity reduction 

- downstream preparation 

This separation is critical. 

Premature convergence destroys creativity. 

Lack of consolidation prevents execution. 

## **3. High-Level Architecture** 

```
Voice Input
  ↓
Whisper (local transcription)
  ↓
Transcript Buffer
  ↓
Mode Selector
   ├── Creative Mode
   └── Distillation Mode
  ↓
Semantic Processing Engine (LLM)
  ↓
Living Markdown Specification
```

2 

```
  ↓
Human Interaction Loop
```

## **4. Core Components** 

## **4.1 Whisper Layer** 

## **Purpose** 

Convert spoken input into text. 

## **Notes** 

- Hosted locally (DGX Spark) 

- Independent from Block 1 logic 

- Treated purely as an input adapter 

- No semantic reasoning occurs here 

## **Output** 

```
raw transcript chunk
```

## **4.2 Transcript Buffer** 

## **Purpose** 

Maintain ordered conversational and ideation history. 

## **Responsibilities** 

- append transcript chunks 

- preserve chronological interaction history 

- provide contextual continuity to semantic engine 

## **Notes** 

The transcript buffer is external state. 

3 

The LLM itself is stateless. 

## **4.3 Living Markdown Specification** 

## **Purpose** 

The canonical structured artefact representing current intent. 

This is the primary output of Block 1. 

## **Structure** 

```
## Objective
## Context
## Ideas
## Hypotheses
## Constraints
## Assumptions
## Requirements
## Conceptual Plan
## Open Questions
```

## **4.4 Semantic Processing Engine** 

## **Purpose** 

Transform: 

- transcript history 

- existing specification 

- optional contextual grounding 

4 

into: 

- updated structured semantic state 

## **Critical Architectural Principle** 

The LLM is NOT the system. 

The LLM is: 

a semantic transformation function operating over explicit external state. 

## **5. Creative Mode (High Entropy)** 

## **Purpose** 

Enable exploratory research thinking without premature convergence. 

## **Behaviour** 

Allowed: 

- divergent thinking 

- multiple competing ideas 

- contradictions 

- speculative hypotheses 

- open-ended questioning 

- reframing 

- alternative generation 

- conceptual expansion 

Encouraged: 

- uncertainty 

- incomplete thoughts 

- conceptual experimentation 

## **Creative Interaction** 

The system may: 

- ask exploratory questions 

5 

- suggest multiple alternative directions 

- propose hypotheses 

- reframe concepts 

- expand possibility space 

The system MUST NOT: 

- force convergence 

- prematurely finalise structure 

- commit to implementation decisions 

## **Creative Mode Output Targets** 

Creative outputs populate: 

```
## Ideas
## Hypotheses
## Open Questions
```

## **6. Distillation Mode (Low Entropy)** 

## **Purpose** 

Convert exploratory thinking into stable structured specifications suitable for downstream execution systems. 

## **Behaviour** 

The system: 

- merges transcript history into structured state 

- extracts requirements 

- stabilises constraints 

- resolves contradictions where appropriate 

- reduces ambiguity carefully 

6 

## **Distillation Rules** 

The system MUST: 

- preserve stable structure 

- perform incremental updates 

- maintain semantic consistency 

- preserve valid existing information unless contradicted 

- explicitly surface unresolved ambiguity 

The system MUST NOT: 

- invent new goals 

- autonomously select architectures 

- generate executable plans 

- decide implementation details without user approval 

## **Distillation Interaction** 

Allowed: 

- clarification questions 

- bounded option proposals 

- ambiguity resolution requests 

Goal: 

compress uncertainty into stable structure. 

## **7. Interaction Layer** 

The system is interactive in both modes. 

## **7.1 Creative Interaction** 

Optimises for: 

- exploration 

- expansion 

- hypothesis generation 

7 

Interaction style: 

- open-ended • speculative 

- divergent 

## **7.2 Distillation Interaction** 

Optimises for: 

- precision 

- structure 

- convergence 

Interaction style: 

- constrained 

- targeted • ambiguity-reducing 

## **8. Mode Switching** 

## **8.1 Creative → Distillation** 

Triggered by phrases such as: 

- “distil this” 

- “convert to spec” 

- “finalise” 

- “prepare for coding agent” 

## **8.2 Distillation → Creative** 

Triggered by phrases such as: 

- “brainstorm” 

- “explore” 

- “what are alternatives” 

8 

• “expand possibilities” 

## **9. State Management** 

## **Critical Principle** 

The API/LLM is stateless. 

Conversation continuity is implemented externally. 

The system itself owns: 

- transcript history 

- specification state 

- mode state 

- optional graph context 

## **Recommended State Object** 

```
{
```

```
"transcript_buffer":[],
""
"current_spec_markdown":,
"mode":"creative | distillation",
"codebase_graph":{},
"metadata":{}
}
```

## **Mental Model** 

The system behaves as: 

```
next_state = f(previous_state, new_input)
```

The model performs: 

- semantic transformation 

9 

The system itself performs: 

- state persistence 

- interaction management 

- orchestration 

## **10. Optional Codebase Graph Injection** 

## **Purpose** 

Provide structural grounding from an existing codebase. 

Useful when: 

- ideation depends on current architecture 

- proposed changes interact with existing systems 

- planning requires awareness of implementation structure 

## **Important Constraint** 

The graph is: 

- optional 

- passive 

- read-only 

It is NOT: 

- an autonomous retrieval system 

- an execution planner 

- a mutable knowledge base 

## **Usage Rule** 

Codebase graph injection occurs ONLY: 

- when explicitly enabled 

- typically during Distillation Mode 

10 

## **Example Graph Schema** 

```
{
"modules":[
{
"name":"string",
"summary":"string"
}
],
"files":[
{
"path":"string",
"summary":"string",
"functions":["string"]
}
],
"edges":[
{
"from":"string",
"to":"string",
"type":"depends_on | calls | imports"
}
]
}
```

## **11. Output Contracts** 

## **11.1 Creative Mode Output** 

Outputs: 

- exploratory notes • hypotheses • questions 

- conceptual branches 

Stored in: 

- Ideas • Hypotheses 

- Open Questions 

11 

No structural finalisation occurs. 

## **11.2 Distillation Mode Output** 

Outputs: 

• single updated Markdown specification 

No: 

- execution logic 

- implementation code 

- orchestration plans 

## **12. Failure Handling** 

## **12.1 Creative Mode** 

Ambiguity is allowed and encouraged. 

The system should: 

- expand uncertainty 

- explore alternatives 

- preserve divergent thinking 

## **12.2 Distillation Mode** 

If ambiguity exists: 

- place ambiguity into: 

- Open Questions 

- do NOT hallucinate requirements 

- do NOT infer hidden intent 

12 

## **13. System Invariants** 

The following invariants must always hold: 

- The Markdown spec is the single source of truth 

- All updates are incremental unless explicitly reset 

- The LLM is stateless 

- The system owns state externally 

- No autonomous decision-making occurs 

- No execution planning occurs 

- Exploration and consolidation remain separated 

## **14. Unit Tests** 

## **14.1 Incremental Update Preservation** 

Input: 

- existing spec 

- unrelated transcript update 

Expected: 

- unrelated sections unchanged 

## **14.2 No Full Regeneration** 

Input: 

- small requirement modification 

Expected: 

- localised update only 

- stable structure preserved 

13 

## **14.3 Contradiction Handling** 

Input: 

- conflicting objective 

Expected: 

• explicit overwrite or contradiction note 

## **14.4 Ambiguity Handling** 

Input: 

- vague or incomplete statement 

Expected: 

• ambiguity placed into Open Questions 

## **14.5 Creative Divergence Preservation** 

Input: 

- multiple conflicting ideas 

Expected: 

• all ideas preserved during Creative Mode 

## **14.6 Distillation Convergence** 

Input: 

- exploratory transcript + distillation trigger 

Expected: 

- structured consolidated spec 

14 

## **14.7 Grounded Mode Injection** 

Input: 

- codebase graph enabled 

Expected: 

- graph influences semantic context only 

## **14.8 Structural Integrity** 

Output must always contain: 

```
## Objective
## Context
## Constraints
## Requirements
## Conceptual Plan
## Open Questions
```

## **15. Final Definition** 

Block 1 is: 

a dual-phase semantic planning system that transforms exploratory research thinking into structured executable specifications while preserving separation between creative exploration and downstream consolidation. 

15 

