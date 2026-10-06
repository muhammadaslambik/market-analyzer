import pandas as pd
from typing import List, Tuple

def generate_walk_forward_splits(
    df: pd.DataFrame, 
    horizon: int, 
    min_train_size: int, 
    test_size: int
) -> List[Tuple[pd.Index, pd.Index]]:
    """
    Menghasilkan indeks latih dan uji menggunakan metode Expanding Window dengan Purging.
    Menghapus 'horizon' baris terakhir di data latihan yang labelnya tumpang tindih dengan awal blok uji.
    """
    splits = []
    n_samples = len(df)
    
    start_idx = min_train_size
    while start_idx + test_size <= n_samples:
        # Menentukan rentang latihan awal (expanding window)
        train_end = start_idx
        test_end = start_idx + test_size
        
        # Jendela Latihan dan Uji Mentah
        raw_train_idx = df.index[:train_end]
        test_idx = df.index[train_end:test_end]
        
        # Penerapan Purging: Hapus 'horizon' baris terakhir dari data latihan
        # karena labelnya bergantung pada data harga di dalam blok uji
        purged_train_idx = raw_train_idx[:-horizon] if len(raw_train_idx) > horizon else raw_train_idx
        
        splits.append((purged_train_idx, test_idx))
        start_idx += test_size
        
    return splits
