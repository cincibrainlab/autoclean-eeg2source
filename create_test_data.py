"""Create test EEG data for validation."""

import numpy as np
import mne
import os

# Create synthetic EEG data
n_channels = 129
n_epochs = 10
n_times = 500
sfreq = 250

# Generate random data
data = np.random.randn(n_epochs, n_channels, n_times) * 1e-5

# Create channel names matching GSN-HydroCel-129
ch_names = [f'E{i+1}' for i in range(n_channels-1)] + ['Cz']
ch_types = ['eeg'] * n_channels

# Create info structure
info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)
info.set_montage(mne.channels.make_standard_montage('GSN-HydroCel-129'))

# Create events
events = np.array([[i * n_times, 0, 1] for i in range(n_epochs)])

# Create epochs
epochs = mne.EpochsArray(data, info, events)

# Save to EEGLAB format
output_dir = "test_data"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "test_epochs.set")

epochs.export(output_file, fmt='eeglab', overwrite=True)
print(f"Created test file: {output_file}")