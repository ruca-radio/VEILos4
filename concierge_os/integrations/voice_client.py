import subprocess
from pathlib import Path

from ..config import settings, MEDIA_DIR


def synthesize_voice(text: str, user_id: int) -> Path:
    """
    Use local Piper TTS to synthesize a voice note.
    Requires `piper` binary and a voice model installed.
    """
    user_dir = MEDIA_DIR / f"user_{user_id}"
    user_dir.mkdir(exist_ok=True, parents=True)
    out_path = user_dir / "good_morning.wav"

    cmd = [
        settings.piper_binary,
        "--model",
        settings.piper_voice,
        "--output_file",
        str(out_path),
    ]

    proc = subprocess.run(
        cmd,
        input=text.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Piper TTS failed: {proc.stderr.decode('utf-8', errors='ignore')}")
    return out_path

