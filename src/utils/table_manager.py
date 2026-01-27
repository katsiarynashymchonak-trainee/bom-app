# utils/table_manager.py
import pandas as pd
from typing import List, Tuple


class DataTableManager:
    """Менеджер для работы с таблицей данных"""

    def __init__(self, data=None):
        self.data = data
        self.page_size = 20
        self.current_page = 1
        self.sort_column = None
        self.sort_ascending = True
        self.search_query = ""
        self.search_column = "all"  # "all" для поиска по всем колонкам, иначе имя колонки

    def set_data(self, data):
        """Установка данных"""
        self.data = data
        self.current_page = 1
        self.sort_column = None
        self.sort_ascending = True
        self.search_query = ""
        self.search_column = "all"

    def get_paged_data(self) -> Tuple[pd.DataFrame, int, int]:
        """Получение данных для текущей страницы"""
        if self.data is None or len(self.data) == 0:
            return pd.DataFrame(), 1, 0

        # Применяем поиск
        filtered_data = self.data
        if self.search_query:
            query = self.search_query.lower()

            if self.search_column == "all":
                # Поиск по всем колонкам
                search_df = self.data.copy()

                # Преобразуем все колонки к строковому типу для поиска
                for col in search_df.columns:
                    search_df[col] = search_df[col].astype(str).str.lower()

                # Фильтруем по всем колонкам
                mask = search_df.apply(lambda row: row.str.contains(query, na=False).any(), axis=1)
                filtered_data = self.data[mask]
            elif self.search_column in self.data.columns:
                # Поиск по конкретной колонке
                search_series = self.data[self.search_column].astype(str).str.lower()
                mask = search_series.str.contains(query, na=False)
                filtered_data = self.data[mask]

        # Применяем сортировку
        if self.sort_column and self.sort_column in filtered_data.columns:
            filtered_data = filtered_data.sort_values(
                by=self.sort_column,
                ascending=self.sort_ascending,
                na_position='last'
            )

        # Вычисляем индексы для пагинации
        total_items = len(filtered_data)
        total_pages = max(1, (total_items + self.page_size - 1) // self.page_size)
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total_items)

        # Получаем данные для текущей страницы
        page_data = filtered_data.iloc[start_idx:end_idx]

        return page_data, total_pages, total_items

    def next_page(self):
        """Переход на следующую страницу"""
        if self.data is None:
            return
        total_items = len(self.data)
        total_pages = max(1, (total_items + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page += 1

    def prev_page(self):
        """Переход на предыдущую страницу"""
        if self.current_page > 1:
            self.current_page -= 1

    def set_sort(self, column):
        """Установка сортировки по колонке"""
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True

    def set_search(self, query: str, column: str = "all"):
        """Установка поискового запроса и колонки"""
        self.search_query = query
        self.search_column = column
        self.current_page = 1

    def set_search_column(self, column: str):
        """Установка только колонки для поиска"""
        self.search_column = column

    def get_searchable_columns(self) -> List[str]:
        """Получение списка колонок, по которым можно искать"""
        if self.data is None:
            return ["all"]

        # Возвращаем все колонки, которые можно использовать для поиска
        # Исключаем сложные типы данных
        columns = ["all"]  # "all" для поиска по всем колонкам

        for col in self.data.columns:
            # Проверяем, можно ли конвертировать колонку в строку для поиска
            try:
                # Пробуем преобразовать первые 10 значений
                sample = self.data[col].head(10).astype(str)
                columns.append(col)
            except:
                continue

        return columns

    def get_column_names(self) -> List[str]:
        """Получение списка всех колонок"""
        if self.data is None:
            return []
        return list(self.data.columns)

    def reset_search(self):
        """Сброс поисковых параметров"""
        self.search_query = ""
        self.search_column = "all"
        self.current_page = 1