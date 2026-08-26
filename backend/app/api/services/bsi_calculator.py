import math

class BSICalculator:
    @staticmethod
    def calculate_steepness_index(Ss: float, Hs: float, h0: float = 2.5) -> float:
        """
        Calculates the Wave Steepness Index (I_steepness).
        Ss: Significant wave steepness (dimensionless ratio of height to wavelength).
        Hs: Significant wave height (m).
        h0: Regional reference wave height (constant = 2.5 m for Indian seas).
        """
        if Hs is None or Ss is None:
            return 0.0
        return (Ss / 0.05) * (Hs / h0)

    @staticmethod
    def calculate_crossing_sea_index(Hs: float, ss: float) -> float:
        """
        Calculates the Crossing Sea Index (I_crossing).
        Hs: Significant wave height (m).
        ss: Directional spread parameter (ranges from 0 to sqrt(2)).
        """
        if Hs is None or ss is None:
            return 0.0
        # Formula: I_crossing = 1/2 * Hs * exp(-10 * (ss - 1)^2)
        return 0.5 * Hs * math.exp(-10.0 * (ss - 1.0) ** 2)

    @staticmethod
    def calculate_rapid_dev_index(Hsea_initial: float, Hsea_final: float) -> float:
        """
        Calculates the Rapid Development of Sea Index (Z_6h).
        Hsea_initial: Wind-sea wave height at initial time (m).
        Hsea_final: Wind-sea wave height 6 hours later (m).
        """
        if Hsea_initial is None or Hsea_final is None:
            return 0.0
        if Hsea_initial == 0.0:
            return 0.0
        return abs(Hsea_initial - Hsea_final) / Hsea_initial

    @classmethod
    def calculate_bsi(
        cls,
        Ss: float,
        Hs: float,
        ss: float,
        Hsea_initial: float,
        Hsea_final: float,
        h0: float = 2.5
    ) -> int:
        """
        Calculates the aggregate Boat Safety Index (BSI) from the three warning criteria.
        Returns a weighted binary sum: BSI in [0, 7].
        """
        # 1. Compute individual indices
        I_steepness = cls.calculate_steepness_index(Ss, Hs, h0)
        I_crossing = cls.calculate_crossing_sea_index(Hs, ss)
        Z_6h = cls.calculate_rapid_dev_index(Hsea_initial, Hsea_final)
        
        # 2. Check warning thresholds
        S_steepness = 1 if I_steepness >= 0.8 else 0
        S_crossing = 2 if I_crossing >= 0.65 else 0
        S_rapiddev = 4 if Z_6h >= 0.2 else 0
        
        # 3. Bitwise sum
        return S_steepness + S_crossing + S_rapiddev

    @staticmethod
    def get_bsi_details(bsi: int) -> dict:
        """
        Decodes a BSI value (0-7) into structural warning reasons and hazard descriptors.
        """
        # Bit mapping check
        has_steepness = bool(bsi & 1)
        has_crossing = bool(bsi & 2)
        has_rapiddev = bool(bsi & 4)
        
        components = []
        reasons = []
        
        if has_steepness:
            components.append("Wave Steepness")
            reasons.append("Wave steepness index exceeds the 0.8 safety threshold (breaking wave danger).")
        if has_crossing:
            components.append("Crossing Sea")
            reasons.append("Crossing sea index exceeds the 0.65 safety threshold (clashing wave roll danger).")
        if has_rapiddev:
            components.append("Rapid Sea Development")
            reasons.append("Sea state is developing rapidly (wave height changed by >=20% within 6 hours).")
            
        if bsi == 0:
            rating = "SAFE"
            description = "All wave-forcing indicators are within safe baseline parameters."
        elif bsi in [1, 2, 4]:
            rating = "ALERT"
            description = f"Elevated capsizing risk due to active wave hazard: {', '.join(components)}."
        else:
            rating = "WARNING"
            description = f"High capsizing risk due to multiple compounding wave hazards: {', '.join(components)}."
            
        return {
            "bsi_score": bsi,
            "rating": rating,
            "description": description,
            "active_hazards": components,
            "reasons": reasons
        }