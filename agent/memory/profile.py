"""User profile — structured user attributes with confidence tracking."""

from datetime import datetime

from agent.models.memory import UserProfileData


class UserProfile:
    """Structured user profile with per-field confidence scores."""

    def __init__(self) -> None:
        self._data: UserProfileData = UserProfileData()

    def get(self, key: str) -> object:
        if hasattr(self._data, key):
            return getattr(self._data, key)
        return None

    def set(self, key: str, value: str | float, confidence: float = 0.5) -> bool:
        if not hasattr(self._data, key):
            return False
        clamped = max(0.0, min(1.0, confidence))
        confidence_scores = dict(self._data.confidence_scores)
        confidence_scores[key] = clamped
        self._data = self._data.model_copy(
            update={
                key: value,
                "confidence_scores": confidence_scores,
                "last_updated": datetime.now(),
            }
        )
        return True

    def add_to_array(self, field: str, value: str) -> bool:
        current = getattr(self._data, field, None)
        if not isinstance(current, list):
            return False
        if value in current:
            return True
        new_list = [*current, value]
        self._data = self._data.model_copy(update={field: new_list, "last_updated": datetime.now()})
        return True

    def remove_from_array(self, field: str, value: str) -> bool:
        current = getattr(self._data, field, None)
        if not isinstance(current, list):
            return False
        if value not in current:
            return False
        new_list = [v for v in current if v != value]
        self._data = self._data.model_copy(update={field: new_list, "last_updated": datetime.now()})
        return True

    def format_for_context(self) -> str:
        d = self._data
        fields: list[tuple[str, str]] = []

        if d.name:
            fields.append(("姓名", d.name))
        if d.preferred_name:
            fields.append(("称呼", d.preferred_name))
        if d.role:
            fields.append(("角色", d.role))
        if d.timezone:
            fields.append(("时区", d.timezone))
        if d.language:
            fields.append(("语言", d.language))
        if d.interests:
            fields.append(("兴趣", ", ".join(d.interests)))
        if d.expertise:
            fields.append(("专长", ", ".join(d.expertise)))
        if d.active_projects:
            fields.append(("当前项目", ", ".join(d.active_projects)))
        if d.common_tools:
            fields.append(("常用工具", ", ".join(d.common_tools)))
        if d.current_focus:
            fields.append(("当前关注", ", ".join(d.current_focus)))
        if d.response_style and len(fields) > 0:
            fields.append(("回复风格", d.response_style))

        if not fields:
            return ""

        lines = ["## 用户画像"]
        for label, value in fields:
            lines.append(f"- **{label}**: {value}")
        return "\n".join(lines)

    def to_data(self) -> UserProfileData:
        return self._data

    def load_data(self, data: UserProfileData) -> None:
        self._data = data

    @property
    def initialized(self) -> bool:
        return self._data.name != "" or len(self._data.interests) > 0
