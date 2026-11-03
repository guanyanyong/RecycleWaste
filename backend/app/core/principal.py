"""登录主体：用户 + 租户 + 角色 + 权限并集。"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Principal:
    user_id: int
    username: str
    real_name: str
    tenant_id: int
    tenant_name: str
    roles: list[str] = field(default_factory=list)
    permissions: set[str] = field(default_factory=set)
    station_scope: list[int] = field(default_factory=list)

    @property
    def is_tenant_admin(self) -> bool:
        return "tenant_admin" in self.roles

    def has_perm(self, perm: str) -> bool:
        # tenant_admin 直接短路，将来新增权限点自动拥有
        return self.is_tenant_admin or perm in self.permissions

    def station_allowed(self, station_id: int) -> bool:
        return not self.station_scope or station_id in self.station_scope
