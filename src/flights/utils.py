def assert_unique(old_data: list[dict], new_data: list[dict], key: str) -> None:
    old_keys = [v for item in old_data if (v := item.get(key)) is not None]
    new_keys = [v for item in new_data if (v := item.get(key)) is not None]

    new_keys_set = set(new_keys)
    if len(new_keys) != len(new_keys_set):
        msg = f"Duplicate values found in new data for key '{key}'"
        raise ValueError(msg)

    duplicates = set(new_keys).intersection(old_keys)
    if duplicates:
        msg = f"Duplicate values found for key '{key}': {duplicates}"
        raise ValueError(msg)
