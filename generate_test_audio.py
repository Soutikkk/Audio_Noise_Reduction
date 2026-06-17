#!/usr/bin/env python3
"""
Synthetic Noisy Audio Generator
-------------------------------
Generates a test WAV file with a pure sine wave and added Gaussian white noise.
This is used to verify the functionality of the audio noise reducer script.
"""

import numpy as np
import soundfile as sf

def main():
    sr = 44100  # Sample rate (Hz)
    duration = 4.0  # Duration in seconds
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    
    # 1. Generate a clean signal (e.g., a 440 Hz A tone)
    # Shape is (samples,)
    clean_signal = 0.5 * np.sin(2 * np.pi * 440.0 * t)
    
    # 2. Add some silent lead-in noise (first 0.75 seconds contains only noise)
    noise_only_duration = 0.75
    noise_only_samples = int(sr * noise_only_duration)
    
    # Make clean signal silent during the lead-in to serve as a pure noise segment
    clean_signal[:noise_only_samples] = 0.0
    
    # 3. Generate Gaussian white noise
    noise = 0.15 * np.random.normal(0, 1, size=clean_signal.shape)
    
    # 4. Mix clean signal with noise
    noisy_signal = clean_signal + noise
    
    # 5. Make it stereo (two channels) to test multi-channel capabilities
    # Left channel has the mix, Right channel has a slightly phase-shifted version
    right_channel = 0.5 * np.sin(2 * np.pi * 440.0 * t + np.pi/4)
    right_channel[:noise_only_samples] = 0.0
    noisy_right = right_channel + noise
    
    # Stack channels to shape (samples, channels)
    stereo_noisy = np.column_stack((noisy_signal, noisy_right))
    
    # Save the synthetic audio file
    output_filename = "test_noisy.wav"
    sf.write(output_filename, stereo_noisy, sr)
    print(f"Created synthetic noisy audio: {output_filename}")
    print(f" - Duration: {duration} seconds (first {noise_only_duration}s is pure noise)")
    print(f" - Sample Rate: {sr} Hz")
    print(f" - Channels: 2 (Stereo)")

if __name__ == "__main__":
    main()
