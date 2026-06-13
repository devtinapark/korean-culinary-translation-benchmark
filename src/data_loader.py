"""
Kitchen Audio Dataset Loader
Loads local audio files and transcriptions for ASR benchmarking
"""
from typing import List, Optional
from pathlib import Path
import json
import numpy as np
from dataclasses import dataclass

def _load_audio(path: Path):
    """Load audio file — supports MP3, WAV, FLAC, M4A, etc. via pydub + ffmpeg."""
    from pydub import AudioSegment
    segment = AudioSegment.from_file(str(path))
    segment = segment.set_channels(1)  # stereo → mono
    sr = segment.frame_rate
    samples = np.array(segment.get_array_of_samples(), dtype=np.float32)
    # normalize to [-1.0, 1.0]
    samples /= 2 ** (segment.sample_width * 8 - 1)
    return samples, sr


@dataclass
class AudioSample:
    """Container for a single audio sample"""
    audio: np.ndarray
    sampling_rate: int
    text: str
    id: str


class KitchenAudioLoader:
    """
    Loads your own kitchen audio clips for ASR evaluation.

    Expected layout (two options):

    Option A — metadata.json index:
        kitchen_samples/
          metadata.json          [{"id": "001", "audio_file": "001.wav", "transcript": "..."}]
          audio/001.wav
          audio/002.wav

    Option B — matching filenames (no metadata.json needed):
        kitchen_samples/
          audio/001.wav
          transcriptions/001.txt   (plain text, one transcript per file)
    """

    def __init__(
        self,
        audio_dir: str,
        transcripts_dir: Optional[str] = None,
        metadata_file: Optional[str] = None,
    ):
        self.audio_dir = Path(audio_dir)
        self.transcripts_dir = Path(transcripts_dir) if transcripts_dir else None
        self.metadata_file = Path(metadata_file) if metadata_file else None
        self.samples: List[AudioSample] = []

    def load(self) -> List[AudioSample]:
        if self.metadata_file and self.metadata_file.exists():
            self._load_from_metadata()
        elif self.transcripts_dir and self.transcripts_dir.exists():
            self._load_from_matching_files()
        else:
            raise FileNotFoundError(
                f"No audio data found. Add audio files to {self.audio_dir} "
                f"and transcripts to {self.transcripts_dir}, or create a metadata.json. "
                f"See kitchen_samples/metadata.json for the expected format."
            )

        print(f"Loaded {len(self.samples)} kitchen audio samples")
        return self.samples

    def _load_from_metadata(self):
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            entries = json.load(f)

        for entry in entries:
            audio_path = self.audio_dir / entry["audio_file"]
            if not audio_path.exists():
                print(f"  Warning: audio file not found, skipping: {audio_path}")
                continue

            audio, sr = _load_audio(audio_path)
            self.samples.append(AudioSample(
                audio=audio,
                sampling_rate=sr,
                text=entry["transcript"],
                id=entry.get("id", audio_path.stem),
            ))

    def _load_from_matching_files(self):
        audio_extensions = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}
        audio_files = sorted(
            f for f in self.audio_dir.iterdir()
            if f.suffix.lower() in audio_extensions
        )

        for audio_path in audio_files:
            transcript_path = self.transcripts_dir / f"{audio_path.stem}.txt"
            if not transcript_path.exists():
                print(f"  Warning: no transcript for {audio_path.name}, skipping")
                continue

            audio, sr = _load_audio(audio_path)
            transcript = transcript_path.read_text(encoding="utf-8").strip()

            self.samples.append(AudioSample(
                audio=audio,
                sampling_rate=sr,
                text=transcript,
                id=audio_path.stem,
            ))

    def __len__(self):
        return len(self.samples)

    def __iter__(self):
        return iter(self.samples)


class AudioPreprocessor:
    """Prepares audio arrays for ASR model input"""

    @staticmethod
    def prepare_for_model(
        audio: np.ndarray,
        sampling_rate: int,
        target_sr: int = 16000,
    ):
        if sampling_rate != target_sr:
            from pydub import AudioSegment
            segment = AudioSegment(
                (audio * 32767).astype(np.int16).tobytes(),
                frame_rate=sampling_rate,
                sample_width=2,
                channels=1,
            )
            segment = segment.set_frame_rate(target_sr)
            audio = np.array(segment.get_array_of_samples(), dtype=np.float32) / 32767
            sampling_rate = target_sr

        # Normalize to [-1, 1]
        peak = np.max(np.abs(audio))
        if peak > 0:
            audio = audio / peak

        return audio, sampling_rate
