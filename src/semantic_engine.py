"""Semantic processing engine with Claude primary + DGX fallback."""

import os
import re
from typing import Optional, Tuple
from anthropic import Anthropic
from openai import OpenAI


class SemanticEngine:
    """
    Transforms transcripts + specs into updated specs using semantic LLM.
    Primary: Claude API (better reasoning for mode discipline)
    Fallback: self-hosted LLM on DGX (when Claude unavailable/rate-limited)
    """

    def __init__(
        self,
        dgx_base_url: Optional[str] = None,
        dgx_api_key: str = "dummy-key",
        dgx_model: str = "your-model",
        dgx_timeout: int = 30,
        claude_api_key: Optional[str] = None,
        claude_model: str = "claude-3-5-haiku-20241022",
        claude_timeout: int = 60,
    ):
        """
        Initialize semantic engine.

        Args:
            dgx_base_url: Base URL for DGX vLLM API (e.g., http://localhost:8000)
            dgx_api_key: API key for DGX
            dgx_model: Model name on DGX
            dgx_timeout: Timeout for DGX requests (seconds)
            claude_api_key: Anthropic API key (optional, loaded from env if not provided)
            claude_model: Claude model to use (default: cheap Haiku)
            claude_timeout: Timeout for Claude requests (seconds)
        """
        self.dgx_base_url = dgx_base_url or os.getenv("DGX_BASE_URL", "http://localhost:8000")
        self.dgx_api_key = dgx_api_key or os.getenv("DGX_API_KEY", "dummy-key")
        self.dgx_model = dgx_model or os.getenv("SEMANTIC_LLM_MODEL", "your-model")
        self.dgx_timeout = dgx_timeout

        self.claude_api_key = claude_api_key or os.getenv("CLAUDE_API_KEY")
        self.claude_model = claude_model or os.getenv("CLAUDE_MODEL", "claude-3-5-haiku-20241022")
        self.claude_timeout = claude_timeout

        # Initialize clients
        self.dgx_client = OpenAI(api_key=self.dgx_api_key, base_url=self.dgx_base_url)
        self.claude_client = Anthropic(api_key=self.claude_api_key) if self.claude_api_key else None

    def process_transcript(
        self,
        mode: str,
        transcript_text: str,
        current_spec: str,
        transcript_history: str = "",
    ) -> Tuple[str, str]:
        """
        Process transcript and return updated spec.

        Args:
            mode: "creative" or "distillation"
            transcript_text: New transcript chunk to process
            current_spec: Current markdown spec
            transcript_history: Full transcript history for context

        Returns:
            Tuple of (updated_spec, backend_used): where backend_used is "claude" or "dgx"
        """
        prompt = self._build_prompt(mode, transcript_text, current_spec, transcript_history)

        # Try Claude first (primary)
        if self.claude_client:
            response = self._try_claude(prompt)
            if response:
                updated_spec = self._extract_spec_from_response(response, current_spec)
                return updated_spec, "claude"

        # Fallback to DGX
        response = self._try_dgx(prompt)
        if response:
            updated_spec = self._extract_spec_from_response(response, current_spec)
            return updated_spec, "dgx"

        # Both failed
        print("Warning: Both Claude and DGX failed. Returning unchanged spec.")
        return current_spec, "none"

    def _try_claude(self, prompt: str) -> Optional[str]:
        """Try to process with Claude API (primary)."""
        try:
            if not self.claude_client:
                return None
            
            message = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
                timeout=self.claude_timeout,
            )
            return message.content[0].text
        except Exception as e:
            print(f"Claude failed ({type(e).__name__}: {e}), falling back to DGX...")
            return None

    def _try_dgx(self, prompt: str) -> Optional[str]:
        """Try to process with DGX LLM (fallback)."""
        try:
            response = self.dgx_client.chat.completions.create(
                model=self.dgx_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2048,
                timeout=self.dgx_timeout,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"DGX failed ({type(e).__name__}: {e})")
            return None

    def _build_prompt(
        self, mode: str, transcript_text: str, current_spec: str, transcript_history: str
    ) -> str:
        """Build mode-specific prompt for semantic processing."""
        if mode == "creative":
            return self._build_creative_prompt(transcript_text, current_spec, transcript_history)
        else:
            return self._build_distillation_prompt(transcript_text, current_spec, transcript_history)

    def _build_creative_prompt(
        self, transcript_text: str, current_spec: str, transcript_history: str
    ) -> str:
        """Build prompt for Creative Mode (divergence, exploration)."""
        return f"""You are a research ideation assistant in CREATIVE MODE.

Your role: Transform new voice-to-text transcript into exploratory thinking updates.

BEHAVIOR:
- Preserve existing structure in the spec
- Encourage divergence: multiple ideas, contradictions, uncertainty
- Populate: Ideas, Hypotheses, Open Questions
- Do NOT force convergence or premature structure
- Do NOT invent goals or decide architectures

CURRENT SPEC:
```markdown
{current_spec}
```

TRANSCRIPT HISTORY (for context):
{transcript_history or "(empty)"}

NEW TRANSCRIPT:
{transcript_text}

OUTPUT FORMAT:
Return ONLY markdown content. Update sections with ## header markers.
For changed sections, output the full section header and new content.
Example format:

## Ideas
- New idea from transcript: ...
- Existing idea: ...

## Hypotheses
...

## Open Questions
...

(only output sections that changed)

Remember: Divergence is good. Contradictions are allowed. Uncertainty is encouraged.
"""

    def _build_distillation_prompt(
        self, transcript_text: str, current_spec: str, transcript_history: str
    ) -> str:
        """Build prompt for Distillation Mode (convergence, structure)."""
        return f"""You are a research specification consolidator in DISTILLATION MODE.

Your role: Convert exploratory thinking into stable, structured specifications.

BEHAVIOR:
- Merge transcript into the spec structure
- Extract concrete requirements
- Stabilize constraints
- Resolve contradictions where safe
- Reduce ambiguity carefully
- PRESERVE existing valid information unless contradicted
- Do NOT invent new goals
- Do NOT select architectures autonomously
- Do NOT generate executable plans

CURRENT SPEC:
```markdown
{current_spec}
```

TRANSCRIPT HISTORY (for context):
{transcript_history or "(empty)"}

NEW TRANSCRIPT:
{transcript_text}

OUTPUT FORMAT:
Return ONLY markdown content. Update sections with ## header markers.
For changed sections, output the full section header and new content.
Example format:

## Objective
Clear, derived from transcript...

## Requirements
- Req 1: ...
- Req 2: ...

## Constraints
- Constraint 1: ...

## Open Questions
- Unresolved: ...

(only output sections that changed)

Remember: Compress uncertainty into stable structure. Preserve existing valid information.
"""

    def _extract_spec_from_response(self, response: str, current_spec: str) -> str:
        """
        Parse LLM response and apply markdown section diffs to current spec.

        Strategy: Extract ## Section headers and content, merge into current spec.
        """
        # Parse response into section updates
        section_pattern = r"^## (.+)$"
        lines = response.split("\n")

        sections = {}
        current_section = None
        current_content = []

        for line in lines:
            match = re.match(section_pattern, line)
            if match:
                # Save previous section
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                
                # Start new section
                current_section = match.group(1).strip()
                current_content = []
            else:
                if current_section:
                    current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        # Apply sections to current spec
        updated_spec = current_spec
        for section_header, content in sections.items():
            updated_spec = self._update_spec_section(updated_spec, section_header, content)

        return updated_spec

    @staticmethod
    def _update_spec_section(spec: str, section_header: str, new_content: str) -> str:
        """Update a single section in markdown spec."""
        section_marker = f"## {section_header}"
        lines = spec.split("\n")

        section_start = None
        section_end = None

        # Find section bounds
        for i, line in enumerate(lines):
            if line.strip().startswith(section_marker):
                section_start = i
                # Find next section or end
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().startswith("##"):
                        section_end = j
                        break
                if section_end is None:
                    section_end = len(lines)
                break

        if section_start is not None:
            # Replace section content
            new_lines = (
                lines[:section_start + 1] +
                [""] +
                new_content.split("\n") +
                [""] +
                lines[section_end:]
            )
            return "\n".join(new_lines)
        else:
            # Section doesn't exist, append it
            return spec + f"\n\n{section_marker}\n\n{new_content}\n"
