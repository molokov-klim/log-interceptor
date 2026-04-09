"""Тесты для системы фильтров LogInterceptor."""

import re

import pytest

from log_interceptor.filters import BaseFilter, CompositeFilter, PredicateFilter, RegexFilter


@pytest.mark.unit
def test_base_filter_interface() -> None:
    """Все фильтры должны реализовывать метод filter()."""

    class CustomFilter(BaseFilter):
        def filter(self, _line: str) -> bool:
            return True

    f = CustomFilter()
    assert f.filter("test") is True


@pytest.mark.unit
def test_base_filter_is_abstract() -> None:
    """BaseFilter должен быть абстрактным классом."""
    with pytest.raises(TypeError):
        BaseFilter()  # type: ignore[abstract]


@pytest.mark.unit
def test_base_filter_requires_filter_method() -> None:
    """BaseFilter требует реализации метода filter()."""

    class IncompleteFilter(BaseFilter):
        pass

    with pytest.raises(TypeError):
        IncompleteFilter()  # type: ignore[abstract]


# RegexFilter tests


@pytest.mark.unit
def test_regex_filter_match() -> None:
    """RegexFilter должен фильтровать по регулярному выражению."""
    filter_obj = RegexFilter(r"ERROR.*")
    assert filter_obj.filter("ERROR: Something went wrong") is True
    assert filter_obj.filter("INFO: All good") is False


@pytest.mark.unit
def test_regex_filter_whitelist() -> None:
    """RegexFilter с режимом whitelist должен включать только совпадения."""
    filter_obj = RegexFilter(r"^ERROR", mode="whitelist")
    assert filter_obj.filter("ERROR: test") is True
    assert filter_obj.filter("INFO: test") is False


@pytest.mark.unit
def test_regex_filter_blacklist() -> None:
    """RegexFilter с режимом blacklist должен исключать совпадения."""
    filter_obj = RegexFilter(r"^DEBUG", mode="blacklist")
    assert filter_obj.filter("DEBUG: test") is False
    assert filter_obj.filter("ERROR: test") is True


@pytest.mark.unit
def test_regex_filter_case_insensitive() -> None:
    """RegexFilter должен поддерживать case-insensitive режим."""
    filter_obj = RegexFilter(r"error", case_sensitive=False)
    assert filter_obj.filter("ERROR: test") is True
    assert filter_obj.filter("error: test") is True
    assert filter_obj.filter("ErRoR: test") is True


@pytest.mark.unit
def test_regex_filter_case_sensitive() -> None:
    """RegexFilter по умолчанию case-sensitive."""
    filter_obj = RegexFilter(r"ERROR")
    assert filter_obj.filter("ERROR: test") is True
    assert filter_obj.filter("error: test") is False


@pytest.mark.unit
def test_regex_filter_invalid_pattern() -> None:
    """RegexFilter должен выбрасывать ошибку для некорректного regex."""
    with pytest.raises(re.error):
        RegexFilter(r"[invalid(")


@pytest.mark.unit
def test_regex_filter_empty_string() -> None:
    """RegexFilter должен корректно обрабатывать пустые строки."""
    filter_obj = RegexFilter(r"ERROR")
    assert filter_obj.filter("") is False


@pytest.mark.unit
def test_regex_filter_multiline() -> None:
    """RegexFilter должен работать с многострочными паттернами."""
    filter_obj = RegexFilter(r"^ERROR", mode="whitelist")
    assert filter_obj.filter("ERROR at start") is True
    assert filter_obj.filter("  ERROR not at start") is False


# PredicateFilter tests


@pytest.mark.unit
def test_predicate_filter() -> None:
    """PredicateFilter должен использовать пользовательскую функцию."""
    filter_obj = PredicateFilter(lambda line: len(line) > 10)
    assert filter_obj.filter("short") is False
    assert filter_obj.filter("this is a longer line") is True


@pytest.mark.unit
def test_predicate_filter_complex() -> None:
    """PredicateFilter должен поддерживать сложные предикаты."""

    def custom_predicate(line: str) -> bool:
        return "ERROR" in line and len(line) > 20

    filter_obj = PredicateFilter(custom_predicate)
    assert filter_obj.filter("ERROR") is False  # слишком короткая
    assert filter_obj.filter("ERROR: this is a long error message") is True
    assert filter_obj.filter("INFO: this is a long info message") is False  # нет ERROR


@pytest.mark.unit
def test_predicate_filter_always_true() -> None:
    """PredicateFilter с always true предикатом."""
    filter_obj = PredicateFilter(lambda _: True)
    assert filter_obj.filter("") is True
    assert filter_obj.filter("anything") is True


@pytest.mark.unit
def test_predicate_filter_always_false() -> None:
    """PredicateFilter с always false предикатом."""
    filter_obj = PredicateFilter(lambda _: False)
    assert filter_obj.filter("") is False
    assert filter_obj.filter("anything") is False


# CompositeFilter tests


@pytest.mark.unit
def test_composite_filter_and() -> None:
    """CompositeFilter должен поддерживать логику AND."""
    f1 = RegexFilter(r"ERROR")
    f2 = PredicateFilter(lambda x: len(x) > 20)
    composite = CompositeFilter([f1, f2], mode="AND")

    assert composite.filter("ERROR: x") is False  # f2 не пройден
    assert composite.filter("ERROR: this is a very long message") is True
    assert composite.filter("INFO: this is a very long message") is False  # f1 не пройден


@pytest.mark.unit
def test_composite_filter_or() -> None:
    """CompositeFilter должен поддерживать логику OR."""
    f1 = RegexFilter(r"ERROR")
    f2 = RegexFilter(r"CRITICAL")
    composite = CompositeFilter([f1, f2], mode="OR")

    assert composite.filter("ERROR: test") is True
    assert composite.filter("CRITICAL: test") is True
    assert composite.filter("INFO: test") is False


@pytest.mark.unit
def test_composite_filter_empty_list() -> None:
    """CompositeFilter с пустым списком фильтров."""
    composite = CompositeFilter([], mode="AND")
    # Пустой AND должен возвращать True (нет условий для проверки)
    assert composite.filter("anything") is True

    composite = CompositeFilter([], mode="OR")
    # Пустой OR должен возвращать False (ни одно условие не выполнено)
    assert composite.filter("anything") is False


@pytest.mark.unit
def test_composite_filter_single() -> None:
    """CompositeFilter с одним фильтром."""
    f1 = RegexFilter(r"ERROR")
    composite = CompositeFilter([f1], mode="AND")

    assert composite.filter("ERROR: test") is True
    assert composite.filter("INFO: test") is False


@pytest.mark.unit
def test_composite_filter_nested() -> None:
    """CompositeFilter должен поддерживать вложенность."""
    # (ERROR OR CRITICAL) AND длина > 20
    f1 = RegexFilter(r"ERROR")
    f2 = RegexFilter(r"CRITICAL")
    or_filter = CompositeFilter([f1, f2], mode="OR")

    f3 = PredicateFilter(lambda x: len(x) > 20)
    and_filter = CompositeFilter([or_filter, f3], mode="AND")

    assert and_filter.filter("ERROR") is False  # слишком короткая
    assert and_filter.filter("ERROR: this is a long message") is True
    assert and_filter.filter("CRITICAL: this is a long message") is True
    assert and_filter.filter("INFO: this is a very long message that exceeds limit") is False
