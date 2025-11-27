"""Система фильтров для LogInterceptor.

Предоставляет базовый интерфейс и различные реализации фильтров
для фильтрации строк логов по различным критериям.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Callable


class BaseFilter(ABC):
    """Абстрактный базовый класс для всех фильтров.

    Все фильтры должны наследоваться от этого класса и реализовывать
    метод filter() для определения логики фильтрации.
    """

    @abstractmethod
    def filter(self, line: str) -> bool:
        """Проверяет, должна ли строка быть включена.

        Args:
            line: Строка для проверки.

        Returns:
            True если строка должна быть включена, False иначе.

        """


class RegexFilter(BaseFilter):
    """Фильтр на основе регулярных выражений.

    Фильтрует строки по регулярному выражению с поддержкой
    режимов whitelist (включать совпадения) и blacklist (исключать совпадения).

    Attributes:
        pattern: Скомпилированное регулярное выражение.
        mode: Режим фильтрации ('whitelist' или 'blacklist').

    """

    def __init__(
        self,
        pattern: str,
        *,
        mode: Literal["whitelist", "blacklist"] = "whitelist",
        case_sensitive: bool = True,
    ) -> None:
        """Инициализирует RegexFilter.

        Args:
            pattern: Регулярное выражение для фильтрации.
            mode: Режим фильтрации:
                - 'whitelist': включать только совпадающие строки
                - 'blacklist': исключать совпадающие строки
            case_sensitive: Учитывать регистр при сопоставлении.

        Raises:
            re.error: Если pattern некорректен.

        """
        flags = 0 if case_sensitive else re.IGNORECASE
        self.pattern = re.compile(pattern, flags)
        self.mode = mode

    def filter(self, line: str) -> bool:
        """Проверяет строку по регулярному выражению.

        Args:
            line: Строка для проверки.

        Returns:
            True если строка проходит фильтр, False иначе.

        """
        matches = bool(self.pattern.search(line))

        if self.mode == "whitelist":
            return matches
        return not matches  # blacklist


class PredicateFilter(BaseFilter):
    """Фильтр на основе пользовательской функции-предиката.

    Использует произвольную функцию для определения, должна ли строка
    быть включена в результат.

    Attributes:
        predicate: Функция-предикат для проверки строк.

    """

    def __init__(self, predicate: Callable[[str], bool]) -> None:
        """Инициализирует PredicateFilter.

        Args:
            predicate: Функция, принимающая строку и возвращающая bool.
                      True означает, что строка должна быть включена.

        """
        self.predicate = predicate

    def filter(self, line: str) -> bool:
        """Проверяет строку с помощью предиката.

        Args:
            line: Строка для проверки.

        Returns:
            Результат применения предиката к строке.

        """
        return self.predicate(line)


class CompositeFilter(BaseFilter):
    """Композитный фильтр для комбинирования нескольких фильтров.

    Поддерживает логические операции AND и OR для объединения
    результатов нескольких фильтров.

    Attributes:
        filters: Список фильтров для комбинирования.
        mode: Режим комбинирования ('AND' или 'OR').

    """

    def __init__(
        self,
        filters: list[BaseFilter],
        *,
        mode: Literal["AND", "OR"] = "AND",
    ) -> None:
        """Инициализирует CompositeFilter.

        Args:
            filters: Список фильтров для комбинирования.
            mode: Режим комбинирования:
                - 'AND': строка должна пройти все фильтры
                - 'OR': строка должна пройти хотя бы один фильтр

        """
        self.filters = filters
        self.mode = mode

    def filter(self, line: str) -> bool:
        """Применяет все фильтры к строке согласно режиму.

        Args:
            line: Строка для проверки.

        Returns:
            Результат комбинированной проверки всех фильтров.

        """
        if not self.filters:
            # Пустой AND возвращает True (нет условий для проверки)
            # Пустой OR возвращает False (ни одно условие не выполнено)
            return self.mode == "AND"

        if self.mode == "AND":
            return all(f.filter(line) for f in self.filters)
        return any(f.filter(line) for f in self.filters)  # OR
