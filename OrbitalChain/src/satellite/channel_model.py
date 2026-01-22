"""
Channel Model Module for OrbitalChain
=====================================

Implements Rician fading channel model for satellite-to-ground and
inter-satellite links (ISL).

References:
    - 3GPP TR 38.811 - Study on NR to support non-terrestrial networks
    - OrbitalChain Paper, Section 4.3
"""

import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass


# Physical constants
SPEED_OF_LIGHT = 299792.458  # km/s
BOLTZMANN = 1.38e-23  # J/K


@dataclass
class LinkParameters:
    """Parameters for a communication link."""
    frequency: float  # Hz
    transmit_power: float  # dBW
    transmit_gain: float  # dBi
    receive_gain: float  # dBi
    system_noise_temp: float  # K
    bandwidth: float  # Hz
    
    @property
    def wavelength(self) -> float:
        """Wavelength in km."""
        return SPEED_OF_LIGHT / self.frequency * 1e3  # Convert to km


class RicianChannel:
    """
    Rician fading channel model for satellite links.
    
    The Rician distribution models a channel with a dominant
    line-of-sight (LoS) component and scattered components.
    
    h = sqrt(K/(K+1)) * h_LoS + sqrt(1/(K+1)) * h_NLoS
    
    where K is the Rician K-factor.
    """
    
    def __init__(
        self,
        k_factor: float = 10.0,
        doppler_shift: float = 0.0
    ):
        """
        Initialize Rician channel.
        
        Args:
            k_factor: Rician K-factor (ratio of LoS to scattered power)
            doppler_shift: Doppler frequency shift (Hz)
        """
        self.k_factor = k_factor
        self.doppler_shift = doppler_shift
    
    def generate_coefficient(self, num_samples: int = 1) -> np.ndarray:
        """
        Generate Rician fading coefficient(s).
        
        Args:
            num_samples: Number of samples to generate
        
        Returns:
            Complex channel coefficient(s)
        """
        # LoS component (deterministic)
        h_los = np.sqrt(self.k_factor / (self.k_factor + 1))
        
        # NLoS component (Rayleigh)
        h_nlos_real = np.random.randn(num_samples) / np.sqrt(2)
        h_nlos_imag = np.random.randn(num_samples) / np.sqrt(2)
        h_nlos = (h_nlos_real + 1j * h_nlos_imag) * np.sqrt(1 / (self.k_factor + 1))
        
        # Combined channel
        h = h_los + h_nlos
        
        return h
    
    def get_fading_loss(self, num_samples: int = 1) -> np.ndarray:
        """
        Get fading loss in dB.
        
        Args:
            num_samples: Number of samples
        
        Returns:
            Fading loss in dB (negative values = attenuation)
        """
        h = self.generate_coefficient(num_samples)
        power = np.abs(h) ** 2
        return 10 * np.log10(power)
    
    @staticmethod
    def compute_k_factor(elevation: float) -> float:
        """
        Estimate K-factor based on elevation angle.
        
        Higher elevation = stronger LoS = higher K-factor.
        
        Args:
            elevation: Elevation angle in degrees
        
        Returns:
            Estimated K-factor
        """
        # Empirical model based on elevation
        if elevation < 10:
            return 1.0  # Low elevation, multipath dominant
        elif elevation < 30:
            return 5.0 + (elevation - 10) * 0.5
        elif elevation < 60:
            return 15.0 + (elevation - 30) * 0.3
        else:
            return 24.0 + (elevation - 60) * 0.1


class ISLChannel:
    """
    Inter-Satellite Link channel model.
    
    ISL channels typically have excellent LoS conditions
    with minimal atmospheric effects.
    """
    
    def __init__(
        self,
        wavelength_nm: float = 1550.0,  # Optical ISL
        pointing_error_urad: float = 1.0
    ):
        """
        Initialize ISL channel.
        
        Args:
            wavelength_nm: Wavelength in nanometers (for optical ISL)
            pointing_error_urad: Pointing error in microradians
        """
        self.wavelength = wavelength_nm * 1e-9  # Convert to meters
        self.pointing_error = pointing_error_urad * 1e-6  # Convert to radians
    
    def compute_geometric_loss(self, distance: float) -> float:
        """
        Compute geometric spreading loss.
        
        Args:
            distance: Link distance in km
        
        Returns:
            Geometric loss in dB
        """
        # Free space path loss for optical
        distance_m = distance * 1000
        loss = 20 * np.log10(4 * np.pi * distance_m / self.wavelength)
        return loss
    
    def compute_pointing_loss(self, beam_divergence: float = 10e-6) -> float:
        """
        Compute pointing loss due to misalignment.
        
        Args:
            beam_divergence: Beam divergence half-angle (radians)
        
        Returns:
            Pointing loss in dB
        """
        # Gaussian beam model
        theta_ratio = self.pointing_error / beam_divergence
        loss = 4.343 * theta_ratio ** 2  # dB
        return loss
    
    def compute_total_loss(self, distance: float) -> float:
        """
        Compute total ISL loss.
        
        Args:
            distance: Link distance in km
        
        Returns:
            Total loss in dB
        """
        geom_loss = self.compute_geometric_loss(distance)
        point_loss = self.compute_pointing_loss()
        return geom_loss + point_loss


