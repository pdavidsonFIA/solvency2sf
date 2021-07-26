# solvency2sf
Solvency 2 Standard Formula

Pandas/numpy implementation of the standard formula for non-life.

The calculation logic generally mimics the calculations within the standard formula guidance provided by Lloyd's.
https://www.lloyds.com/resources-and-services/capital-and-reserving/capital-guidance/standard-formula-scr

The template populated with sample data is saved under /tests

Provides:
- scr:
  - non-life
    - premium and reserve
    - lapse
    - catastrophy
      - natcat euro
      - man-made
  - default
  - bscr
  - op
  - scr
- mcr

Structure:
- Each scr sub-module is within its own package.
- Any required parameters are typically stored in CSV files in the same package 
- Functions often return tuples. The first item will be a numerical result, the subsequent items data frames containing additional breakdown to debug and support QRT completion.

Known limitations:
- only gross scr calculated in natcat: approach for reinsurance may be very company specific.
- not all nat-cat modules included (yet)
- default quite simple
