#!/usr/bin/env python3
"""
Audio Noise Reducer
-------------------
A modular command-line tool to reduce background noise from audio files (WAV, MP3, FLAC)
using the noisereduce, soundfile, numpy, and pydub libraries.

Usage:
    python noise_reducer.py input.wav output.wav --strength 0.8
"""

import os
import sys
import argparse
import numpy as np
import soundfile as sf
from pydub import AudioSegment

def load_audio(file_path):
    """
    Loads an audio file and returns a tuple (audio_data, sample_rate, channels, backend).
    Supports WAV, FLAC, and MP3.
    
    Parameters:
    - file_path: str, path to the input audio file
    
    Returns:
    - audio_data: np.ndarray, shape (samples,) or (samples, channels)
    - sr: int, sample rate (Hz)
    - channels: int, number of audio channels
    - backend: str, "soundfile" or "pydub"
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
        
    ext = os.path.splitext(file_path.lower())[1]
    if ext not in ['.wav', '.mp3', '.flac']:
        raise ValueError(f"Unsupported audio format '{ext}'. Only WAV, MP3, and FLAC are supported.")
        
    # Attempt to load using soundfile first (very efficient for WAV/FLAC, no ffmpeg required)
    if ext in ['.wav', '.flac']:
        try:
            print(f"Loading '{file_path}' using soundfile...")
            data, sr = sf.read(file_path)
            data = data.astype(np.float32)
            channels = 1 if len(data.shape) == 1 else data.shape[1]
            return data, sr, channels, "soundfile"
        except Exception as e:
            print(f"[Warning] soundfile failed to load WAV/FLAC: {e}. Falling back to pydub...")
            
    # Fallback/MP3 using pydub
    try:
        print(f"Loading '{file_path}' using pydub...")
        segment = AudioSegment.from_file(file_path)
        sr = segment.frame_rate
        channels = segment.channels
        sample_width = segment.sample_width
        
        # Get raw samples as numpy array
        samples = np.array(segment.get_array_of_samples())
        
        # Reshape array for multi-channel audio
        if channels > 1:
            # pydub interleaves samples so shape is (samples * channels,)
            samples = samples.reshape((-1, channels))
            
        # Standardize data to float32 range [-1.0, 1.0] based on bit depth
        if sample_width == 1:
            samples = (samples.astype(np.float32) - 128) / 128.0
        elif sample_width == 2:
            samples = samples.astype(np.float32) / 32768.0
        elif sample_width == 4:
            samples = samples.astype(np.float32) / 2147483648.0
        else:
            samples = samples.astype(np.float32) / np.max(np.abs(samples))
            
        return samples, sr, channels, "pydub"
    except Exception as e:
        if "ffmpeg" in str(e).lower() or "ffprobe" in str(e).lower():
            raise RuntimeError(
                f"Failed to load audio file '{file_path}'.\n"
                f"For formats like MP3/FLAC, you may need to install FFmpeg.\n"
                f"Original error: {e}"
            )
        else:
            raise RuntimeError(f"Failed to load audio file '{file_path}': {e}")

def reduce_noise(audio_data, sr, prop_decrease=1.0, noise_duration=0.5):
    """
    Applies noise reduction to the audio data using the noisereduce library.
    Estimates the noise profile from the first `noise_duration` seconds of the audio.
    
    Parameters:
    - audio_data: np.ndarray, shape (samples,) or (samples, channels)
    - sr: int, sample rate (Hz)
    - prop_decrease: float, noise reduction strength (0.0 to 1.0)
    - noise_duration: float, duration in seconds to estimate noise (default 0.5)
    
    Returns:
    - cleaned_audio: np.ndarray, same shape as input
    """
    import noisereduce as nr
    
    # Calculate number of samples for the noise estimation window
    noise_samples = int(sr * noise_duration)
    if noise_samples > len(audio_data):
        raise ValueError(
            f"Audio file duration ({len(audio_data)/sr:.2f}s) is shorter than the "
            f"requested noise estimation duration ({noise_duration}s)."
        )
        
    print(f"Estimating noise profile from first {noise_duration}s ({noise_samples} samples)...")
    
    # Check if stereo/multichannel
    is_stereo = len(audio_data.shape) > 1
    
    # noisereduce expects shape (channels, samples) for multi-channel.
    if is_stereo:
        y = audio_data.T
        y_noise = y[:, :noise_samples]
    else:
        y = audio_data
        y_noise = y[:noise_samples]
        
    print(f"Reducing noise with strength factor of {prop_decrease:.2f}...")
    cleaned_y = nr.reduce_noise(
        y=y,
        sr=sr,
        y_noise=y_noise,
        prop_decrease=prop_decrease
    )
    
    # Restore original shape (samples, channels)
    if is_stereo:
        return cleaned_y.T
    return cleaned_y

def save_audio(audio_data, sr, channels, output_path, backend="soundfile"):
    """
    Saves the cleaned audio array to the target output file.
    
    Parameters:
    - audio_data: np.ndarray, shape (samples,) or (samples, channels)
    - sr: int, sample rate
    - channels: int, number of audio channels
    - output_path: str, path to the output audio file
    - backend: str, "soundfile" or "pydub"
    """
    ext = os.path.splitext(output_path.lower())[1]
    if ext not in ['.wav', '.mp3', '.flac']:
        raise ValueError(f"Unsupported output audio format '{ext}'. Only WAV, MP3, and FLAC are supported.")
        
    # Use soundfile if backend is soundfile and format is WAV/FLAC
    if backend == "soundfile" and ext in ['.wav', '.flac']:
        try:
            print(f"Saving '{output_path}' using soundfile...")
            sf.write(output_path, audio_data, sr)
            return
        except Exception as e:
            print(f"[Warning] soundfile failed to save: {e}. Falling back to pydub...")
            
    # pydub fallback or saving MP3
    try:
        print(f"Saving '{output_path}' using pydub...")
        # Convert float32 array back to 16-bit signed integer
        int_data = (audio_data * 32768.0).clip(-32768, 32767).astype(np.int16)
        
        if channels > 1:
            # Flatten to interleave channels
            raw_bytes = int_data.flatten().tobytes()
        else:
            raw_bytes = int_data.tobytes()
            
        segment = AudioSegment(
            data=raw_bytes,
            sample_width=2,
            frame_rate=sr,
            channels=channels
        )
        
        format_name = ext.replace('.', '')
        segment.export(output_path, format=format_name)
    except Exception as e:
        raise RuntimeError(
            f"Failed to save audio file to '{output_path}'.\n"
            f"For formats like MP3/FLAC, you may need to install FFmpeg.\n"
            f"Original error: {e}"
        )

def main():
    parser = argparse.ArgumentParser(
        description="A professional, command-line utility for audio noise reduction using noisereduce."
    )
    parser.add_argument("input_file", help="Path to the input WAV, MP3, or FLAC file.")
    parser.add_argument("output_file", help="Path where the cleaned WAV, MP3, or FLAC file should be saved.")
    parser.add_argument(
        "-s", "--strength",
        type=float,
        default=1.0,
        help="Reduction strength. A value from 0.0 (no reduction) to 1.0 (maximum reduction). Default is 1.0."
    )
    parser.add_argument(
        "-d", "--noise-duration",
        type=float,
        default=0.5,
        help="Duration in seconds at the beginning of the audio file to estimate noise from. Default is 0.5 seconds."
    )
    
    args = parser.parse_args()
    
    # Validate strength parameter range
    if not (0.0 <= args.strength <= 1.0):
        print(f"Error: Strength factor must be between 0.0 and 1.0, got {args.strength}.", file=sys.stderr)
        sys.exit(1)
        
    # Validate duration parameter
    if args.noise_duration <= 0.0:
        print(f"Error: Noise duration must be positive, got {args.noise_duration}.", file=sys.stderr)
        sys.exit(1)
        
    print("=" * 60)
    print("                 Audio Noise Reducer CLI")
    print("=" * 60)
    
    try:
        # 1. Load Audio
        print(f"[*] Task 1/3: Loading audio...")
        audio_data, sr, channels, backend = load_audio(args.input_file)
        duration = len(audio_data) / sr
        print(f"    Loaded successfully! Duration: {duration:.2f}s | Sample Rate: {sr}Hz | Channels: {channels}")
        
        # 2. Reduce Noise
        print(f"[*] Task 2/3: Applying noise reduction...")
        cleaned_audio = reduce_noise(
            audio_data=audio_data,
            sr=sr,
            prop_decrease=args.strength,
            noise_duration=args.noise_duration
        )
        
        # 3. Save Audio
        print(f"[*] Task 3/3: Saving output file...")
        save_audio(
            audio_data=cleaned_audio,
            sr=sr,
            channels=channels,
            output_path=args.output_file,
            backend=backend
        )

        
        print("\n[+] Noise reduction completed successfully!")
        print(f"    Cleaned file saved at: {args.output_file}")
        print("=" * 60)

    
    except Exception as e:
        print(f"\n[!] Error: {e}", file=sys.stderr)
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
