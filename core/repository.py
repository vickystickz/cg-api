from typing import Any, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy import Select, func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from .pagination import PageSchema, PaginatedResponse

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession, schema: Optional[str] = None):
        self.db = db
        self.model = self._get_model_for_schema(
            model, schema) if schema else model

    def _get_model_for_schema(self, model: Type[ModelType], schema: str) -> Type[ModelType]:
        new_attrs = dict(model.__dict__)
        new_attrs["__table_args__"] = {
            "schema": schema, "extend_existing": True}
        return type(f"{model.__name__}_{schema}", (model,), new_attrs)

    def query(self) -> Select:
        return select(self.model)

    def _apply_filters(self, query: Select, **kwargs) -> Select:
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        return query

    async def get(self, id: Any) -> Optional[ModelType]:
        return await self.db.get(self.model, id)

    async def get_one(
        self,
        *where_clauses,
        query: Optional[Select] = None,
        **filters
    ) -> Optional[ModelType]:
        if query is None:
            query = self.query()

        if where_clauses:
            query = query.where(*where_clauses)

        query = self._apply_filters(query, **filters)

        result = await self.db.execute(query.limit(1))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *where_clauses,
        query: Optional[Select] = None,
        limit: Optional[int] = None,
        **filters
    ) -> List[ModelType]:
        if query is None:
            query = self.query()

        if where_clauses:
            query = query.where(*where_clauses)

        query = self._apply_filters(query, **filters)

        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, obj_in: Union[dict, ModelType], commit: bool = True) -> ModelType:
        """Create a new record. Accepts either a dict or a model instance."""
        if isinstance(obj_in, dict):
            db_obj = self.model(**obj_in)
        else:
            db_obj = obj_in
        self.db.add(db_obj)
        if commit:
            await self.db.commit()
            await self.db.refresh(db_obj)
        return db_obj

    async def create_many(self, items: List[Union[dict, ModelType]], commit: bool = True) -> List[ModelType]:
        """Create multiple records. Accepts list of dicts or model instances."""
        objs = []
        for item in items:
            if isinstance(item, dict):
                objs.append(self.model(**item))
            else:
                objs.append(item)
        self.db.add_all(objs)
        if commit:
            await self.db.commit()
        return objs

    async def update(self, id_or_obj: Union[Any, ModelType], attributes: Optional[dict] = None, commit: bool = True) -> Optional[ModelType]:
        """
        Update a record. Accepts either:
        - id + attributes dict: update(1, {"name": "John"})
        - model instance: update(user_obj)  # saves changes made to the object
        """
        if isinstance(id_or_obj, self.model):
            # It's a model instance - just save it
            db_obj = id_or_obj
            if attributes:
                for key, value in attributes.items():
                    if hasattr(db_obj, key):
                        setattr(db_obj, key, value)
            self.db.add(db_obj)
            if commit:
                await self.db.commit()
                await self.db.refresh(db_obj)
            return db_obj
        else:
            # It's an ID - use bulk update
            if not attributes:
                return None
            stmt = (
                update(self.model)
                .where(self.model.id == id_or_obj)
                .values(**attributes)
                .returning(self.model)
            )
            result = await self.db.execute(stmt)
            if commit:
                await self.db.commit()
            return result.scalar_one_or_none()

    async def delete(self, id: Any, commit: bool = True) -> bool:
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        if commit:
            await self.db.commit()
        return result.rowcount > 0

    async def count(self, *where_clauses, query: Optional[Select] = None, **filters) -> int:
        if query is None:
            query = self.query()

        if where_clauses:
            query = query.where(*where_clauses)

        query = self._apply_filters(query, **filters)

        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db.execute(count_query)
        return result.scalar_one()

    async def paginate(
        self,
        page_params: PageSchema,
        *where_clauses,
        query: Optional[Select] = None,
        filter_obj=None,
        **filters
    ) -> PaginatedResponse[ModelType]:
        if query is None:
            query = self.query()

        if where_clauses:
            query = query.where(*where_clauses)

        if filter_obj:
            query = filter_obj.apply(query, self.model)
        else:
            query = self._apply_filters(query, **filters)

        # Calculate Total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        # Apply Pagination
        limit = page_params.page_size
        offset = (page_params.page_number - 1) * limit

        paginated_query = query.limit(limit).offset(offset)
        result = await self.db.execute(paginated_query)
        items = result.scalars().all()

        return PaginatedResponse(
            items=items,
            total=total,
            page=page_params.page_number,
            page_size=limit,
            pages=(total + limit - 1) // limit
        )
