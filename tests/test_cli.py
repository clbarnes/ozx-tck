import subprocess as sp


def run_cli(*args) -> sp.CompletedProcess[str]:
    result = sp.run(
        ["ozx-tck", *(str(a) for a in args)],
        capture_output=True,
        text=True,
        check=False,
    )
    return result


def test_help():
    res = run_cli("--help")
    res.check_returncode()
    assert res.stdout.strip()
