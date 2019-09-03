import filecmp
import pathlib
import shutil
import subprocess


def test_webpage_command():
    manuscript_path = pathlib.Path(__file__).parent.joinpath('test-manuscript')
    webpage_path = manuscript_path.joinpath('webpage')
    if webpage_path.exists():
        shutil.rmtree(webpage_path)
    args = [
        "manubot", "webpage",
        "--timestamp",
        "--no-ots-cache",
        "--version=testing",
    ]
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=manuscript_path,
    )
    print(process.args)
    print(process.stdout.decode())
    print(process.stderr.decode())
    assert process.returncode == 0
    assert webpage_path.is_dir()
    manuscript_html_path = manuscript_path.joinpath('output/manuscript.html')
    index_html_latest_path = webpage_path.joinpath('v/latest/index.html')
    index_html_version_path = webpage_path.joinpath('v/testing/index.html')
    for path in index_html_latest_path, index_html_version_path:
        assert filecmp.cmp(manuscript_html_path, path, shallow=False)
    assert index_html_version_path.with_name('index.html.ots').exists()
