#!/usr/bin/env python3
# Fixed EEG to Source Script (Properly Exporting SET Files)

import os
import glob
import numpy as np
import mne
from mne.datasets import fetch_fsaverage
import argparse
from loguru import logger
import sys
import gc

# Configure logger with a colorful format
logger.remove()
logger.add(
    sys.stdout,
    format="<level>{level: <8}</level> | <green>{time:YYYY-MM-DD HH:mm:ss}</green> | <cyan>{message}</cyan>",
    colorize=True,
    level="INFO"
)

# Function to convert source estimates to EEG SET format
def convert_stc_list_to_eeg(stc_list, subject='fsaverage', subjects_dir=None, output_dir=None, subject_id=None, events=None, event_id=None):
    """
    Convert a list of source estimates (stc) to EEG SET format with DK atlas regions as channels.
    
    Parameters
    ----------
    stc_list : list of SourceEstimate
        List of source time courses to convert, representing different trials or segments
    subject : str
        Subject name in FreeSurfer subjects directory (default: 'fsaverage')
    subjects_dir : str | None
        Path to FreeSurfer subjects directory
    output_dir : str | None
        Directory to save output files
    subject_id : str | None
        Subject identifier for file naming
    events : array, shape (n_events, 3) | None
        Events array to use when creating the epochs. If None, will create generic events.
    event_id : dict | None
        Dictionary mapping event types to IDs. If None, will use {1: 'event'}.
        
    Returns
    -------
    epochs : instance of mne.Epochs
        The converted EEG data in MNE Epochs format
    eeglab_out_file : str
        Path to the saved EEGLAB .set file
    """
    import os
    import numpy as np
    import mne
    import pandas as pd
    from mne.datasets import fetch_fsaverage
    
    # Set up paths
    if subjects_dir is None:
        subjects_dir = os.path.dirname(fetch_fsaverage())
    
    if output_dir is None:
        output_dir = os.getcwd()
    os.makedirs(output_dir, exist_ok=True)
    
    if subject_id is None:
        subject_id = 'stc_to_eeg'
    
    logger.info(f"Converting {len(stc_list)} source estimates to EEG epochs format for {subject_id}...")
    
    # Check if all stc objects have the same structure
    n_times_list = [stc.data.shape[1] for stc in stc_list]
    if len(set(n_times_list)) > 1:
        raise ValueError(f"Source estimates have different time dimensions: {n_times_list}")
    
    # Load the parcellation labels from DK atlas
    labels = mne.read_labels_from_annot(subject, parc='aparc', subjects_dir=subjects_dir)
    labels = [label for label in labels if 'unknown' not in label.name]
    
    # Extract time series for each label for each stc
    all_label_ts = []
    for stc in stc_list:
        # Extract label time courses for this stc
        label_ts = mne.extract_label_time_course(stc, labels, src=None, mode='mean', verbose=False)
        all_label_ts.append(label_ts)
    
    # Stack to get 3D array (n_epochs, n_regions, n_times)
    label_data = np.array(all_label_ts)
    
    # Get data properties from the first stc
    n_epochs = len(stc_list)
    n_regions = len(labels)
    n_times = n_times_list[0]
    sfreq = 1.0 / stc_list[0].tstep
    ch_names = [label.name for label in labels]
    
    # Create an array of channel positions based on region centroids
    ch_pos = {}
    for i, label in enumerate(labels):
        # Extract centroid of the label
        if hasattr(label, 'pos') and len(label.pos) > 0:
            centroid = np.mean(label.pos, axis=0)
        else:
            # If no positions available, create a point on a unit sphere
            phi = (1 + np.sqrt(5)) / 2
            idx = i + 1
            theta = 2 * np.pi * idx / phi**2
            phi = np.arccos(1 - 2 * ((idx % phi**2) / phi**2))
            centroid = np.array([
                np.sin(phi) * np.cos(theta),
                np.sin(phi) * np.sin(theta),
                np.cos(phi)
            ]) * 0.1  # Scaled to approximate head radius
        
        # Store in dictionary
        ch_pos[label.name] = centroid
    
    # Create MNE Info object with channel information
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=['eeg'] * n_regions)
    
    # Update channel positions
    for idx, ch_name in enumerate(ch_names):
        info['chs'][idx]['loc'][:3] = ch_pos[ch_name]
    
    # Create events array if not provided
    if events is None:
        events = np.array([[i, 0, 1] for i in range(n_epochs)])
    
    # Create event_id dictionary if not provided
    if event_id is None:
        event_id = {'event': 1}
    
    # Create MNE Epochs object from the extracted label time courses
    tmin = stc_list[0].tmin
    epochs = mne.EpochsArray(label_data, info, events=events, event_id=event_id, tmin=tmin)
    
    # Save to EEGLAB format
    eeglab_out_file = os.path.join(output_dir, f"{subject_id}_dk_regions.set")
    epochs.export(eeglab_out_file, fmt='eeglab')
    
    logger.info(f"Saved EEG SET file with {n_regions} channels (DK regions) to {eeglab_out_file}")
    
    # Create and save a montage file to help with visualization
    montage = mne.channels.make_dig_montage(ch_pos=ch_pos, coord_frame='head')
    montage_file = os.path.join(output_dir, f"{subject_id}_dk_montage.fif")
    montage.save(montage_file)
    
    logger.info(f"Saved montage file to {montage_file}")
    
    # Export additional metadata to help with interpretation
    region_info = {
        'names': ch_names,
        'hemisphere': ['lh' if '-lh' in name else 'rh' for name in ch_names],
        'centroid_x': [ch_pos[name][0] for name in ch_names],
        'centroid_y': [ch_pos[name][1] for name in ch_names],
        'centroid_z': [ch_pos[name][2] for name in ch_names]
    }
    
    info_file = os.path.join(output_dir, f"{subject_id}_region_info.csv")
    pd.DataFrame(region_info).to_csv(info_file, index=False)
    
    logger.info(f"Saved region information to {info_file}")
    
    return epochs, eeglab_out_file

