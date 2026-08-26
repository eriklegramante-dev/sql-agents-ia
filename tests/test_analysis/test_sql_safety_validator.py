import pytest

from app.analysis.sql_safety_validator import SQLSafetyValidator


class TestSQLSafetyValidator:
    def setup_method(self) -> None:
        self.validator = SQLSafetyValidator()

    def test_validate_should_accept_valid_select_statement(self) -> None:
        sql = "SELECT * FROM dataset"

        result = self.validator.validate(sql)

        assert result == sql

    def test_validate_should_accept_lowercase_select_statement(self) -> None:
        sql = "select name, age from dataset"

        result = self.validator.validate(sql)

        assert result == sql

    def test_validate_should_remove_trailing_semicolon(self) -> None:
        sql = "SELECT * FROM dataset;"

        result = self.validator.validate(sql)

        assert result == "SELECT * FROM dataset"

    def test_validate_should_reject_empty_sql(self) -> None:
        with pytest.raises(
            ValueError,
            match="SQL query must not be empty.",
        ):
            self.validator.validate("   ")

    @pytest.mark.parametrize(
        "sql",
        [
            "INSERT INTO dataset VALUES (1)",
            "UPDATE dataset SET value = 1",
            "DELETE FROM dataset",
            "DROP TABLE dataset",
            "ALTER TABLE dataset ADD COLUMN test INT",
            "CREATE TABLE test (id INT)",
            "TRUNCATE TABLE dataset",
        ],
    )
    def test_validate_should_reject_non_select_statements(
        self,
        sql: str,
    ) -> None:
        with pytest.raises(
            ValueError,
            match="Only SELECT statements are allowed.",
        ):
            self.validator.validate(sql)

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM dataset; DELETE FROM dataset",
            "SELECT * FROM dataset; DROP TABLE dataset",
            "SELECT * FROM dataset; UPDATE dataset SET value = 1",
        ],
    )
    def test_validate_should_reject_multiple_statements(
        self,
        sql: str,
    ) -> None:
        with pytest.raises(
            ValueError,
            match="Multiple SQL statements are not allowed.",
        ):
            self.validator.validate(sql)
