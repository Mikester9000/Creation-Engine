import json

from creation_engine.cli import main


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
