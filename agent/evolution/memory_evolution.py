"""Memory evolution — orchestrate episodic memory decay and reinforcement cycles."""

from agent.memory.episodic import EpisodicMemory


class MemoryEvolution:
    """Orchestrate periodic memory maintenance cycles."""

    def __init__(self, episodic: EpisodicMemory) -> None:
        self._episodic = episodic

    def run_cycle(self) -> int:
        decayed = self._episodic.apply_decay()

        active = self._episodic.get_active_entries()

        # Prune if over capacity (pruning happens on next add, handled by EpisodicMemory)
        # Reinforcement: boost recently accessed entries
        for entry in active:
            if entry.usage_frequency > 0:
                self._episodic.reinforce(entry.id, 0.01 * entry.usage_frequency)

        return decayed
