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
