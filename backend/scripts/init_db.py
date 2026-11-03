"""
数据库初始化脚本
----------------
1. 使用项目根目录「数据库连接字符串/数据库连接字符串.js」中的配置连接 MySQL
2. 若目标库不存在则创建（utf8mb4）
3. 执行「数据库设计和说明/建表语句.sql」
4. 执行扩展表脚本（业务补充表 biz_customer / biz_vehicle）
5. 校验表数量与种子数据

用法：
    python scripts/init_db.py            # 建库 + 建表 + 种子数据
    python scripts/init_db.py --check    # 仅校验
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import pymysql

BASE_DIR = Path(__file__).resolve().parents[2]  # 项目根目录
CONFIG_FILE = BASE_DIR / "数据库连接字符串" / "数据库连接字符串.js"
SQL_FILE = BASE_DIR / "数据库设计和说明" / "建表语句.sql"
EXT_SQL_FILE = BASE_DIR / "backend" / "scripts" / "extension_business.sql"


def load_config() -> dict:
    """解析 JS 对象形式的连接配置（JSON5 宽松解析）。"""
    text = CONFIG_FILE.read_text(encoding="utf-8")
    cfg: dict = {}
    for key in ("host", "port", "user", "password", "database", "charset"):
        m = re.search(rf'["\']?{key}["\']?\s*:\s*["\']([^"\']*)["\']', text)
        if not m:
            m = re.search(rf'["\']?{key}["\']?\s*:\s*(\d+)', text)
        if m:
            value = m.group(1)
            cfg[key] = int(value) if key == "port" else value
    if not cfg.get("host") or not cfg.get("database"):
        raise RuntimeError("连接配置解析失败，请检查 数据库连接字符串.js")
    return cfg


def split_sql(sql: str) -> list[str]:
    """按分号拆分 SQL，忽略字符串与注释中的分号。"""
    statements: list[str] = []
    buf: list[str] = []
    i, n = 0, len(sql)
    quote: str | None = None
    in_line_comment = False
    in_block_comment = False

    while i < n:
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ""

        if in_line_comment:
            buf.append(ch)
            if ch == "\n":
                in_line_comment = False
            i += 1
            continue
        if in_block_comment:
            buf.append(ch)
            if ch == "*" and nxt == "/":
                buf.append(nxt)
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue

        if quote:
            buf.append(ch)
            if ch == "\\":
                if nxt:
                    buf.append(nxt)
                i += 2
                continue
            if ch == quote:
                if nxt == quote:  # 转义引号
                    buf.append(nxt)
                    i += 2
                    continue
                quote = None
            i += 1
            continue

        if ch in ("'", '"', "`"):
            quote = ch
            buf.append(ch)
            i += 1
            continue
        if ch == "-" and nxt == "-":
            in_line_comment = True
            buf.append(ch)
            i += 1
            continue
        if ch == "#":
            in_line_comment = True
            buf.append(ch)
            i += 1
            continue
        if ch == "/" and nxt == "*":
            in_block_comment = True
            buf.append(ch)
            buf.append(nxt)
            i += 2
            continue
        if ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def execute_file(cursor, path: Path, label: str) -> None:
    if not path.exists():
        print(f"[SKIP] {label} 不存在：{path}")
        return
    statements = split_sql(path.read_text(encoding="utf-8"))
    ok = 0
    for idx, stmt in enumerate(statements, 1):
        if not stmt or stmt.upper() in ("SET NAMES UTF8MB4",):
            continue
        try:
            cursor.execute(stmt)
            ok += 1
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"{label} 第 {idx} 条语句执行失败：\n{stmt[:300]}\n{exc}") from exc
    print(f"[OK] {label}：执行 {ok} 条语句")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="仅校验")
    args = parser.parse_args()

    cfg = load_config()
    db = cfg["database"]
    print(f"目标数据库：{cfg['host']}:{cfg['port']} / {db}")

    conn = pymysql.connect(
        host=cfg["host"], port=cfg["port"], user=cfg["user"], password=cfg["password"],
        charset=cfg.get("charset", "utf8mb4"), autocommit=True, connect_timeout=15,
    )
    try:
        with conn.cursor() as cur:
            if not args.check:
                cur.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{db}` DEFAULT CHARACTER SET utf8mb4 "
                    f"COLLATE utf8mb4_general_ci"
                )
                print(f"[OK] 数据库已就绪：{db}")
    finally:
        conn.close()

    conn = pymysql.connect(
        host=cfg["host"], port=cfg["port"], user=cfg["user"], password=cfg["password"],
        database=db, charset=cfg.get("charset", "utf8mb4"), autocommit=True, connect_timeout=15,
    )
    try:
        with conn.cursor() as cur:
            if not args.check:
                execute_file(cur, SQL_FILE, "建表语句.sql")
                execute_file(cur, EXT_SQL_FILE, "扩展业务表")

            cur.execute("SHOW TABLES")
            tables = [row[0] for row in cur.fetchall()]
            print(f"\n共 {len(tables)} 张表：")
            for t in tables:
                cur.execute(f"SELECT COUNT(*) FROM `{t}`")
                print(f"  - {t:<24} {cur.fetchone()[0]:>6} 行")

            cur.execute(
                "SELECT u.username, t.tenant_name, r.role_code "
                "FROM sys_user u "
                "JOIN sys_user_tenant ut ON ut.user_id = u.user_id "
                "JOIN sys_tenant t ON t.tenant_id = ut.tenant_id "
                "LEFT JOIN sys_user_tenant_role r ON r.user_id = u.user_id AND r.tenant_id = ut.tenant_id"
            )
            print("\n账号信息：")
            for row in cur.fetchall():
                print(f"  {row[0]} / {row[1]} / {row[2]}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
