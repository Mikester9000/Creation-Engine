import json

import creation_engine.gui
from creation_engine.cli import main
from creation_engine.quality_check import run_quality_check


def test_list_backends(capsys):
    rc = main(["list-backends"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "procedural" in out


def test_texture_command(tmp_path):
    rc = main(
        [
            "texture",
            "--prompt",
            "stone",
            "--seed",
            "42",
            "--output",
            str(tmp_path),
        ]
    )
    assert rc == 0
    assert (tmp_path / "stone_albedo.png").exists()
    with open(tmp_path / "stone.json", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["family"] == "props"
    assert manifest["content_target"]["textures"] == "Content/Textures"
    assert manifest["style_profile"] == "ps2_ff7_ff12_highest_quality_ps2"


def test_ui_icon_and_pack_commands(tmp_path):
    rc = main(
        [
            "ui-icon",
            "--prompt",
            "quest icon",
            "--seed",
            "7",
            "--output",
            str(tmp_path),
        ]
    )
    assert rc == 0
    assert (tmp_path / "quest_icon.png").exists()
    with open(tmp_path / "quest_icon.json", encoding="utf-8") as f:
        icon_manifest = json.load(f)
    assert icon_manifest["content_target"]["ui"] == "Content/UI"
    assert icon_manifest["style_profile"] == "ps2_ff7_ff12_highest_quality_ps2"

    pack_dir = tmp_path / "pack"
    rc = main(["material-pack", "--seed", "11", "--output", str(pack_dir)])
    assert rc == 0
    pack_manifest_path = pack_dir / "materials" / "material_pack.json"
    assert pack_manifest_path.exists()
    with open(pack_manifest_path, encoding="utf-8") as f:
        pack_manifest = json.load(f)
    assert pack_manifest["destination_map"]
    assert pack_manifest["style_profile"] == "ps2_ff7_ff12_highest_quality_ps2"


def test_quality_check_command_passes_on_generated_bundle(tmp_path, capsys):
    rc = main(["full-bundle", "--seed", "13", "--output", str(tmp_path)])
    assert rc == 0
    rc = main(["quality-check", "--output", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Quality check passed" in out


def test_quality_check_command_fails_on_bad_style_profile(tmp_path, capsys):
    rc = main(["texture", "--prompt", "stone", "--seed", "42", "--output", str(tmp_path)])
    assert rc == 0
    manifest_path = tmp_path / "stone.json"
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    manifest["style_profile"] = "bad_style"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    rc = main(["quality-check", "--output", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 1
    assert "Quality check failed:" in out
    assert "style_profile" in out


def test_quality_check_rejects_banned_prompt_terms(tmp_path):
    rc = main(
        [
            "texture",
            "--prompt",
            "ps2 jrpg photoreal stone",
            "--seed",
            "42",
            "--output",
            str(tmp_path),
        ]
    )
    assert rc == 0

    result = run_quality_check(tmp_path)
    assert result.ok is False
    assert any("banned style term" in error for error in result.errors)


def test_bundle_audit_reports_coverage_and_pass(tmp_path, capsys):
    rc = main(["full-bundle", "--seed", "13", "--output", str(tmp_path)])
    assert rc == 0

    rc = main(["bundle-audit", "--output", str(tmp_path)])
    out = capsys.readouterr().out

    assert rc == 0
    assert "Bundle audit checked manifests:" in out
    assert "Narrative coverage:" in out
    assert "Style coverage:" in out
    assert "FF aesthetic compliance: PASS" in out


def test_release_check_passes_on_generated_bundle(tmp_path, capsys):
    rc = main(["full-bundle", "--seed", "13", "--output", str(tmp_path)])
    assert rc == 0

    rc = main(["release-check", "--output", str(tmp_path)])
    out = capsys.readouterr().out

    assert rc == 0
    assert "Release readiness passed" in out


def test_release_check_fails_on_invalid_bundle_completeness(tmp_path, capsys):
    rc = main(["full-bundle", "--seed", "13", "--output", str(tmp_path)])
    assert rc == 0

    bundle_manifest_path = next(
        path
        for path in tmp_path.rglob("*.json")
        if json.loads(path.read_text(encoding="utf-8")).get("asset_family") == "bundles"
    )
    bundle_manifest = json.loads(bundle_manifest_path.read_text(encoding="utf-8"))
    bundle_manifest["completeness_matrix"]["complete"] = False
    bundle_manifest_path.write_text(json.dumps(bundle_manifest, indent=2), encoding="utf-8")

    rc = main(["release-check", "--output", str(tmp_path)])
    out = capsys.readouterr().out

    assert rc == 1
    assert "Release readiness failed:" in out
    assert "completeness_matrix.complete must be true" in out


def test_quality_check_rejects_non_directory_output(tmp_path):
    output_file = tmp_path / "not_a_directory"
    output_file.write_text("x", encoding="utf-8")

    result = run_quality_check(output_file)

    assert result.ok is False
    assert result.checked_manifests == 0
    assert result.errors == [f"Output path is not a directory: {output_file}"]


def test_quality_check_skips_non_object_json(tmp_path):
    (tmp_path / "manifest.json").write_text('["asset_family"]', encoding="utf-8")

    result = run_quality_check(tmp_path)

    assert result.ok is False
    assert result.checked_manifests == 0
    assert result.errors == ["No asset manifests found (no JSON file with asset_family field)."]


def test_quality_check_rejects_unsafe_references_and_negative_png_size(tmp_path):
    rc = main(["texture", "--prompt", "stone", "--seed", "42", "--output", str(tmp_path)])
    assert rc == 0

    manifest_path = tmp_path / "stone.json"
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    outside_path = tmp_path.parent / "outside.png"
    outside_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 64)

    manifest["files"]["albedo"] = "../outside.png"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    result = run_quality_check(tmp_path)
    assert result.ok is False
    assert any("referenced file must stay within output directory" in error for error in result.errors)

    manifest["files"]["albedo"] = "*.png"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    result = run_quality_check(tmp_path)
    assert result.ok is False
    assert any("must not contain glob metacharacters" in error for error in result.errors)

    result = run_quality_check(tmp_path, min_png_size=-1)
    assert result.ok is False
    assert result.errors == ["Minimum PNG size must be non-negative, got -1"]


def test_gui_command_dispatches(monkeypatch, tmp_path):
    called: dict[str, str] = {}

    def _stub_run_gui(*, output_dir, initial_file):
        called["output_dir"] = output_dir
        called["initial_file"] = initial_file

    monkeypatch.setattr(creation_engine.gui, "run_gui", _stub_run_gui)
    rc = main(["gui", "--output", str(tmp_path), "--file", str(tmp_path / "stone.json")])
    assert rc == 0
    assert called["output_dir"] == str(tmp_path)
    assert called["initial_file"] == str(tmp_path / "stone.json")


def test_gui_command_returns_error_when_launch_fails(monkeypatch, tmp_path, capsys):
    def _stub_run_gui(*, output_dir, initial_file):
        raise RuntimeError("Tkinter is required to run the GUI.")

    monkeypatch.setattr(creation_engine.gui, "run_gui", _stub_run_gui)
    rc = main(["gui", "--output", str(tmp_path)])
    err = capsys.readouterr().err
    assert rc == 1
    assert "GUI launch failed: Tkinter is required to run the GUI." in err
