#!/usr/bin/env python3
"""Build WeChat and Instagram three-by-three JPEG previews."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile

from PIL import Image, ImageCms


EXPECTED_SIZES = {"wechat": (1080, 1080), "instagram": (1080, 1350)}
_SRGB_ICC_PROFILE = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
_REQUIRED_ITEM_FIELDS = ("order", "source_id", "master", "wechat", "instagram")


def _validate_manifest(manifest: dict) -> None:
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")

    items = manifest.get("items")
    if not isinstance(items, list) or len(items) != 9:
        raise ValueError("manifest must contain exactly nine items")

    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each manifest item must be an object")
        missing = [field for field in _REQUIRED_ITEM_FIELDS if field not in item]
        if missing:
            raise ValueError(f"manifest item is missing fields: {', '.join(missing)}")

    orders = [item["order"] for item in items]
    if any(type(order) is not int for order in orders):
        raise ValueError("manifest item orders must be integers")
    if orders != list(range(1, 10)):
        raise ValueError("manifest item orders must be exactly 1 through 9 in sequence")

    source_ids = [item["source_id"] for item in items]
    if any(
        not isinstance(source_id, str) or not source_id.strip()
        for source_id in source_ids
    ):
        raise ValueError("each source_id must be a non-empty string")
    if len(set(source_ids)) != 9:
        raise ValueError("manifest must contain nine unique source_id values")

    previews = manifest.get("previews")
    if not isinstance(previews, dict):
        raise ValueError("manifest previews must be an object")
    for platform in EXPECTED_SIZES:
        if not isinstance(previews.get(platform), str) or not previews[platform]:
            raise ValueError(f"manifest previews must declare {platform}")


def load_manifest(manifest_path: Path) -> dict:
    """Load JSON and require exactly nine ordered, unique source items."""
    path = Path(manifest_path)
    with path.open("r", encoding="utf-8") as manifest_file:
        manifest = json.load(manifest_file)
    _validate_manifest(manifest)
    return manifest


def _resolve_contained(delivery_root: Path, declared_path: str, label: str) -> Path:
    if not isinstance(declared_path, str) or not declared_path:
        raise ValueError(f"{label} path must be a non-empty string")

    root = delivery_root.resolve()
    path = Path(declared_path)
    resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError(f"{label} path resolves outside delivery_root: {declared_path}") from error
    return resolved


def _validate_contained_manifest_paths(delivery_root: Path, manifest: dict) -> None:
    for item in manifest["items"]:
        for field in ("master", "wechat", "instagram"):
            _resolve_contained(
                delivery_root,
                item[field],
                f"{field} item {item['order']}",
            )
    for platform in EXPECTED_SIZES:
        _resolve_contained(
            delivery_root,
            manifest["previews"][platform],
            f"{platform} preview",
        )


def _validate_output_collisions(
    delivery_root: Path,
    manifest: dict,
    manifest_path: Path | None = None,
) -> None:
    inputs = []
    for item in manifest["items"]:
        for field in ("master", "wechat", "instagram"):
            inputs.append(
                (
                    field,
                    item["order"],
                    _resolve_contained(
                        delivery_root,
                        item[field],
                        f"{field} input for order {item['order']}",
                    ),
                )
            )

    outputs = {
        platform: _resolve_contained(
            delivery_root,
            manifest["previews"][platform],
            f"{platform} preview",
        )
        for platform in EXPECTED_SIZES
    }

    def paths_collide(left: Path, right: Path) -> bool:
        if left == right:
            return True
        try:
            return left.exists() and right.exists() and left.samefile(right)
        except OSError as error:
            raise ValueError(
                f"cannot compare file identity for {left} and {right}: {error}"
            ) from error

    for platform, output_path in outputs.items():
        for field, order, input_path in inputs:
            if paths_collide(output_path, input_path):
                raise ValueError(
                    f"{platform} preview path {output_path} collides with declared "
                    f"{field} input for order {order} at path {input_path}"
                )

    if paths_collide(outputs["wechat"], outputs["instagram"]):
        raise ValueError(
            f"wechat preview path {outputs['wechat']} collides with "
            f"instagram preview path {outputs['instagram']}"
        )

    if manifest_path is not None:
        resolved_manifest = Path(manifest_path).resolve()
        for platform, output_path in outputs.items():
            if paths_collide(output_path, resolved_manifest):
                raise ValueError(
                    f"{platform} preview path {output_path} collides with "
                    f"manifest path {resolved_manifest}"
                )


def build_platform_preview(
    delivery_root: Path,
    manifest: dict,
    platform: str,
) -> Path:
    """Compose platform images row-major into the declared preview path."""
    root = Path(delivery_root).resolve()
    if not root.is_dir():
        raise ValueError(f"delivery_root is not a directory: {delivery_root}")
    if platform not in EXPECTED_SIZES:
        raise ValueError(f"unsupported platform: {platform}")
    _validate_manifest(manifest)
    _validate_contained_manifest_paths(root, manifest)
    _validate_output_collisions(root, manifest)

    cell_width, cell_height = EXPECTED_SIZES[platform]
    output_path = _resolve_contained(
        root, manifest["previews"][platform], f"{platform} preview"
    )

    canvas = Image.new("RGB", (cell_width * 3, cell_height * 3))
    try:
        for index, item in enumerate(manifest["items"]):
            source_path = _resolve_contained(
                root, item[platform], f"{platform} item {item['order']}"
            )
            if not source_path.is_file():
                raise FileNotFoundError(
                    f"missing input: platform={platform}, order={item['order']}, "
                    f"path={source_path}"
                )

            with Image.open(source_path) as source:
                if source.size != (cell_width, cell_height):
                    raise ValueError(
                        f"wrong dimensions: platform={platform}, order={item['order']}, "
                        f"path={source_path}; actual={source.size}, "
                        f"expected={(cell_width, cell_height)}"
                    )
                cell = source.convert("RGB")
                try:
                    column = index % 3
                    row = index // 3
                    canvas.paste(cell, (column * cell_width, row * cell_height))
                finally:
                    cell.close()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
        try:
            canvas.save(
                temporary_path,
                format="JPEG",
                quality=95,
                subsampling=0,
                icc_profile=_SRGB_ICC_PROFILE,
            )
            os.replace(temporary_path, output_path)
        finally:
            temporary_path.unlink(missing_ok=True)
    finally:
        canvas.close()

    return output_path


def build_previews(delivery_root: Path, manifest_path: Path) -> dict[str, Path]:
    """Build both previews and return {'wechat': path, 'instagram': path}."""
    root = Path(delivery_root).resolve()
    if not root.is_dir():
        raise ValueError(f"delivery_root is not a directory: {delivery_root}")
    manifest_file = Path(manifest_path)
    manifest = load_manifest(manifest_file)
    _validate_contained_manifest_paths(root, manifest)
    _validate_output_collisions(root, manifest, manifest_file)
    return {
        platform: build_platform_preview(root, manifest, platform)
        for platform in ("wechat", "instagram")
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delivery-root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args(argv)

    outputs = build_previews(args.delivery_root, args.manifest)
    print(json.dumps({platform: str(path) for platform, path in outputs.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
