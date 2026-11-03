"""端到端冒烟测试：登录 → 建行程 → 加货 → 核价 → 皮重 → 结算 → 付款。"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def call(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        payload = json.loads(exc.read().decode())
        raise SystemExit(f"HTTP {exc.code} {path}: {payload}") from exc
    if "code" in payload and payload.get("code") != "OK":
        raise SystemExit(f"业务失败 {path}: {payload}")
    return payload.get("data", payload)


def main() -> int:
    health = call("GET", "/health")
    print("1. 健康检查:", health["status"])

    login = call("POST", "/api/v1/auth/login", {"username": "admin", "password": "admin123"})
    token = login["access_token"]
    print(f"2. 登录成功: {login['user']['real_name']} / 权限 {login['user']['permissions']}")

    overview = call("GET", "/api/v1/dashboard/overview", token=token)
    print("3. 看板概览:", overview)

    trip = call(
        "POST",
        "/api/v1/weigh/trips",
        {
            "station_id": 1,
            "biz_type": 1,
            "customer_id": 1,
            # 每次运行使用唯一车牌，避免与在场工单重复开单校验冲突
            "plate_no": f"测A{int(time.time()) % 100000:05d}",
            "driver_name": "张师傅",
            "remark": "冒烟测试",
        },
        token,
    )
    trip_id = trip["trip"]["trip_id"]
    print(f"4. 创建行程: {trip['trip']['trip_no']} (id={trip_id})")

    detail = call(
        "POST",
        f"/api/v1/weigh/trips/{trip_id}/items",
        {"material_id": 1, "weight": 10.50, "weigh_mode": 1},
        token,
    )
    item = detail["items"][0]
    item_id = item["item_id"]
    print(f"5. 添加货物: {item['ticket_no']} 毛重 {item['start_weight']} 状态={item['status']}")

    priced = call(
        "POST",
        f"/api/v1/weigh/items/{item_id}/price",
        {
            "unit_price": 2200,
            "price_type": 1,
            "deduct_type": 1,
            "deduct_ratio": 0.02,
            "calc_base": 2,
        },
        token,
    )
    print(f"6. 核价: 单价 {priced['unit_price']} 状态={priced['status_text']}")

    completed = call(
        "POST", f"/api/v1/weigh/items/{item_id}/complete", {"end_weight": 3.50}, token
    )
    print(
        f"7. 称重完成: 净重 {completed['net_weight']} 扣杂 {completed['deduct_weight']} "
        f"结算净重 {completed['settle_weight']} 状态={completed['status_text']}"
    )
    assert abs(completed["net_weight"] - 7.00) < 0.001, "净重计算错误"
    assert abs(completed["deduct_weight"] - 0.14) < 0.001, "扣杂计算错误"
    assert abs(completed["settle_weight"] - 6.86) < 0.001, "结算净重计算错误"

    unsettled = call("GET", "/api/v1/weigh/items/unsettled", token=token)
    print(f"8. 待结算批次: {len(unsettled)} 条")

    settle = call(
        "POST",
        "/api/v1/settlements",
        {"item_ids": [item_id], "settle_mode": 3, "remark": "冒烟测试结算"},
        token,
    )
    print(
        f"9. 结算单: {settle['settle_no']} 净重 {settle['total_settle_weight']} "
        f"金额 {settle['total_amount']} 明细 {len(settle['details'])} 条"
    )
    assert abs(settle["total_amount"] - 15092.00) < 0.01, "金额计算错误"

    paid = call("POST", f"/api/v1/settlements/{settle['settle_id']}/pay", {"amount": 100}, token)
    print(f"10. 付款登记: 已付 {paid['paid_amount']} 状态={paid['pay_status']}")

    report = call("GET", "/api/v1/reports/daily", token=token)
    print("11. 日报汇总:", report["summary"])

    print("\n全部冒烟检查通过 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
