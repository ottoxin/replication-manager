from __future__ import annotations

from .models import AgentRecord, SkillRecord


AGENT_ROLES = {
    "Coordinator": "Plans the next skill and builds the shared replication state.",
    "Executor": "Prepares the runtime, runs scripts, and diagnoses execution blockers.",
    "Reporter": "Compares outputs to the paper and compiles the submission-facing report.",
}


def build_agent_trace(
    *,
    skill_trace: list[SkillRecord],
    diagnostic_notes: list[str],
) -> list[AgentRecord]:
    grouped: dict[str, list[SkillRecord]] = {}
    order: list[str] = []
    for skill in skill_trace:
        if skill.agent not in grouped:
            grouped[skill.agent] = []
            order.append(skill.agent)
        grouped[skill.agent].append(skill)

    records: list[AgentRecord] = []
    for agent in order:
        skills = grouped[agent]
        records.append(
            AgentRecord(
                name=agent,
                role=AGENT_ROLES.get(agent, "Workflow agent"),
                phase=collapse_phases(skills),
                status=aggregate_status(skills),
                summary=agent_summary(agent, skills, diagnostic_notes),
                artifact_paths=collect_artifacts(skills),
            )
        )
    return records


def collapse_phases(skills: list[SkillRecord]) -> str:
    phases = [skill.phase for skill in skills]
    unique = list(dict.fromkeys(phases))
    if not unique:
        return "Phase A-C"
    if len(unique) == 1:
        return unique[0]
    return f"{unique[0]}-{unique[-1]}"


def aggregate_status(skills: list[SkillRecord]) -> str:
    statuses = {skill.status for skill in skills}
    if "failed" in statuses:
        return "failed"
    if "blocked" in statuses:
        return "blocked"
    if statuses == {"skipped"}:
        return "skipped"
    return "success"


def agent_summary(agent: str, skills: list[SkillRecord], diagnostic_notes: list[str]) -> str:
    snippets = [skill.summary.rstrip(".") for skill in skills[:3]]
    if len(skills) > 3:
        snippets.append(f"plus {len(skills) - 3} more skill(s)")
    summary = "; ".join(snippets).strip()
    if agent == "Executor" and diagnostic_notes:
        summary = f"{summary}; captured {len(diagnostic_notes)} diagnostic note(s)"
    return summary + "."


def collect_artifacts(skills: list[SkillRecord]) -> list[str]:
    artifacts: list[str] = []
    seen: set[str] = set()
    for skill in skills:
        for path in skill.artifact_paths:
            if path in seen:
                continue
            seen.add(path)
            artifacts.append(path)
    return artifacts
