"""
Orbital Mechanics Module for OrbitalChain
=========================================

Implements Keplerian orbital mechanics for LEO satellite positioning
and visibility calculations.

References:
    - Vallado, D. (2007). Fundamentals of Astrodynamics and Applications.
    - OrbitalChain Paper, Section 4.2
"""

import numpy as np
from typing import Tuple, List, Optional
from dataclasses import dataclass
import math


# Constants
MU_EARTH = 398600.4418  # km³/s² - Earth's gravitational parameter
R_EARTH = 6371.0  # km - Earth's mean radius
J2 = 1.08263e-3  # Earth's J2 perturbation coefficient


@dataclass
class KeplerianOrbit:
    """
    Keplerian orbital elements.
    
    Attributes:
        a: Semi-major axis (km)
        e: Eccentricity (dimensionless)
        i: Inclination (radians)
        omega: Argument of perigee (radians)
        Omega: Right ascension of ascending node (radians)
        nu: True anomaly (radians)
        epoch: Epoch time (Julian date)
    """
    a: float  # Semi-major axis (km)
    e: float  # Eccentricity
    i: float  # Inclination (rad)
    omega: float  # Argument of perigee (rad)
    Omega: float  # RAAN (rad)
    nu: float  # True anomaly (rad)
    epoch: float  # Julian date
    
    @classmethod
    def from_tle(cls, tle_line1: str, tle_line2: str) -> 'KeplerianOrbit':
        """
        Parse Two-Line Element set to Keplerian elements.
        
        Args:
            tle_line1: First line of TLE
            tle_line2: Second line of TLE
        
        Returns:
            KeplerianOrbit object
        """
        # Parse TLE line 2
        i = float(tle_line2[8:16]) * np.pi / 180  # Inclination
        Omega = float(tle_line2[17:25]) * np.pi / 180  # RAAN
        e = float('0.' + tle_line2[26:33])  # Eccentricity
        omega = float(tle_line2[34:42]) * np.pi / 180  # Arg of perigee
        M = float(tle_line2[43:51]) * np.pi / 180  # Mean anomaly
        n = float(tle_line2[52:63])  # Mean motion (rev/day)
        
        # Compute semi-major axis from mean motion
        n_rad = n * 2 * np.pi / 86400  # rad/s
        a = (MU_EARTH / n_rad**2) ** (1/3)
        
        # Convert mean anomaly to true anomaly
        E = cls._solve_kepler(M, e)
        nu = 2 * np.arctan2(
            np.sqrt(1 + e) * np.sin(E / 2),
            np.sqrt(1 - e) * np.cos(E / 2)
        )
        
        # Parse epoch from line 1
        year = int(tle_line1[18:20])
        year = 2000 + year if year < 57 else 1900 + year
        day = float(tle_line1[20:32])
        epoch = cls._ymd_to_jd(year, 1, 1) + day - 1
        
        return cls(a=a, e=e, i=i, omega=omega, Omega=Omega, nu=nu, epoch=epoch)
    
    @staticmethod
    def _solve_kepler(M: float, e: float, tol: float = 1e-10) -> float:
        """Solve Kepler's equation M = E - e*sin(E) for E."""
        E = M  # Initial guess
        for _ in range(100):
            E_new = M + e * np.sin(E)
            if abs(E_new - E) < tol:
                return E_new
            E = E_new
        return E
    
    @staticmethod
    def _ymd_to_jd(year: int, month: int, day: float) -> float:
        """Convert year, month, day to Julian date."""
        if month <= 2:
            year -= 1
            month += 12
        A = int(year / 100)
        B = 2 - A + int(A / 4)
        return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5
    
    def to_state_vector(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert Keplerian elements to state vector (position, velocity).
        
        Returns:
            Tuple of (position, velocity) in ECI frame (km, km/s)
        """
        # Perifocal coordinates
        p = self.a * (1 - self.e**2)
        r_mag = p / (1 + self.e * np.cos(self.nu))
        
        r_pqw = np.array([
            r_mag * np.cos(self.nu),
            r_mag * np.sin(self.nu),
            0
        ])
        
        v_pqw = np.sqrt(MU_EARTH / p) * np.array([
            -np.sin(self.nu),
            self.e + np.cos(self.nu),
            0
        ])
        
        # Rotation matrices
        R3_Omega = self._rotation_matrix(self.Omega, 3)
        R1_i = self._rotation_matrix(self.i, 1)
        R3_omega = self._rotation_matrix(self.omega, 3)
        
        # Transform to ECI
        Q = R3_Omega @ R1_i @ R3_omega
        
        r_eci = Q @ r_pqw
        v_eci = Q @ v_pqw
        
        return r_eci, v_eci
    
    @staticmethod
    def _rotation_matrix(angle: float, axis: int) -> np.ndarray:
        """Create rotation matrix around given axis."""
        c, s = np.cos(angle), np.sin(angle)
        if axis == 1:
            return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
        elif axis == 2:
            return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
        else:  # axis == 3
            return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    
    @property
    def period(self) -> float:
        """Orbital period in seconds."""
        return 2 * np.pi * np.sqrt(self.a**3 / MU_EARTH)
    
    @property
    def altitude(self) -> float:
        """Altitude at current position (km)."""
        r, _ = self.to_state_vector()
        return np.linalg.norm(r) - R_EARTH


class OrbitalPropagator:
    """
    Propagates satellite orbits using simplified perturbation models.
    
    For production use, consider SGP4 propagator from sgp4 package.
    """
    
    def __init__(self, include_j2: bool = True):
        """
        Initialize propagator.
        
        Args:
            include_j2: Whether to include J2 perturbation
        """
        self.include_j2 = include_j2
    
    def propagate(
        self,
        orbit: KeplerianOrbit,
        dt: float
    ) -> KeplerianOrbit:
        """
        Propagate orbit forward by dt seconds.
        
        Args:
            orbit: Initial orbital elements
            dt: Time step in seconds
        
        Returns:
            New KeplerianOrbit at time t + dt
        """
        # Mean motion
        n = np.sqrt(MU_EARTH / orbit.a**3)
        
        # J2 perturbations (secular terms)
        if self.include_j2:
            p = orbit.a * (1 - orbit.e**2)
            dOmega_dt = -1.5 * n * J2 * (R_EARTH / p)**2 * np.cos(orbit.i)
            domega_dt = 0.75 * n * J2 * (R_EARTH / p)**2 * (5 * np.cos(orbit.i)**2 - 1)
        else:
            dOmega_dt = 0
            domega_dt = 0
        
        # Update mean anomaly
        M = self._true_to_mean_anomaly(orbit.nu, orbit.e)
        M_new = M + n * dt
        
        # Convert back to true anomaly
        E_new = KeplerianOrbit._solve_kepler(M_new % (2 * np.pi), orbit.e)
        nu_new = 2 * np.arctan2(
            np.sqrt(1 + orbit.e) * np.sin(E_new / 2),
            np.sqrt(1 - orbit.e) * np.cos(E_new / 2)
        )
        
        # Update RAAN and argument of perigee
        Omega_new = orbit.Omega + dOmega_dt * dt
        omega_new = orbit.omega + domega_dt * dt
        
        # New epoch
        epoch_new = orbit.epoch + dt / 86400.0
        
        return KeplerianOrbit(
            a=orbit.a,
            e=orbit.e,
            i=orbit.i,
            omega=omega_new,
            Omega=Omega_new,
            nu=nu_new,
            epoch=epoch_new
        )
    
    @staticmethod
    def _true_to_mean_anomaly(nu: float, e: float) -> float:
        """Convert true anomaly to mean anomaly."""
        E = 2 * np.arctan2(
            np.sqrt(1 - e) * np.sin(nu / 2),
            np.sqrt(1 + e) * np.cos(nu / 2)
        )
        M = E - e * np.sin(E)
        return M


class VisibilityCalculator:
    """
    Calculate satellite visibility from ground stations or between satellites.
    """
    
    def __init__(self, min_elevation: float = 10.0):
        """
        Initialize calculator.
        
        Args:
            min_elevation: Minimum elevation angle (degrees) for visibility
        """
        self.min_elevation = min_elevation
    
    def compute_elevation(
        self,
        sat_position: np.ndarray,
        ground_position: np.ndarray
    ) -> float:
        """
        Compute elevation angle from ground to satellite.
        
        Args:
            sat_position: Satellite ECI position (km)
            ground_position: Ground station ECI position (km)
        
        Returns:
            Elevation angle in degrees
        """
        # Vector from ground to satellite
        r = sat_position - ground_position
        
        # Local vertical (radially outward from Earth center)
        local_up = ground_position / np.linalg.norm(ground_position)
        
        # Compute angle
        cos_zenith = np.dot(r, local_up) / (np.linalg.norm(r))
        zenith = np.arccos(np.clip(cos_zenith, -1, 1))
        elevation = 90 - np.degrees(zenith)
        
        return elevation
    
    def is_visible(
        self,
        sat_position: np.ndarray,
        ground_position: np.ndarray
    ) -> bool:
        """Check if satellite is visible from ground station."""
        elevation = self.compute_elevation(sat_position, ground_position)
        return elevation >= self.min_elevation
    
    def compute_visibility_window(
        self,
        orbit: KeplerianOrbit,
        ground_position: np.ndarray,
        start_time: float,
        duration: float,
        time_step: float = 10.0
    ) -> List[Tuple[float, float]]:
        """
        Compute visibility windows over a time period.
        
        Args:
            orbit: Satellite orbit
            ground_position: Ground station ECI position
            start_time: Start Julian date
            duration: Duration in seconds
            time_step: Time step in seconds
        
        Returns:
            List of (start, end) tuples for visibility windows
        """
        propagator = OrbitalPropagator()
        windows = []
        
        current_orbit = orbit
        in_visibility = False
        window_start = None
        
        for t in np.arange(0, duration, time_step):
            sat_pos, _ = current_orbit.to_state_vector()
            visible = self.is_visible(sat_pos, ground_position)
            
            if visible and not in_visibility:
                # Start of visibility window
                window_start = start_time + t / 86400.0
                in_visibility = True
            elif not visible and in_visibility:
                # End of visibility window
                window_end = start_time + t / 86400.0
                windows.append((window_start, window_end))
                in_visibility = False
            
            current_orbit = propagator.propagate(current_orbit, time_step)
        
        # Close final window if still visible
        if in_visibility:
            windows.append((window_start, start_time + duration / 86400.0))
        
        return windows


# Utility functions
def compute_orbital_period(altitude: float) -> float:
    """
    Compute orbital period for circular orbit at given altitude.
    
    Args:
        altitude: Altitude above Earth surface (km)
    
    Returns:
        Orbital period in seconds
    """
    a = R_EARTH + altitude
    return 2 * np.pi * np.sqrt(a**3 / MU_EARTH)


def compute_visibility_window(
    altitude: float,
    latitude: float,
    min_elevation: float = 10.0
) -> float:
    """
    Estimate visibility window duration for a satellite pass.
    
    Args:
        altitude: Satellite altitude (km)
        latitude: Ground station latitude (degrees)
        min_elevation: Minimum elevation angle (degrees)
    
    Returns:
        Estimated visibility duration in seconds
    """
    # Simplified estimation based on geometry
    h = altitude
    Re = R_EARTH
    theta_min = np.radians(min_elevation)
    
    # Central angle from satellite to horizon
    rho = np.arcsin(Re / (Re + h) * np.cos(theta_min))
    
    # Arc length visible
    lambda_arc = np.pi - 2 * (theta_min + rho)
    
    # Convert to time using orbital velocity
    v_orbital = np.sqrt(MU_EARTH / (Re + h))
    arc_length = lambda_arc * (Re + h)
    duration = arc_length / v_orbital
    
    return duration


def eci_to_geodetic(position: np.ndarray, time_jd: float) -> Tuple[float, float, float]:
    """
    Convert ECI position to geodetic coordinates.
    
    Args:
        position: ECI position vector (km)
        time_jd: Julian date
    
    Returns:
        Tuple of (latitude, longitude, altitude) in (degrees, degrees, km)
    """
    # Greenwich Sidereal Time
    T = (time_jd - 2451545.0) / 36525.0
    theta_g = 280.46061837 + 360.98564736629 * (time_jd - 2451545.0)
    theta_g = theta_g % 360.0
    
    # Convert to ECEF
    theta_rad = np.radians(theta_g)
    R = np.array([
        [np.cos(theta_rad), np.sin(theta_rad), 0],
        [-np.sin(theta_rad), np.cos(theta_rad), 0],
        [0, 0, 1]
    ])
    pos_ecef = R @ position
    
    # Convert to geodetic
    x, y, z = pos_ecef
    r = np.sqrt(x**2 + y**2)
    lon = np.degrees(np.arctan2(y, x))
    lat = np.degrees(np.arctan2(z, r))
    alt = np.linalg.norm(pos_ecef) - R_EARTH
    
    return lat, lon, alt


if __name__ == "__main__":
    # Demo
    print("=== Orbital Mechanics Demo ===\n")
    
    # Create a LEO orbit at 550 km
    orbit = KeplerianOrbit(
        a=R_EARTH + 550,
        e=0.0001,
        i=np.radians(53),
        omega=0,
        Omega=0,
        nu=0,
        epoch=2460000.5
    )
    
    print(f"Orbital period: {orbit.period / 60:.2f} minutes")
    print(f"Current altitude: {orbit.altitude:.2f} km")
    
    # Get state vector
    r, v = orbit.to_state_vector()
    print(f"Position: {r} km")
    print(f"Velocity: {v} km/s")
    
    # Propagate
    propagator = OrbitalPropagator()
    orbit_1hr = propagator.propagate(orbit, 3600)
    print(f"\nAfter 1 hour:")
    print(f"True anomaly: {np.degrees(orbit_1hr.nu):.2f}°")
