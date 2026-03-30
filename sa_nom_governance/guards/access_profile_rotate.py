from argparse import ArgumentParser
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from sa_nom_governance.guards.access_control import hash_token
from sa_nom_governance.utils.config import AppConfig


def main() -> None:
    parser = ArgumentParser(description="Rotate a hashed access profile token for SA-NOM private server runtime.")
    parser.add_argument("profile_id")
    parser.add_argument("token")
    parser.add_argument("--profiles", default=None)
    parser.add_argument("--rotate-after-days", type=int, default=90)
    parser.add_argument("--keep-previous", type=int, default=2)
    args = parser.parse_args()

    config = AppConfig()
    profiles_path = Path(args.profiles) if args.profiles else config.access_profiles_path
    if profiles_path is None or not profiles_path.exists():
        raise SystemExit("access_profiles.json not found")

    data = json.loads(profiles_path.read_text(encoding="utf-8"))
    for item in data:
        if str(item.get("profile_id")) != args.profile_id:
            continue

        current_hash = item.get("token_hash")
        previous_hashes = [str(value) for value in item.get("previous_token_hashes", [])]
        if current_hash:
            previous_hashes.insert(0, str(current_hash))
        deduped = []
        for value in previous_hashes:
            if value not in deduped:
                deduped.append(value)
        item["previous_token_hashes"] = deduped[: max(args.keep_previous, 0)]
        item["token_hash"] = hash_token(args.token)
        item.pop("token", None)
        now = datetime.now(timezone.utc)
        item["not_before"] = now.isoformat()
        item["rotate_after"] = (now + timedelta(days=args.rotate_after_days)).isoformat()
        profiles_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({
            "profile_id": args.profile_id,
            "updated": True,
            "rotate_after": item["rotate_after"],
            "previous_token_hashes": len(item["previous_token_hashes"]),
            "profiles_path": str(profiles_path),
        }, ensure_ascii=False, indent=2))
        return

    raise SystemExit(f"profile not found: {args.profile_id}")


if __name__ == "__main__":
    main()
