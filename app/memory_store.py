from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings


_local_items: dict[str, list[dict[str, str]]] = {}


def now_iso() -> str:
    return datetime.now(ZoneInfo(settings.timezone)).isoformat(timespec="seconds")


def now_label() -> str:
    return datetime.now(ZoneInfo(settings.timezone)).strftime("%d-%m %H:%M")


def _table():
    if not settings.memory_table_name:
        return None
    boto3 = __import__("boto3")
    return boto3.resource("dynamodb").Table(settings.memory_table_name)


def put_item(user: str, category: str, text: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    created_at = now_iso()
    item = {
        "pk": f"USER#{user}",
        "sk": f"{category.upper()}#{created_at}",
        "category": category,
        "text": text,
        "created_at": created_at,
    }
    if extra:
        item.update(extra)

    table = _table()
    if table:
        try:
            table.put_item(Item=item)
        except Exception as exc:
            print(f"DynamoDB put_item failed, using local fallback: {exc}")
            _local_items.setdefault(user, []).append(item)
    else:
        _local_items.setdefault(user, []).append(item)
    return item


def list_items(user: str, category: str, limit: int = 20) -> list[dict[str, str]]:
    table = _table()
    if table:
        try:
            response = table.query(
                KeyConditionExpression="pk = :pk AND begins_with(sk, :prefix)",
                ExpressionAttributeValues={
                    ":pk": f"USER#{user}",
                    ":prefix": f"{category.upper()}#",
                },
                ScanIndexForward=False,
                Limit=limit,
            )
            return list(reversed(response.get("Items", [])))
        except Exception as exc:
            print(f"DynamoDB query failed, using local fallback: {exc}")

    items = [
        item for item in _local_items.get(user, [])
        if item.get("category") == category
    ]
    return items[-limit:]


def mark_done(user: str, category: str, text_contains: str) -> bool:
    needle = text_contains.lower().strip()
    if not needle:
        return False

    table = _table()
    items = list_items(user, category, limit=50)
    for item in reversed(items):
        if needle in item.get("text", "").lower():
            item["status"] = "done"
            item["done_at"] = now_iso()
            if table:
                try:
                    table.put_item(Item=item)
                except Exception as exc:
                    print(f"DynamoDB mark_done failed: {exc}")
            return True
    return False


def search_items(user: str, text_contains: str, limit: int = 12) -> list[dict[str, str]]:
    needle = text_contains.lower().strip()
    if not needle:
        return []
    categories = ["note", "agenda", "reminder", "therapy", "eye_drops", "commitment"]
    matches = []
    for category in categories:
        for item in list_items(user, category, limit=50):
            if needle in item.get("text", "").lower():
                matches.append(item)
    return matches[-limit:]


def delete_matching_items(user: str, category: str | None, text_contains: str = "") -> int:
    needle = text_contains.lower().strip()
    categories = [category] if category else ["note", "agenda", "reminder", "therapy", "eye_drops", "commitment"]
    table = _table()
    deleted = 0
    for current_category in categories:
        for item in list_items(user, current_category, limit=100):
            if needle and needle not in item.get("text", "").lower():
                continue
            if table:
                try:
                    table.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})
                except Exception as exc:
                    print(f"DynamoDB delete failed: {exc}")
                    continue
            else:
                _local_items[user] = [
                    local for local in _local_items.get(user, [])
                    if not (local.get("pk") == item.get("pk") and local.get("sk") == item.get("sk"))
                ]
            deleted += 1
    return deleted
