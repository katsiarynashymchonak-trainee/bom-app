import pandas as pd
from typing import List, Tuple


class DataTableManager:
    def __init__(self, data=None):
        self.data = data
        self.page_size = 20
        self.current_page = 1
        self.sort_column = None
        self.sort_ascending = True

    def set_data(self, data):
        self.data = data
        self.current_page = 1
        self.sort_column = None
        self.sort_ascending = True

    def get_paged_data(self) -> Tuple[pd.DataFrame, int, int]:
        if self.data is None or len(self.data) == 0:
            return pd.DataFrame(), 1, 0

        filtered_data = self.data

        if self.sort_column and self.sort_column in filtered_data.columns:
            filtered_data = filtered_data.sort_values(
                by=self.sort_column,
                ascending=self.sort_ascending,
                na_position='last'
            )

        total_items = len(filtered_data)
        total_pages = max(1, (total_items + self.page_size - 1) // self.page_size)
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total_items)

        page_data = filtered_data.iloc[start_idx:end_idx]

        return page_data, total_pages, total_items

    def next_page(self):
        if self.data is None:
            return
        total_items = len(self.data)
        total_pages = max(1, (total_items + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page += 1

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1

    def set_sort(self, column):
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True

    def get_searchable_columns(self) -> List[str]:
        if self.data is None:
            return ["all"]

        columns = ["all"]

        for col in self.data.columns:
            try:
                sample = self.data[col].head(10).astype(str)
                columns.append(col)
            except:
                continue

        return columns

    def get_column_names(self) -> List[str]:
        if self.data is None:
            return []
        return list(self.data.columns)
