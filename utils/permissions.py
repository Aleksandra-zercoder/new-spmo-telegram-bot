from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Access:
    admin_ids: set[int]

    def is_admin(self, user_id: int | None) -> bool:
        return user_id is not None and user_id in self.admin_ids
