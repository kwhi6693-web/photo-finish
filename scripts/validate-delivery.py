#!/usr/bin/env python3
"""Validate a Pinterest photo-set delivery without changing it."""

from __future__ import annotations

import argparse
from collections import defaultdict
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
import sys

from PIL import Image, ImageCms


EXPECTED_SIZES = {"wechat": (1080, 1080), "instagram": (1080, 1350)}
_SRGB_ICC_PROFILE = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
_ITEM_FIELDS = ("order", "source_id", "master", "wechat", "instagram")
_LAYOUT_HEADERS = (
    "order",
    "position",
    "source_id",
    "master",
    "wechat",
    "instagram",
    "visual_role",
    "publish_order",
)
_IMAGE_DECODE_EXCEPTIONS = (
    OSError,
    SyntaxError,
    ValueError,
    Image.DecompressionBombError,
    Image.DecompressionBombWarning,
)


def _one_line(value: object) -> str:
    return str(value).replace("\r", "\\r").replace("\n", "\\n")


def _one_line_errors(errors: list[str]) -> list[str]:
    return [_one_line(error) for error in errors]


def _error_context(
    *,
    field: str | None = None,
    platform: str | None = None,
    order: object | None = None,
    path: Path | str | None = None,
) -> str:
    parts = []
    if field is not None:
        parts.append(f"field={field}")
    if platform is not None:
        parts.append(f"platform={platform}")
    if order is not None:
        parts.append(f"order={order}")
    if path is not None:
        parts.append(f"path={path}")
    return ", ".join(parts)


def _resolve_declared_path(
    root: Path,
    declared_path: object,
    errors: list[str],
    *,
    field: str,
    platform: str | None = None,
    order: object | None = None,
) -> Path | None:
    context = _error_context(field=field, platform=platform, order=order)
    if not isinstance(declared_path, str) or not declared_path:
        errors.append(f"invalid path declaration: {context}; expected non-empty string")
        return None

    try:
        candidate = Path(declared_path)
        resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError) as error:
        errors.append(
            f"path resolves outside delivery_root or cannot be resolved: {context}, "
            f"path={declared_path}; {type(error).__name__}: {error}"
        )
        return None
    return resolved


def _read_hash(path: Path, errors: list[str], context: str) -> str | None:
    try:
        return sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        errors.append(f"cannot read file: {context}; {type(error).__name__}: {error}")
        return None


def _is_srgb_profile(profile_bytes: object) -> bool:
    if not isinstance(profile_bytes, bytes) or not profile_bytes:
        return False
    try:
        profile = ImageCms.ImageCmsProfile(BytesIO(profile_bytes))
        name = ImageCms.getProfileName(profile)
        color_space = profile.profile.xcolor_space.strip()
        return "srgb" in name.lower() and color_space == "RGB"
    except (OSError, TypeError, ValueError):
        return False


def _inspect_image(
    path: Path,
    errors: list[str],
    *,
    context: str,
    expected_size: tuple[int, int] | None = None,
    require_rgb_srgb: bool = False,
) -> bool:
    if not path.is_file():
        errors.append(f"missing image: {context}")
        return False

    try:
        with Image.open(path) as image:
            image.load()
            if expected_size is not None and image.size != expected_size:
                errors.append(
                    f"wrong dimensions: {context}; actual={image.size}, "
                    f"expected={expected_size}"
                )
            if require_rgb_srgb:
                if image.mode != "RGB":
                    errors.append(
                        f"image must be RGB: {context}; actual_mode={image.mode}"
                    )
                if not _is_srgb_profile(image.info.get("icc_profile")):
                    errors.append(f"image must have an sRGB ICC profile: {context}")
    except _IMAGE_DECODE_EXCEPTIONS as error:
        errors.append(
            f"image cannot be opened: {context}; {type(error).__name__}: {error}"
        )
        return False
    return True


