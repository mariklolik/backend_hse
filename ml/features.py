import numpy as np


def extract_features(
    is_verified_seller: bool,
    images_qty: int,
    description: str,
    category: int,
) -> np.ndarray:
    return np.array([[
        1.0 if is_verified_seller else 0.0,
        images_qty / 10,
        len(description) / 1000,
        category / 100,
    ]])
