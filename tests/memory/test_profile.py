"""Tests for UserProfile."""

from agent.memory.profile import UserProfile


class TestUserProfile:
    def test_set_get(self) -> None:
        up = UserProfile()
        up.set("name", "Alice", 0.8)
        assert up.get("name") == "Alice"

    def test_set_invalid_key(self) -> None:
        up = UserProfile()
        assert not up.set("invalid_key", "value")

    def test_confidence_tracking(self) -> None:
        up = UserProfile()
        up.set("name", "Bob", 0.9)
        assert up.to_data().confidence_scores.get("name") == 0.9

    def test_add_to_array(self) -> None:
        up = UserProfile()
        up.add_to_array("interests", "coding")
        up.add_to_array("interests", "ai")
        assert "coding" in up.to_data().interests
        assert "ai" in up.to_data().interests

    def test_add_duplicate(self) -> None:
        up = UserProfile()
        up.add_to_array("interests", "coding")
        up.add_to_array("interests", "coding")
        assert len(up.to_data().interests) == 1

    def test_remove_from_array(self) -> None:
        up = UserProfile()
        up.add_to_array("interests", "coding")
        up.add_to_array("interests", "ai")
        up.remove_from_array("interests", "coding")
        assert "coding" not in up.to_data().interests
        assert "ai" in up.to_data().interests

    def test_format_for_context(self) -> None:
        up = UserProfile()
        up.set("name", "Alice", 0.8)
        up.add_to_array("interests", "coding")
        ctx = up.format_for_context()
        assert "Alice" in ctx
        assert "coding" in ctx
        assert "用户画像" in ctx

    def test_format_for_context_empty(self) -> None:
        up = UserProfile()
        assert up.format_for_context() == ""

    def test_load_data(self) -> None:
        from agent.models.memory import UserProfileData

        up = UserProfile()
        data = UserProfileData(name="Test", role="dev")
        up.load_data(data)
        assert up.get("name") == "Test"

    def test_initialized(self) -> None:
        up = UserProfile()
        assert not up.initialized
        up.set("name", "Alice", 0.8)
        assert up.initialized
