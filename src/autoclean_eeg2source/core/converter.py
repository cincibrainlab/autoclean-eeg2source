"""Main sequential processing pipeline for EEG to source conversion."""

import os
import gc
import logging
from typing import Optional, Dict, Any
import numpy as np
import mne
from mne.datasets import fetch_fsaverage
import pandas as pd

from ..io.eeglab_reader import EEGLABReader
from ..io.validators import EEGLABValidator
from .memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class SequentialProcessor:
    """Sequential processor for EEG to source localization conversion."""
    
    def __init__(self, 
                 memory_manager: Optional[MemoryManager] = None,
                 montage: str = "GSN-HydroCel-129",
                 resample_freq: float = 250,
                 lambda2: float = 1.0 / 9.0):
        """
        Initialize sequential processor.
        
        Parameters
        ----------
        memory_manager : MemoryManager, optional
            Memory manager instance
        montage : str
            EEG montage name
        resample_freq : float
            Target sampling frequency
        lambda2 : float
            Regularization parameter for inverse solution
        """
        self.memory_manager = memory_manager or MemoryManager()
        self.montage = montage
        self.resample_freq = resample_freq
        self.lambda2 = lambda2
        
        # Cache for forward solution to avoid recomputation
        self.forward_solution = None
        self.fsaverage_src = None
        self.fsaverage_bem = None
        self.labels = None
        
        # Initialize components
        self.reader = EEGLABReader(memory_manager=self.memory_manager)
        self.validator = EEGLABValidator()
        
        logger.info(f"Initialized processor with montage={montage}, resample={resample_freq}Hz")
        
    def _setup_fsaverage(self):
        """Setup fsaverage brain model and source space."""
        if self.fsaverage_src is not None:
            return  # Already setup
            
        logger.info("Setting up fsaverage brain model...")
        
        # Fetch fsaverage files
        fs_dir = fetch_fsaverage(verbose=False)
        subjects_dir = os.path.dirname(fs_dir)
        
        # Load source space
        self.fsaverage_src = mne.read_source_spaces(
            os.path.join(fs_dir, "bem", "fsaverage-ico-5-src.fif")
        )
        
        # Load BEM solution
        self.fsaverage_bem = os.path.join(fs_dir, "bem", "fsaverage-5120-5120-5120-bem-sol.fif")
        
        # Load labels for DK atlas
        self.labels = mne.read_labels_from_annot(
            'fsaverage', parc='aparc', subjects_dir=subjects_dir
        )
        self.labels = [label for label in self.labels if 'unknown' not in label.name]
        
        logger.info(f"Loaded {len(self.labels)} brain regions from DK atlas")
        
    def _get_forward_solution(self, info: mne.Info) -> mne.Forward:
        """Get cached or compute forward solution."""
        if self.forward_solution is not None:
            # Check if montage matches
            if len(self.forward_solution['info']['ch_names']) == len(info['ch_names']):
                logger.debug("Using cached forward solution")
                return self.forward_solution
        
        logger.info("Computing forward solution...")
        self.memory_manager.check_available()
        
        # Compute forward solution
        self.forward_solution = mne.make_forward_solution(
            info, 
            trans="fsaverage", 
            src=self.fsaverage_src, 
            bem=self.fsaverage_bem,
            eeg=True, 
            mindist=5.0, 
            n_jobs=1  # Avoid parallel processing for memory efficiency
        )
        
        self.memory_manager.log_memory_status("After forward solution")
        return self.forward_solution
        
    def process_file(self, input_file: str, output_dir: str) -> Dict[str, Any]:
        """
        Process single EEG file with memory monitoring.
        
        Parameters
        ----------
        input_file : str
            Path to input .set file
        output_dir : str
            Output directory
            
        Returns
        -------
        result : dict
            Processing result with status and output file
        """
        result = {
            'input_file': input_file,
            'status': 'failed',
            'output_file': None,
            'error': None
        }
        
        try:
            # Validate input file
            logger.info(f"Processing: {os.path.basename(input_file)}")
            report = self.validator.validate_file_pair(input_file)
                       
            # Check memory before starting
            self.memory_manager.check_available()
            
            # Setup fsaverage if needed
            self._setup_fsaverage()
                        
            # Load epochs
            if report['file_type'] == 'epochs':
                epochs = self.reader.read_epochs(input_file)
            else:
                epochs = self.reader.read_raw(input_file)
            
            # Set montage
            logger.info(f"Setting montage: {self.montage}")
            epochs.set_montage(
                mne.channels.make_standard_montage(self.montage), 
                match_case=False
            )
            epochs.pick("eeg")
            
            # Resample if needed
            if epochs.info['sfreq'] != self.resample_freq:
                logger.info(f"Resampling from {epochs.info['sfreq']}Hz to {self.resample_freq}Hz")
                epochs.resample(self.resample_freq)
            
            # Set EEG reference
            epochs.set_eeg_reference(projection=True)
            
            # Get forward solution
            fwd = self._get_forward_solution(epochs.info)
            
            # Compute noise covariance
            logger.info("Computing noise covariance...")
            noise_cov = mne.make_ad_hoc_cov(epochs.info)
            
            # Create inverse operator
            logger.info("Creating inverse operator...")
            inv = mne.minimum_norm.make_inverse_operator(
                epochs.info, fwd, noise_cov, verbose=False
            )

            
            # Apply inverse solution
            logger.info("Applying inverse solution to epochs...")
            if report['file_type'] == 'epochs':
                stcs = mne.minimum_norm.apply_inverse_epochs(
                        epochs, inv, lambda2=self.lambda2, method="MNE", 
                        pick_ori='normal', verbose=False
                    )
            else:
                if report['file_type'] == 'raw':
                    stcs = mne.minimum_norm.apply_inverse_raw(
                        epochs, inv, lambda2=self.lambda2, method="MNE", 
                        pick_ori='normal', verbose=False
                    )
            
            # Convert to EEG format with DK regions
            logger.info("Converting source estimates to EEG format...")
            if report['file_type'] == 'epochs':
                output_epochs, output_file = self._convert_stc_to_eeg(
                    stcs, output_dir, 
                    subject_id=os.path.splitext(os.path.basename(input_file))[0],
                    original_epochs=epochs
                )
            else:
                output_epochs, output_file = self.convert_raw_stc_to_eeg(
                    stcs, output_dir, 
                    subject_id=os.path.splitext(os.path.basename(input_file))[0]
                )
            
            # Update result
            result['status'] = 'success'
            result['output_file'] = output_file
            
            # Cleanup
            del epochs, inv, stcs, output_epochs
            gc.collect()
            self.memory_manager.cleanup()
            
            logger.info(f"✓ Successfully processed: {output_file}")
            
        except MemoryError as e:
            logger.error(f"Memory exhausted: {e}")
            result['error'] = str(e)
            # Try to cleanup
            gc.collect()
            self.memory_manager.cleanup()
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            result['error'] = str(e)
            
        return result
        
    def _convert_stc_to_eeg(self, stc_list: list, output_dir: str, subject_id: str, original_epochs: mne.Epochs = None) -> tuple:
        """
        Convert source estimates to EEG format with DK atlas regions.
        
        This is adapted from the original convert_stc_list_to_eeg function.
        """
        logger.info(f"Converting {len(stc_list)} source estimates to EEG format...")
        
        # Extract time series for each label
        all_label_ts = []
        for stc in stc_list:
            # Extract label time courses
            label_ts = mne.extract_label_time_course(
                stc, self.labels, src=self.fsaverage_src, 
                mode='mean', verbose=False
            )
            all_label_ts.append(label_ts)
        
        # Stack to get 3D array (n_epochs, n_regions, n_times)
        label_data = np.array(all_label_ts)
        
        # Get properties
        n_epochs = len(stc_list)
        n_regions = len(self.labels)
        n_times = stc_list[0].data.shape[1]
        sfreq = 1.0 / stc_list[0].tstep
        ch_names = [label.name for label in self.labels]
        
        # Create channel positions
        ch_pos = {}
        for i, label in enumerate(self.labels):
            # Extract centroid of the label
            if hasattr(label, 'pos') and len(label.pos) > 0:
                centroid = np.mean(label.pos, axis=0)
            else:
                # If no positions available, create a point on a unit sphere using golden ratio
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
        
        # Create MNE Info
        info = mne.create_info(
            ch_names=ch_names, 
            sfreq=sfreq, 
            ch_types=['eeg'] * n_regions
        )
        
        # Update channel positions
        for idx, ch_name in enumerate(ch_names):
            info['chs'][idx]['loc'][:3] = ch_pos[ch_name]
        
        # Create epochs with proper event handling
        if original_epochs is not None and hasattr(original_epochs, 'event_id') and hasattr(original_epochs, 'events'):
            # Preserve original event structure
            event_id = original_epochs.event_id.copy()
            # Use proper sample indices based on epoch timing to avoid EEGLABIO issues
            if len(original_epochs.events) == n_epochs:
                # Create realistic sample indices with padding to avoid EEGLABIO issues
                events = []
                epoch_duration = stc_list[0].times[-1] - stc_list[0].times[0]
                epoch_length_samples = int(sfreq * epoch_duration)
                # Add padding between epochs to prevent EEGLABIO from adding dummy events
                padding_samples = int(sfreq * 0.1)  # 100ms padding
                epoch_spacing = epoch_length_samples + padding_samples
                
                for i in range(n_epochs):
                    sample_idx = i * epoch_spacing
                    events.append([sample_idx, 0, original_epochs.events[i, 2]])
                events = np.array(events)
            else:
                # Fallback: use the first event code from original data
                first_event_code = list(event_id.values())[0]
                events = []
                epoch_duration = stc_list[0].times[-1] - stc_list[0].times[0]
                epoch_length_samples = int(sfreq * epoch_duration)
                padding_samples = int(sfreq * 0.1)  # 100ms padding
                epoch_spacing = epoch_length_samples + padding_samples
                
                for i in range(n_epochs):
                    sample_idx = i * epoch_spacing
                    events.append([sample_idx, 0, first_event_code])
                events = np.array(events)
        else:
            # Default fallback
            events = []
            epoch_duration = stc_list[0].times[-1] - stc_list[0].times[0]
            epoch_length_samples = int(sfreq * epoch_duration)
            padding_samples = int(sfreq * 0.1)  # 100ms padding
            epoch_spacing = epoch_length_samples + padding_samples
            
            for i in range(n_epochs):
                sample_idx = i * epoch_spacing
                events.append([sample_idx, 0, 1])
            events = np.array(events)
            event_id = {'event': 1}
        tmin = stc_list[0].tmin
        
        epochs = mne.EpochsArray(
            label_data, info, events=events, 
            event_id=event_id, tmin=tmin
        )
        
        # Save to EEGLAB format
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{subject_id}_dk_regions.set")
        epochs.export(output_file, fmt='eeglab', overwrite=True)
        
        logger.info(f"Saved {n_regions} regions to {output_file}")
        
        # Save metadata
        self._save_metadata(output_dir, subject_id, ch_names, ch_pos)
        
        return epochs, output_file
        
    def _save_metadata(self, output_dir: str, subject_id: str, 
                      ch_names: list, ch_pos: dict):
        """Save region metadata to CSV file."""
        region_info = {
            'names': ch_names,
            'hemisphere': ['lh' if '-lh' in name else 'rh' for name in ch_names],
            'x': [ch_pos[name][0] for name in ch_names],
            'y': [ch_pos[name][1] for name in ch_names],
            'z': [ch_pos[name][2] for name in ch_names]
        }
        
        info_file = os.path.join(output_dir, f"{subject_id}_region_info.csv")
        pd.DataFrame(region_info).to_csv(info_file, index=False)
        logger.debug(f"Saved region info to {info_file}")

    def convert_raw_stc_to_eeg(self, stc: mne.SourceEstimate, output_dir: str, subject_id: str) -> tuple:
        """
        Convert a single raw SourceEstimate to EEG format with DK atlas regions.
        
        Parameters
        ----------
        stc : mne.SourceEstimate
            Source estimate from continuous/raw data
        output_dir : str
            Directory to save output files
        subject_id : str
            Subject identifier for naming output files
            
        Returns
        -------
        raw : mne.io.Raw
            Raw object with source time courses
        output_file : str
            Path to saved output file
        """
        logger.info("Converting raw source estimate to EEG format...")
        
        # Extract time series for each label
        logger.info(f"Extracting time courses for {len(self.labels)} regions...")
        label_ts = mne.extract_label_time_course(
            stc, self.labels, src=self.fsaverage_src, 
            mode='mean', verbose=False
        )
        
        # Get properties
        n_regions = len(self.labels)
        n_times = stc.data.shape[1]
        sfreq = 1.0 / stc.tstep
        ch_names = [label.name for label in self.labels]
        
        # Create channel positions
        ch_pos = {}
        for i, label in enumerate(self.labels):
            # Extract centroid of the label
            if hasattr(label, 'pos') and len(label.pos) > 0:
                centroid = np.mean(label.pos, axis=0)
            else:
                # If no positions available, create a point on a unit sphere using golden ratio
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
        
        # Create MNE Info
        info = mne.create_info(
            ch_names=ch_names, 
            sfreq=sfreq, 
            ch_types=['eeg'] * n_regions
        )
        
        # Update channel positions
        for idx, ch_name in enumerate(ch_names):
            info['chs'][idx]['loc'][:3] = ch_pos[ch_name]
        
        # Create Raw object
        raw = mne.io.RawArray(
            label_ts, info, first_samp=0,
            verbose=False
        )
        
        # Save to EEGLAB format
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{subject_id}_dk_regions.set")
        raw.export(output_file, fmt='eeglab', overwrite=True)
        
        logger.info(f"Saved {n_regions} regions to {output_file}")
        
        # Save metadata
        self._save_metadata(output_dir, subject_id, ch_names, ch_pos)
        
        return raw, output_file
