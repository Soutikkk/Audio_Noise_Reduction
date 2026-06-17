# Audio Noise Reducer CLI

A modular, beginner-friendly, and professional Python command-line tool that reduces background noise from audio files using spectral gating algorithms.

## Features

- **Wide Format Support**: Works natively with **WAV**, **FLAC**, and **MP3** files.
- **Robust Multi-Channel Handling**: Supports both mono and stereo files seamlessly.
- **Adjustable Strength**: Fine-tune the reduction intensity via a simple command-line argument.
- **Smart Estimation**: Automatically samples noise profiles from the beginning of the audio.
- **Double-Engine Loader**: Leverages `soundfile` for lightning-fast native loading of WAV/FLAC files (without external dependencies), and falls back to `pydub` (via FFmpeg) for MP3 files.
- **Clear Progress Indicators**: Displays progress messages during each stage of execution.

---

## Prerequisites

- **Python 3.10 or higher**
- **FFmpeg (Optional but recommended)**: Required by `pydub` only for decoding/encoding MP3s. If you only process WAV or FLAC files, you don't need FFmpeg.
  - *On Windows*: Download the builds from [ffmpeg.org](https://ffmpeg.org/download.html) and add the `bin` directory to your system Environment PATH.
  - *On macOS*: `brew install ffmpeg`
  - *On Linux*: `sudo apt install ffmpeg`

---

## Installation

1. Clone or download this project to your local workspace.
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

*This will install `noisereduce`, `soundfile`, `numpy`, `scipy`, and `pydub`.*

---

## Usage Guide

The tool provides a simple command-line interface:

```bash
python noise_reducer.py <input_file> <output_file> [options]
```

### Positional Arguments
- `input_file`: Path to the input audio file (WAV, MP3, FLAC).
- `output_file`: Path where the cleaned audio file should be saved.

### Optional Arguments
- `-s`, `--strength`: Noise reduction strength (from `0.0` to `1.0`). 
  - `1.0` (Default): Maximum noise reduction.
  - `0.0`: No noise reduction.
  - `0.7` to `0.85`: Often provides a more natural sound by preserving subtle audio nuances.
- `-d`, `--noise-duration`: Duration in seconds at the beginning of the audio file to estimate the noise profile from. Default is `0.5` seconds.

### Quick Example

Reduce noise on `recording.wav` and save it to `recording_cleaned.wav` with a strength of `0.8` (80% reduction):

```bash
python noise_reducer.py recording.wav recording_cleaned.wav --strength 0.8
```

---

## Testing the Tool (Synthetic Test)

If you don't have a noisy audio file on hand, you can generate a synthetic test audio signal using the helper script `generate_test_audio.py`.

1. **Generate the noisy sample**:
   ```bash
   python generate_test_audio.py
   ```
   This will generate a stereo `test_noisy.wav` file containing a clean 440 Hz tone blended with strong Gaussian white noise. The first 0.75 seconds of the file is pure noise (no tone).

2. **Run the noise reduction**:
   ```bash
   python noise_reducer.py test_noisy.wav test_cleaned.wav -s 0.8 -d 0.5
   ```
   This will read the noise pattern from the first 0.5 seconds of the track, apply the noise reduction, and output `test_cleaned.wav`.

3. **Check the result**:
   Open and play `test_cleaned.wav` to hear the tone clearly with the background hiss significantly suppressed.

---

## Modular Architecture Overview

The source code (`noise_reducer.py`) is structured with modular functions for ease of understanding and reusability:

- **`load_audio(file_path)`**: Safely handles file reads. Standardizes audio arrays to float32 NumPy arrays and returns metadata.
- **`reduce_noise(audio_data, sr, prop_decrease, noise_duration)`**: Isolates the noise sample, transposes channels to match `noisereduce`'s expectation `(channels, samples)`, performs spectral gating, and transposes the cleaned signal back.
- **`save_audio(audio_data, sr, channels, output_path, backend)`**: Re-scales the audio data back to standard integer PCM limits and exports it using the corresponding format backend.
- **`main()`**: Manages CLI arguments, exception handling, formatting, and console output logs.

Made with ❤️ by me (Soutik)
