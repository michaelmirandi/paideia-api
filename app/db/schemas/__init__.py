from typing import Optional

from pydantic.fields import ModelField

class RestrictedAlphabetStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value, field: ModelField):
        alphabet = field.field_info.extra['alphabet']
        if any(c not in alphabet for c in value):
            raise ValueError(f'{value!r} is not restricted to {alphabet!r}')
        return cls(value)

    @classmethod
    def __modify_schema__(cls, field_schema, field: Optional[ModelField]):
        if field:
            alphabet = field.field_info.extra['alphabet']
            field_schema['examples'] = [c * 3 for c in alphabet]
