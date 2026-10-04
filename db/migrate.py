"""Pasang skema ke Neon dan D1.

Jalankan dari folder utama repo (dengan lingkungan pipeline aktif):
    python db/migrate.py                # Neon dan D1
    python db/migrate.py --target neon  # hanya Neon
    python db/migrate.py --target d1    # hanya D1
"""

import sys

from analyzer.migrate import main

if __name__ == "__main__":
    sys.exit(main())