def _rebuild_preview_bytes(
    platform_paths: list[tuple[object, Path]],
    platform: str,
    icc_profile: bytes,
) -> bytes:
    cell_width, cell_height = EXPECTED_SIZES[platform]
    canvas = Image.new("RGB", (cell_width * 3, cell_height * 3))
    try:
        for index, (_, source_path) in enumerate(platform_paths):
            with Image.open(source_path) as source:
                cell = source.convert("RGB")
                try:
                    canvas.paste(
                        cell,
                        ((index % 3) * cell_width, (index // 3) * cell_height),
                    )
                finally:
                    cell.close()
        output = BytesIO()
        canvas.save(
            output,
            format="JPEG",
            quality=95,
            subsampling=0,
            icc_profile=icc_profile,
        )
        return output.getvalue()
    finally:
        canvas.close()


def _heading_numbers(text: str, labels: str) -> list[int]:
    label_then_number = re.compile(
        rf"^\s*#{{1,6}}\s*(?:{labels})\s*(?:no\.?\s*)?(\d+)\s*(?:篇|则)?\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    number_then_label = re.compile(
        rf"^\s*#{{1,6}}\s*(\d+)\s*[.:、-]?\s*(?:{labels})\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    return [int(number) for number in label_then_number.findall(text)] + [
        int(number) for number in number_then_label.findall(text)
    ]


def _validate_documents(root: Path, errors: list[str]) -> None:
    captions_path = root / "captions.md"
    layout_path = root / "layout.md"

    if not captions_path.is_file():
        errors.append(f"missing captions.md: path={captions_path}")
    else:
        try:
            captions = captions_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append(
                f"cannot read captions.md: path={captions_path}; "
                f"{type(error).__name__}: {error}"
            )
        else:
            heading_requirements = (
                ("Chinese", r"中文(?:文案|标题)|Chinese\s+Caption", [1, 2, 3, 4]),
                ("English", r"English\s+(?:Caption|Copy)", [1, 2, 3, 4]),
                ("hashtag", r"Hashtags?(?:\s+(?:Set|Group))?", [1, 2]),
            )
            for label, pattern, expected in heading_requirements:
                actual = sorted(_heading_numbers(captions, pattern))
                if actual != expected:
                    errors.append(
                        f"captions.md {label} numbered headings must be "
                        f"{', '.join(map(str, expected))}; actual={actual}, "
                        f"path={captions_path}"
                    )

    if not layout_path.is_file():
        errors.append(f"missing layout.md: path={layout_path}")


def _split_markdown_table_row(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return [cell.strip().strip("`").strip() for cell in stripped[1:-1].split("|")]


def _validate_layout_mapping(root: Path, items: list[dict], errors: list[str]) -> None:
    layout_path = root / "layout.md"
    if not layout_path.is_file():
        return
    try:
        text = layout_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        errors.append(
            f"cannot read layout.md manifest mapping: path={layout_path}; "
            f"{type(error).__name__}: {error}"
        )
        return

    lines = text.splitlines()
    header_index = None
    for index, line in enumerate(lines):
        cells = _split_markdown_table_row(line)
        if cells is not None and tuple(cell.lower() for cell in cells) == _LAYOUT_HEADERS:
            header_index = index
            break
    if header_index is None:
        errors.append(
            f"layout.md must contain the manifest mapping table: path={layout_path}"
        )
        return

    if header_index + 1 >= len(lines):
        errors.append(
            f"layout.md manifest mapping table is missing its separator row: "
            f"path={layout_path}"
        )
        return
    separators = _split_markdown_table_row(lines[header_index + 1])
    if separators is None or len(separators) != len(_LAYOUT_HEADERS) or any(
        re.fullmatch(r":?-{3,}:?", separator.replace(" ", "")) is None
        for separator in separators
    ):
        errors.append(
            f"layout.md manifest mapping table has an invalid separator row: "
            f"path={layout_path}"
        )
        return

    rows: list[list[str]] = []
    for line in lines[header_index + 2 :]:
        if not line.strip():
            break
        cells = _split_markdown_table_row(line)
        if cells is None:
            break
        rows.append(cells)

    if len(rows) != 9:
        errors.append(
            f"layout.md manifest mapping table must contain exactly 9 rows; "
            f"actual={len(rows)}, path={layout_path}"
        )
        return

    for index, (item, cells) in enumerate(zip(items, rows), start=1):
        if len(cells) != len(_LAYOUT_HEADERS):
            errors.append(
                f"layout.md manifest mapping row has {len(cells)} fields; "
                f"expected={len(_LAYOUT_HEADERS)}, row={index}, path={layout_path}"
            )
            continue

        record = dict(zip(_LAYOUT_HEADERS, cells))
        order = item.get("order", index)
        expected_position = f"r{(index - 1) // 3 + 1}c{(index - 1) % 3 + 1}"
        expected = {
            "order": str(order),
            "position": expected_position,
            "source_id": str(item.get("source_id", "")),
            "master": str(item.get("master", "")),
            "wechat": str(item.get("wechat", "")),
            "instagram": str(item.get("instagram", "")),
            "publish_order": str(order),
        }
        for field, expected_value in expected.items():
            if record[field] != expected_value:
                errors.append(
                    f"layout.md manifest mapping mismatch: field={field}, row={index}, "
                    f"actual={record[field]!r}, expected={expected_value!r}, "
                    f"path={layout_path}"
                )
        if not record["visual_role"]:
            errors.append(
                f"layout.md manifest mapping requires a visual_role: row={index}, "
                f"path={layout_path}"
            )


def _load_manifest(manifest_path: Path, errors: list[str]) -> dict | None:
    try:
        with manifest_path.open("r", encoding="utf-8") as manifest_file:
            manifest = json.load(manifest_file)
    except FileNotFoundError:
        errors.append(f"missing manifest: path={manifest_path}")
        return None
    except json.JSONDecodeError as error:
        errors.append(
            f"manifest contains invalid JSON: path={manifest_path}; "
            f"line={error.lineno}, column={error.colno}: {error.msg}"
        )
        return None
    except (UnicodeError, ValueError) as error:
        errors.append(
            f"manifest parsing error: path={manifest_path}; "
            f"{type(error).__name__}: {error}"
        )
        return None
    except OSError as error:
        errors.append(
            f"cannot read manifest: path={manifest_path}; "
            f"{type(error).__name__}: {error}"
        )
        return None

    if not isinstance(manifest, dict):
        errors.append("manifest must be a JSON object")
        return None
    return manifest


def _validate_manifest_structure(manifest: dict, errors: list[str]) -> list[dict]:
    raw_items = manifest.get("items")
    if not isinstance(raw_items, list):
        errors.append("manifest field=items must be a list containing exactly 9 items")
        return []
    if len(raw_items) != 9:
        errors.append(f"manifest must contain exactly 9 items; actual={len(raw_items)}")

    items = []
    for index, raw_item in enumerate(raw_items, start=1):
        if not isinstance(raw_item, dict):
            errors.append(
                f"manifest item must be an object: index={index}, "
                f"actual_type={type(raw_item).__name__}"
            )
            continue
        items.append(raw_item)
        missing = [field for field in _ITEM_FIELDS if field not in raw_item]
        if missing:
            errors.append(
                f"manifest item is missing fields: index={index}, "
                f"fields={', '.join(missing)}"
            )

    orders = [item.get("order") for item in items]
    for index, order in enumerate(orders, start=1):
        if type(order) is not int:
            errors.append(
                f"invalid order: index={index}, order={order!r}; expected integer"
            )
    if orders != list(range(1, 10)):
        errors.append(f"manifest orders must be exactly 1 through 9 in sequence; actual={orders}")

    source_occurrences: dict[str, list[object]] = defaultdict(list)
    for index, item in enumerate(items, start=1):
        source_id = item.get("source_id")
        order = item.get("order", index)
        if not isinstance(source_id, str) or not source_id.strip():
            errors.append(
                f"invalid source_id: order={order}; expected non-empty string"
            )
        else:
            source_occurrences[source_id].append(order)
    for source_id, duplicate_orders in source_occurrences.items():
        if len(duplicate_orders) > 1:
            errors.append(
                f"duplicate source_id: source_id={source_id!r}, "
                f"orders={duplicate_orders}"
            )
    return items


def _validate_item_files(
    root: Path, items: list[dict], errors: list[str]
) -> dict[str, list[tuple[object, Path]]]:
    platform_paths: dict[str, list[tuple[object, Path]]] = {
        platform: [] for platform in EXPECTED_SIZES
    }
    platform_hashes: dict[str, dict[str, list[tuple[object, Path]]]] = {
        platform: defaultdict(list) for platform in EXPECTED_SIZES
    }

    for index, item in enumerate(items, start=1):
        order = item.get("order", index)
        master_path = _resolve_declared_path(
            root,
            item.get("master"),
            errors,
            field="master",
            order=order,
        )
        if master_path is not None:
            _inspect_image(
                master_path,
                errors,
                context=_error_context(field="master", order=order, path=master_path),
            )

        for platform, expected_size in EXPECTED_SIZES.items():
            platform_path = _resolve_declared_path(
                root,
                item.get(platform),
                errors,
                field=platform,
                platform=platform,
                order=order,
            )
            if platform_path is None:
                continue

            context = _error_context(
                field=platform, platform=platform, order=order, path=platform_path
            )
            expected_basename = f"{index:02d}.jpg"
            if platform_path.name != expected_basename:
                errors.append(
                    f"wrong platform basename: {context}; actual={platform_path.name}, "
                    f"expected={expected_basename}"
                )

            image_ok = _inspect_image(
                platform_path,
                errors,
                context=context,
                expected_size=expected_size,
                require_rgb_srgb=True,
            )
            if image_ok:
                platform_paths[platform].append((order, platform_path))
            digest = _read_hash(platform_path, errors, context)
            if digest is not None:
                platform_hashes[platform][digest].append((order, platform_path))

    for platform, hashes in platform_hashes.items():
        for digest, occurrences in hashes.items():
            if len(occurrences) > 1:
                first_order, first_path = occurrences[0]
                for order, path in occurrences[1:]:
                    errors.append(
                        f"duplicate platform image bytes: platform={platform}, "
                        f"order={order}, path={path}; duplicates order={first_order}, "
                        f"path={first_path}, sha256={digest}"
                    )
    return platform_paths


def _validate_previews(
    root: Path,
    manifest: dict,
    platform_paths: dict[str, list[tuple[object, Path]]],
    errors: list[str],
) -> None:
    previews = manifest.get("previews")
    if not isinstance(previews, dict):
        errors.append("manifest field=previews must be an object")
        return

    for platform in EXPECTED_SIZES:
        preview_path = _resolve_declared_path(
            root,
            previews.get(platform),
            errors,
            field="preview",
            platform=platform,
        )
        if preview_path is None:
            continue
        context = _error_context(
            field="preview", platform=platform, path=preview_path
        )
        preview_ok = _inspect_image(
            preview_path,
            errors,
            context=context,
            require_rgb_srgb=True,
        )
        if not preview_ok or len(platform_paths[platform]) != 9:
            continue

        try:
            with Image.open(preview_path) as preview:
                preview_icc = preview.info.get("icc_profile")
            if not isinstance(preview_icc, bytes) or not preview_icc:
                preview_icc = _SRGB_ICC_PROFILE
            expected_bytes = _rebuild_preview_bytes(
                platform_paths[platform], platform, preview_icc
            )
            actual_bytes = preview_path.read_bytes()
        except _IMAGE_DECODE_EXCEPTIONS as error:
            errors.append(
                f"cannot rebuild preview for comparison: {context}; "
                f"{type(error).__name__}: {error}"
            )
            continue
        expected_digest = sha256(expected_bytes).hexdigest()
        actual_digest = sha256(actual_bytes).hexdigest()
        if actual_digest != expected_digest:
            errors.append(
                f"preview byte hash does not match row-major rebuild: {context}; "
                f"actual_sha256={actual_digest}, expected_sha256={expected_digest}"
            )


def validate_delivery(delivery_root: Path, manifest_path: Path) -> list[str]:
    """Return every structural validation error without mutating the delivery."""
    errors: list[str] = []
    try:
        root = Path(delivery_root).resolve()
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        return _one_line_errors([
            f"invalid delivery_root: path={delivery_root!r}; "
            f"{type(error).__name__}: {error}"
        ])

    if not root.is_dir():
        return _one_line_errors([f"delivery_root is not a directory: path={root}"])

    _validate_documents(root, errors)
    try:
        manifest_file = Path(manifest_path)
    except (TypeError, ValueError) as error:
        errors.append(
            f"invalid manifest path: path={manifest_path!r}; "
            f"{type(error).__name__}: {error}"
        )
        return _one_line_errors(errors)

    manifest = _load_manifest(manifest_file, errors)
    if manifest is None:
        return _one_line_errors(errors)

    items = _validate_manifest_structure(manifest, errors)
    _validate_layout_mapping(root, items, errors)
    platform_paths = _validate_item_files(root, items, errors)
    _validate_previews(root, manifest, platform_paths, errors)
    return _one_line_errors(errors)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delivery-root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        errors = validate_delivery(args.delivery_root, args.manifest)
    except Exception as error:
        print(
            _one_line(
                f"validation failed unexpectedly: {type(error).__name__}: {error}"
            ),
            file=sys.stderr,
        )
        return 1
    if errors:
        for error in errors:
            print(_one_line(error))
        return 1
    print("Delivery is valid!")
    return 0


if __name__ == '__main__':
    import sys
    for _photo_finish_stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_photo_finish_stream, 'reconfigure'):
            _photo_finish_stream.reconfigure(encoding='utf-8')
    raise SystemExit(main())
