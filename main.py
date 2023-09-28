import argparse
import fitz
import numpy as np
import pandas as pd
from src.extract import extract_tables
from os import path
import logging

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The filename of the PDF file.")
    parser.add_argument("-s", "--start", help="The page number to start extracting tables from.")
    parser.add_argument("-e", "--end", help="The page number to end extracting tables from.")
    args = parser.parse_args()
    doc = fitz.open(args.filename)
    start = int(args.start) if args.start else 0
    end = int(args.end) if args.end else len(doc)
    for page in doc:
        if page.number < start:
            continue
        if page.number > end:
            break
        rects = [d['rect'] for d in page.get_drawings()]
        tables = extract_tables(rects)
        for table_i, table in enumerate(tables):
            for (w_x0, w_y0, w_x1, w_y1, word, _, _, _) in page.get_text_words():
                if table.table_rect.contains(((w_x0+w_x1)/2, (w_y0+w_y1)/2)):
                    try:
                        table.add_word(word, w_x0, w_y0, w_x1, w_y1)
                    except Exception as e:
                        logging.error('Error adding word "%s" to table cell: %s', word, e)

            table_arr = np.ndarray(
                (len(table.horizontals), len(table.verticals)),
                dtype=object)

            for ci, cj, cell, cwords in table.table_cells:
                table_arr[ci, cj] = ' '.join(cwords)

            pdf_name = path.basename(args.filename)
            pd.DataFrame(table_arr)\
                .replace(r'^\s*$', np.nan, regex=True)\
                .dropna(axis=0, how='all')\
                .dropna(axis=1, how='all')\
                .to_csv(f"{pdf_name}-page-{page.number}-table-{table_i}.csv", index=False)