# Function to process EEG files and convert them to source-localized SET format
def eeg_to_source_set(input_set_files, output_dir, montage="GSN-HydroCel-129", resample_freq=250):
    # Fetch the fsaverage brain model for source localization
    logger.info("Fetching fsaverage brain model...")
    fs_dir = fetch_fsaverage(verbose=False)
    src = mne.read_source_spaces(os.path.join(fs_dir, "bem", "fsaverage-ico-5-src.fif"))
    bem = os.path.join(fs_dir, "bem", "fsaverage-5120-5120-5120-bem-sol.fif")
    subjects_dir = os.path.dirname(fs_dir)

    # Read brain parcellation labels from the aparc atlas
    logger.info("Reading brain parcellation labels...")
    labels = mne.read_labels_from_annot('fsaverage', parc='aparc', subjects_dir=subjects_dir)
    labels = [label for label in labels if 'unknown' not in label.name]
    logger.info(f"Found {len(labels)} brain regions for source localization")

    # Iterate through each input EEG file
    total_files = len(input_set_files)
    for i, input_set_file in enumerate(input_set_files):
        try:
            subject_id = os.path.splitext(os.path.basename(input_set_file))[0]
            logger.info(f"Processing file {i+1}/{total_files}: {subject_id}")

            # Load EEG epochs from EEGLAB .set file
            logger.info(f"Loading epochs from {input_set_file}")
            epochs = mne.io.read_epochs_eeglab(input_set_file)

            # Set EEG montage for sensor positioning
            logger.info(f"Setting montage: {montage}")
            epochs.set_montage(mne.channels.make_standard_montage(montage), match_case=False)
            epochs.pick("eeg")

            # Optional resampling step
            logger.info(f"Resampling data to {resample_freq} Hz")
            epochs.resample(resample_freq)

            # Set EEG reference
            logger.info("Setting EEG reference with projection")
            epochs.set_eeg_reference(projection=True)

            # Compute forward solution (maps source space to sensor space)
            logger.info("Computing forward solution...")
            fwd = mne.make_forward_solution(
                epochs.info, trans="fsaverage", src=src, bem=bem, eeg=True, mindist=5.0, n_jobs=1  # Reduced parallelism to save memory
            )

            # Compute noise covariance matrix
            logger.info("Computing noise covariance matrix...")
            noise_cov = mne.make_ad_hoc_cov(epochs.info)

            # Create inverse operator (maps sensor space to source space)
            logger.info("Creating inverse operator...")
            inv = mne.minimum_norm.make_inverse_operator(epochs.info, fwd, noise_cov, verbose=False)

            # Apply inverse operator to EEG epochs to get source estimates (STCs)
            logger.info("Applying inverse solution to epochs...")
            stcs = mne.minimum_norm.apply_inverse_epochs(
                epochs, inv, lambda2=1.0 / 9.0, method="MNE", pick_ori='normal', verbose=False
            )

            # Convert source estimates to EEG format with brain regions as channels
            logger.info("Converting source estimates to EEG format...")
            # THIS IS THE CRUCIAL FIX: Actually call the conversion function
            _, output_set_file = convert_stc_list_to_eeg(
                stc_list=stcs,
                subject='fsaverage',
                subjects_dir=subjects_dir,
                output_dir=output_dir,
                subject_id=subject_id
            )

            # Free memory
            del epochs, fwd, noise_cov, inv, stcs
            gc.collect()

            # Log completion message for the current file
            logger.success(f"Successfully saved source-localized file: {output_set_file}")
            
        except Exception as e:
            logger.error(f"Error processing file {input_set_file}: {str(e)}")
            continue

# Main execution block with improved memory handling
def main():
    parser = argparse.ArgumentParser(description="EEG to Source-localized SET Converter")
    parser.add_argument('--input_path', default="./Input", help='Input EEG .set file or directory containing multiple .set files')
    parser.add_argument('--output_dir', default="./Output", help='Directory to store output files')
    parser.add_argument('--montage', default="GSN-HydroCel-129", help='EEG montage type for sensor positioning')
    parser.add_argument('--resample_freq', type=float, default=250, help='Optional resampling frequency (Hz)')
    parser.add_argument('--recursive', action='store_true', help='Search recursively in subdirectories')

    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Collect input EEG files
    if os.path.isdir(args.input_path):
        if args.recursive:
            input_set_files = glob.glob(os.path.join(args.input_path, "**", "*.set"), recursive=True)
        else:
            input_set_files = glob.glob(os.path.join(args.input_path, "*.set"))
        logger.info(f"Found {len(input_set_files)} .set files")
    else:
        input_set_files = [args.input_path]
        logger.info(f"Processing single file: {args.input_path}")

    # Start processing
    logger.info("=" * 80)
    logger.info("Starting EEG to source localization conversion...")
    logger.info("=" * 80)
    
    # Process files one by one to manage memory better
    for file_path in input_set_files:
        try:
            eeg_to_source_set([file_path], args.output_dir, montage=args.montage, resample_freq=args.resample_freq)
            # Force garbage collection after each file
            gc.collect()
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            continue

    logger.success("=" * 80)
    logger.success("All files processed successfully!")
    logger.success("=" * 80)

if __name__ == '__main__':
    main()