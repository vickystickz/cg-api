from typing import Any, Optional, List, Set, Tuple
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import Select, or_, and_
from sqlalchemy.sql.sqltypes import String, Enum as SAEnum, Boolean, Integer, Date, DateTime


class FilterBase(BaseModel):
    """
    Base class for declarative filtering.

    Features:
    - Auto-detects operators (String -> ilike, Int/Enum -> eq)
    - Auto-handles Enums (extracts .value)
    - Auto-joins relationships (address__city)
    - Supports suffixes (age__gte, role__neq)
    - Supports lists (status=['active'] -> IN)
    - Global search (q)
    """
    q: Optional[str] = Field(
        None, description="Global search across search_fields")

    def _get_column_and_join(self, query: Select, model: Any, field_path: str) -> Tuple[Select, Any]:
        """
        Helper to traverse relationships (e.g., 'address__city'), 
        apply necessary joins to the query, and return the final column.
        """
        target_model = model

        if "__" not in field_path:
            if hasattr(target_model, field_path):
                return query, getattr(target_model, field_path)
            return query, None

        parts = field_path.split("__")

        for part in parts[:-1]:
            if not hasattr(target_model, part):
                return query, None

            rel_attr = getattr(target_model, part)
            target_model = rel_attr.property.mapper.class_
            query = query.outerjoin(rel_attr)

        column_name = parts[-1]
        if hasattr(target_model, column_name):
            return query, getattr(target_model, column_name)

        return query, None

    def apply(self, query: Select, model: Any) -> Select:
        filter_config = getattr(self, "Constants", {})
        search_fields = getattr(filter_config, "search_fields", [])

        params = self.model_dump(exclude_unset=True, exclude_none=True)

        known_ops = {"eq", "neq", "gt", "gte", "lt", "lte",
                     "in", "like", "ilike", "isnull", "isnotnull"}

        for key, value in params.items():
            if key in ("q", "from_date", "to_date"):
                continue

            field_name = key
            operator = None

            if "__" in key:
                parts = key.split("__")
                if parts[-1] in known_ops:
                    operator = parts[-1]
                    field_name = "__".join(parts[:-1])
                else:
                    field_name = key

            query, column = self._get_column_and_join(query, model, field_name)
            if column is None:
                continue
            is_enum_input = False

            if isinstance(value, Enum):
                value = value.value
                is_enum_input = True

            if isinstance(value, list) and value and isinstance(value[0], Enum):
                value = [v.value for v in value]
                is_enum_input = True

            if not operator:
                operator = getattr(filter_config, field_name, None)

            if not operator:
                if is_enum_input:
                    operator = "eq"
                elif isinstance(column.type, (SAEnum, Boolean, Integer, Date, DateTime)):
                    operator = "eq"
                elif isinstance(column.type, String):
                    operator = "ilike"
                else:
                    operator = "eq"

            if isinstance(value, list) and operator != "neq":
                query = query.where(column.in_(value))

            elif operator == "eq":
                query = query.where(column == value)
            elif operator == "neq":
                query = query.where(column != value)
            elif operator == "ilike":
                query = query.where(column.ilike(f"%{value}%"))
            elif operator == "like":
                query = query.where(column.like(f"%{value}%"))
            elif operator == "gt":
                query = query.where(column > value)
            elif operator == "gte":
                query = query.where(column >= value)
            elif operator == "lt":
                query = query.where(column < value)
            elif operator == "lte":
                query = query.where(column <= value)
            elif operator == "isnull":
                if value is True:
                    query = query.where(column.is_(None))
                else:
                    query = query.where(column.is_not(None))

        if self.from_date or self.to_date:
            from datetime import datetime, timezone
            query, created_at_col = self._get_column_and_join(
                query, model, "created_at")

            if created_at_col:
                if self.from_date:
                    try:
                        from_date_str = self.from_date.strip()
                        if len(from_date_str) == 10:
                            from_date_obj = datetime.strptime(
                                from_date_str, "%Y-%m-%d")
                        elif "T" in from_date_str or " " in from_date_str:
                            from_date_obj = datetime.fromisoformat(
                                from_date_str.replace("Z", "+00:00"))
                        else:
                            from_date_obj = datetime.strptime(
                                from_date_str, "%Y-%m-%d")

                        if from_date_obj.tzinfo is None:
                            from_date_obj = from_date_obj.replace(
                                tzinfo=timezone.utc)

                        query = query.where(created_at_col >= from_date_obj)
                    except (ValueError, AttributeError) as e:
                        pass

                if self.to_date:
                    try:
                        to_date_str = self.to_date.strip()
                        if len(to_date_str) == 10:
                            to_date_obj = datetime.strptime(
                                to_date_str, "%Y-%m-%d")
                            to_date_obj = to_date_obj.replace(
                                hour=23, minute=59, second=59, microsecond=999999)
                        elif "T" in to_date_str or " " in to_date_str:
                            to_date_obj = datetime.fromisoformat(
                                to_date_str.replace("Z", "+00:00"))
                        else:
                            to_date_obj = datetime.strptime(
                                to_date_str, "%Y-%m-%d")
                            to_date_obj = to_date_obj.replace(
                                hour=23, minute=59, second=59, microsecond=999999)

                        if to_date_obj.tzinfo is None:
                            to_date_obj = to_date_obj.replace(
                                tzinfo=timezone.utc)

                        query = query.where(created_at_col <= to_date_obj)
                    except (ValueError, AttributeError) as e:
                        pass

        if self.q and search_fields:
            search_conditions = []
            for field_name in search_fields:
                query, column = self._get_column_and_join(
                    query, model, field_name)
                if column is not None:
                    search_conditions.append(
                        column.cast(String).ilike(f"%{self.q}%"))

            if search_conditions:
                query = query.where(or_(*search_conditions))

        return query