def compute_path_loss(
    distance: float,
    frequency: float,
    elevation: float = 90.0
) -> float:
    """
    Compute path loss for satellite link.
    
    Args:
        distance: Distance in km
        frequency: Frequency in Hz
        elevation: Elevation angle in degrees
    
    Returns:
        Path loss in dB
    """
    # Free space path loss
    wavelength = SPEED_OF_LIGHT * 1e3 / frequency  # meters
    distance_m = distance * 1000
    fspl = 20 * np.log10(4 * np.pi * distance_m / wavelength)
    
    # Atmospheric loss (simplified model based on elevation)
    if elevation < 10:
        atm_loss = 2.0  # dB
    elif elevation < 30:
        atm_loss = 0.5
    else:
        atm_loss = 0.2
    
    return fspl + atm_loss


def compute_link_budget(
    params: LinkParameters,
    distance: float,
    elevation: float,
    include_fading: bool = True
) -> dict:
    """
    Compute link budget for satellite link.
    
    Args:
        params: Link parameters
        distance: Distance in km
        elevation: Elevation angle in degrees
        include_fading: Whether to include fading margin
    
    Returns:
        Dictionary with link budget breakdown
    """
    # Path loss
    path_loss = compute_path_loss(distance, params.frequency, elevation)
    
    # EIRP
    eirp = params.transmit_power + params.transmit_gain
    
    # Received power
    received_power = eirp - path_loss + params.receive_gain
    
    # Noise power
    noise_power = 10 * np.log10(BOLTZMANN * params.system_noise_temp * params.bandwidth)
    
    # SNR
    snr = received_power - noise_power
    
    # Fading margin
    if include_fading:
        k_factor = RicianChannel.compute_k_factor(elevation)
        channel = RicianChannel(k_factor)
        # 99th percentile fading depth
        fading_samples = channel.get_fading_loss(10000)
        fading_margin = -np.percentile(fading_samples, 1)
    else:
        fading_margin = 0
    
    # Effective SNR
    effective_snr = snr - fading_margin
    
    return {
        'eirp_dBW': eirp,
        'path_loss_dB': path_loss,
        'received_power_dBW': received_power,
        'noise_power_dBW': noise_power,
        'snr_dB': snr,
        'fading_margin_dB': fading_margin,
        'effective_snr_dB': effective_snr
    }


def compute_data_rate(
    snr: float,
    bandwidth: float,
    efficiency: float = 0.8
) -> float:
    """
    Estimate achievable data rate using Shannon capacity.
    
    Args:
        snr: Signal-to-noise ratio (linear, not dB)
        bandwidth: Bandwidth in Hz
        efficiency: Spectral efficiency factor
    
    Returns:
        Data rate in bits per second
    """
    capacity = bandwidth * np.log2(1 + snr) * efficiency
    return capacity


class SatelliteLink:
    """
    Complete satellite link model combining all effects.
    """
    
    def __init__(
        self,
        link_params: LinkParameters,
        channel_type: str = 'rician'
    ):
        """
        Initialize satellite link.
        
        Args:
            link_params: Link parameters
            channel_type: 'rician' or 'isl'
        """
        self.params = link_params
        self.channel_type = channel_type
    
    def compute_link_quality(
        self,
        distance: float,
        elevation: float = 90.0
    ) -> dict:
        """
        Compute link quality metrics.
        
        Args:
            distance: Distance in km
            elevation: Elevation angle in degrees
        
        Returns:
            Dictionary with link quality metrics
        """
        budget = compute_link_budget(
            self.params, distance, elevation,
            include_fading=(self.channel_type == 'rician')
        )
        
        # Convert SNR to linear
        snr_linear = 10 ** (budget['effective_snr_dB'] / 10)
        
        # Data rate
        data_rate = compute_data_rate(
            snr_linear, self.params.bandwidth
        )
        
        # Latency (propagation only)
        latency = distance / SPEED_OF_LIGHT * 1000  # ms
        
        # Bit error rate estimate (BPSK approximation)
        ber = 0.5 * np.exp(-snr_linear / 2) if snr_linear > 0 else 0.5
        
        return {
            **budget,
            'data_rate_bps': data_rate,
            'latency_ms': latency,
            'ber': ber,
            'link_margin_dB': budget['effective_snr_dB'] - 10  # Assume 10 dB required
        }


if __name__ == "__main__":
    print("=== Channel Model Demo ===\n")
    
    # Define link parameters (Ka-band)
    params = LinkParameters(
        frequency=26.5e9,  # 26.5 GHz
        transmit_power=10,  # 10 dBW
        transmit_gain=35,  # 35 dBi
        receive_gain=40,  # 40 dBi
        system_noise_temp=300,  # 300 K
        bandwidth=500e6  # 500 MHz
    )
    
    # Test at different elevations
    print("Link budget analysis for LEO satellite at 550 km:\n")
    print(f"{'Elevation':<12} {'Path Loss':<12} {'SNR':<10} {'Data Rate':<15} {'Latency':<10}")
    print("-" * 60)
    
    link = SatelliteLink(params, 'rician')
    
    for elevation in [10, 30, 60, 90]:
        # Approximate slant range
        h = 550  # km
        Re = 6371  # km
        theta = np.radians(elevation)
        distance = np.sqrt((Re + h)**2 - (Re * np.cos(theta))**2) - Re * np.sin(theta)
        
        quality = link.compute_link_quality(distance, elevation)
        
        print(f"{elevation}°{'':<9} {quality['path_loss_dB']:<12.1f} "
              f"{quality['effective_snr_dB']:<10.1f} "
              f"{quality['data_rate_bps']/1e9:<15.2f} Gbps "
              f"{quality['latency_ms']:<10.2f} ms")
    
    # ISL example
    print("\n\nISL between satellites 1000 km apart:")
    isl = ISLChannel()
    isl_loss = isl.compute_total_loss(1000)
    print(f"Total ISL loss: {isl_loss:.1f} dB")
