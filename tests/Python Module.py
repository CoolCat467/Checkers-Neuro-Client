import checkers_neuro


def test_cli_run_exists() -> None:
    assert callable(checkers_neuro.cli_run)
