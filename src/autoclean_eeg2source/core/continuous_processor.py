"""Continuous data processor for EEG to source conversion."""

import os
import gc
import time
import logging
from typing import Optional, Dict, Any, List
import numpy as np
import mne

from .converter import SequentialProcessor
from .memory_manager import MemoryManager
from ..io.exceptions import ProcessingError

logger = logging.getLogger(__name__)


class ContinuousProcessor(SequentialProcessor):
    """Processor for continuous EEG data with chunking capabilities."""
    
    def __init__(self, 
                 memory_manager: Optional[MemoryManager] = None,
                 montage: str = "GSN-HydroCel-129",
                 resample_freq: float = 250,
                 lambda2: float = 1.0 / 9.0,
                 chunk_duration: float = 30.0,
                 overlap: float = 0.1,
                 filter_settings: Optional[Dict[str, Any]] = None):
        """
        Initialize continuous processor.
        
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
        chunk_duration : float
            Duration of each chunk in seconds
        overlap : float
            Overlap between chunks as fraction (0-1)
        filter_settings : dict, optional
            Filter settings with keys 'l_freq', 'h_freq', 'notch_freq'
        """
        super().__init__(
            memory_manager=memory_manager,
            montage=montage,
            resample_freq=resample_freq,
            lambda2=lambda2
        )
        
        self.chunk_duration = chunk_duration
        self.overlap = overlap
        self.filter_settings = filter_settings or {}
        
        # Processing metrics
        self.chunk_metrics = {
            'n_chunks': 0,
            'processing_times': [],
            'chunk_sizes': [],
            'memory_usage': []
        }
        
        logger.info(f"Initialized continuous processor with {chunk_duration}s chunks, "
                   f"{overlap*100}% overlap")
    
    def process_file(self, input_file: str, output_dir: str) -> Dict[str, Any]:
        """
        Process continuous EEG file with chunking.
        
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
        start_time = time.time()
        
        result = {
            'input_file': input_file,
            'status': 'failed',
            'output_file': None,
            'error': None,
            'chunk_metrics': None,
            'processing_time': None
        }
        
        try:
            # Reset chunk metrics
            self.chunk_metrics = {
                'n_chunks': 0,
                'processing_times': [],
                'chunk_sizes': [],
                'memory_usage': []
            }
            
            # Validate input file
            logger.info(f"Processing continuous data: {os.path.basename(input_file)}")
            report = self.validator.validate_file_pair(input_file)
            
            if report['file_type'] != 'raw':
                logger.warning(f"File type is {report['file_type']}, not raw - proceeding anyway")
            
            # Check memory before starting
            self.memory_manager.check_available()
            
            # Setup fsaverage if needed
            self._setup_fsaverage()
            
            # Load raw data
            logger.info("Loading continuous data...")
            raw = self.reader.read_raw_eeglab(input_file)
            
            # Pick EEG channels first to remove EOG, ECG, etc.
            logger.info("Selecting EEG channels only")
            
            # First set channel types for known EOG channels
            eog_channels = [ch for ch in raw.ch_names if any(eog in ch.upper() for eog in ['EOG', 'HEOG', 'VEOG'])]
            if eog_channels:
                logger.info(f"Setting {len(eog_channels)} EOG channels: {eog_channels}")
                raw.set_channel_types({ch: 'eog' for ch in eog_channels})
            
            # Now pick only EEG channels
            raw.pick("eeg")
            
            # Set montage
            logger.info(f"Setting montage: {self.montage}")
            raw.set_montage(
                mne.channels.make_standard_montage(self.montage), 
                match_case=False
            )
            
            # Apply preprocessing
            raw = self._preprocess_raw(raw)
            
            # Process in chunks
            logger.info("Processing continuous data in chunks...")
            all_stcs = self._process_chunks(raw)
            
            # Combine chunks into single source estimate
            logger.info("Combining chunks...")
            combined_stc = self._combine_chunks(all_stcs)
            
            # Convert to EEG format
            logger.info("Converting to EEG format...")
            output_raw, output_file = self.convert_raw_stc_to_eeg(
                combined_stc, output_dir, 
                subject_id=os.path.splitext(os.path.basename(input_file))[0]
            )
            
            # Update result
            result['status'] = 'success'
            result['output_file'] = output_file
            result['chunk_metrics'] = self.chunk_metrics.copy()
            result['processing_time'] = time.time() - start_time
            
            # Cleanup
            del raw, all_stcs, combined_stc, output_raw
            gc.collect()
            self.memory_manager.cleanup()
            
            logger.info(f"✓ Successfully processed continuous data: {output_file} "
                       f"in {result['processing_time']:.2f}s")
            
        except MemoryError as e:
            logger.error(f"Memory exhausted: {e}")
            result['error'] = str(e)
            gc.collect()
            self.memory_manager.cleanup()
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            result['error'] = str(e)
            
        return result
    
    def _preprocess_raw(self, raw: mne.io.Raw) -> mne.io.Raw:
        """Apply preprocessing to raw data."""
        logger.info("Applying preprocessing...")
        
        # Apply filters if specified
        if 'l_freq' in self.filter_settings or 'h_freq' in self.filter_settings:
            l_freq = self.filter_settings.get('l_freq', None)
            h_freq = self.filter_settings.get('h_freq', None)
            logger.info(f"Applying bandpass filter: {l_freq}-{h_freq} Hz")
            raw.filter(l_freq, h_freq, fir_design='firwin')
        
        # Apply notch filter if specified
        if 'notch_freq' in self.filter_settings:
            notch_freq = self.filter_settings['notch_freq']
            logger.info(f"Applying notch filter at {notch_freq} Hz")
            raw.notch_filter(notch_freq)
        
        # Resample if needed
        if raw.info['sfreq'] != self.resample_freq:
            logger.info(f"Resampling from {raw.info['sfreq']}Hz to {self.resample_freq}Hz")
            raw.resample(self.resample_freq)
        
        # Set EEG reference
        raw.set_eeg_reference(projection=True)
        
        return raw
    
    def _process_chunks(self, raw: mne.io.Raw) -> List[mne.SourceEstimate]:
        """Process raw data in chunks."""
        sfreq = raw.info['sfreq']
        
        # Calculate chunk parameters
        chunk_samples = int(self.chunk_duration * sfreq)
        overlap_samples = int(self.overlap * chunk_samples)
        step_samples = chunk_samples - overlap_samples
        
        # Calculate number of chunks
        n_chunks = int(np.ceil((len(raw.times) - overlap_samples) / step_samples))
        self.chunk_metrics['n_chunks'] = n_chunks
        
        logger.info(f"Processing {n_chunks} chunks of {self.chunk_duration}s each "
                   f"with {self.overlap*100}% overlap")
        
        all_stcs = []
        
        for i in range(n_chunks):
            chunk_start_time = time.time()
            
            # Calculate chunk boundaries
            start_sample = i * step_samples
            end_sample = min(start_sample + chunk_samples, len(raw.times))
            
            # Extract chunk
            chunk_raw = raw.copy().crop(
                tmin=raw.times[start_sample], 
                tmax=raw.times[end_sample-1]
            )
            
            logger.info(f"Processing chunk {i+1}/{n_chunks} "
                       f"({chunk_raw.times[0]:.1f}-{chunk_raw.times[-1]:.1f}s)")
            
            # Check memory
            self.memory_manager.check_available()
            
            try:
                # Process chunk
                stc = self._process_chunk(chunk_raw, i)
                all_stcs.append(stc)
                
                # Record metrics
                chunk_time = time.time() - chunk_start_time
                self.chunk_metrics['processing_times'].append(chunk_time)
                self.chunk_metrics['chunk_sizes'].append(chunk_raw.get_data().nbytes)
                self.chunk_metrics['memory_usage'].append(
                    self.memory_manager.get_memory_usage()
                )
                
                logger.debug(f"Chunk {i+1} processed in {chunk_time:.2f}s")
                
            except Exception as e:
                logger.error(f"Error processing chunk {i+1}: {e}")
                raise ProcessingError(f"Chunk {i+1} processing failed: {e}")
            
            # Cleanup chunk
            del chunk_raw
            gc.collect()
        
        return all_stcs
    
    def _process_chunk(self, chunk_raw: mne.io.Raw, chunk_idx: int = 0) -> mne.SourceEstimate:
        """Process a single chunk of raw data."""
        # Get forward solution
        fwd = self._get_forward_solution(chunk_raw.info)
        
        # Compute noise covariance
        noise_cov = mne.make_ad_hoc_cov(chunk_raw.info)
        
        # Create inverse operator
        inv = mne.minimum_norm.make_inverse_operator(
            chunk_raw.info, fwd, noise_cov, verbose=False
        )
        
        # Apply inverse solution
        stc = mne.minimum_norm.apply_inverse_raw(
            chunk_raw, inv, lambda2=self.lambda2, method="MNE", 
            pick_ori='normal', verbose=False
        )
        
        return stc
    
    def _combine_chunks(self, stcs: List[mne.SourceEstimate]) -> mne.SourceEstimate:
        """Combine multiple source estimates into one."""
        if len(stcs) == 1:
            return stcs[0]
        
        logger.info(f"Combining {len(stcs)} source estimate chunks...")
        
        # Handle overlap by averaging overlapping regions
        if self.overlap > 0:
            return self._combine_with_overlap(stcs)
        else:
            return self._combine_without_overlap(stcs)
    
    def _combine_without_overlap(self, stcs: List[mne.SourceEstimate]) -> mne.SourceEstimate:
        """Combine chunks without overlap (simple concatenation)."""
        # Concatenate time series
        combined_data = np.concatenate([stc.data for stc in stcs], axis=1)
        
        # Create time vector
        combined_times = []
        current_time = stcs[0].tmin
        
        for stc in stcs:
            chunk_times = stc.times
            combined_times.append(chunk_times + current_time - stc.tmin)
            current_time += (chunk_times[-1] - chunk_times[0])
        
        combined_times = np.concatenate(combined_times)
        
        # Create combined source estimate
        combined_stc = mne.SourceEstimate(
            data=combined_data,
            vertices=stcs[0].vertices,
            tmin=stcs[0].tmin,
            tstep=stcs[0].tstep,
            subject=stcs[0].subject
        )
        
        return combined_stc
    
    def _combine_with_overlap(self, stcs: List[mne.SourceEstimate]) -> mne.SourceEstimate:
        """Combine chunks with overlap using weighted averaging."""
        if len(stcs) == 1:
            return stcs[0]
        
        # Calculate overlap parameters
        overlap_samples = int(self.overlap * len(stcs[0].times))
        
        # Start with first chunk
        combined_data = stcs[0].data.copy()
        combined_times = stcs[0].times.copy()
        
        for i in range(1, len(stcs)):
            current_stc = stcs[i]
            
            if overlap_samples > 0:
                # Create weight ramp for smooth transition
                ramp = np.linspace(0, 1, overlap_samples)
                
                # Apply weighted averaging in overlap region
                overlap_start = len(combined_times) - overlap_samples
                combined_data[:, overlap_start:] = (
                    combined_data[:, overlap_start:] * (1 - ramp) +
                    current_stc.data[:, :overlap_samples] * ramp
                )
                
                # Append non-overlapping part
                if current_stc.data.shape[1] > overlap_samples:
                    combined_data = np.concatenate([
                        combined_data,
                        current_stc.data[:, overlap_samples:]
                    ], axis=1)
                    combined_times = np.concatenate([
                        combined_times,
                        current_stc.times[overlap_samples:]
                    ])
            else:
                # No overlap, simple concatenation
                combined_data = np.concatenate([combined_data, current_stc.data], axis=1)
                combined_times = np.concatenate([combined_times, current_stc.times])
        
        # Create combined source estimate
        combined_stc = mne.SourceEstimate(
            data=combined_data,
            vertices=stcs[0].vertices,
            tmin=stcs[0].tmin,
            tstep=stcs[0].tstep,
            subject=stcs[0].subject
        )
        
        return combined_stc
    
    def get_chunk_metrics(self) -> Dict[str, Any]:
        """Get chunk processing metrics."""
        metrics = self.chunk_metrics.copy()
        
        if metrics['processing_times']:
            metrics['avg_chunk_time'] = np.mean(metrics['processing_times'])
            metrics['total_processing_time'] = np.sum(metrics['processing_times'])
            metrics['max_chunk_time'] = np.max(metrics['processing_times'])
            metrics['min_chunk_time'] = np.min(metrics['processing_times'])
        
        if metrics['chunk_sizes']:
            metrics['avg_chunk_size_mb'] = np.mean(metrics['chunk_sizes']) / (1024**2)
            metrics['total_data_size_mb'] = np.sum(metrics['chunk_sizes']) / (1024**2)
        
        if metrics['memory_usage']:
            metrics['avg_memory_usage_mb'] = np.mean(metrics['memory_usage'])
            metrics['max_memory_usage_mb'] = np.max(metrics['memory_usage'])
        
        return metrics