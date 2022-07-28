from pydantic import BaseModel
import typing as t
import datetime


class CreateOrUpdateComment(BaseModel):
    user_id: int
    comment: t.Optional[str]
    parent: t.Optional[int]


class CreateOrUpdateAddendum(BaseModel):
    name: str
    content: t.Optional[str]


class CreateProposal(BaseModel):
    dao_id: int
    user_id: int
    name: str
    image_url: t.Optional[str]
    category: t.Optional[str]
    content: t.Optional[str]
    voting_system: t.Optional[str]
    references: t.List[int]  # list of proposal ids
    actions: t.List[dict]
    tags: t.List[str]
    attachments: t.List[str]
    is_proposal: bool


class CreateOrUpdateProposal(CreateProposal):
    comments: t.List[CreateOrUpdateComment]
    likes: t.List[int]  # list of user_ids who like
    dislikes: t.List[int]  # list of user_ids who dislike
    followers: t.List[int]  # list of user_ids who follow
    addendums: t.List[CreateOrUpdateAddendum]


class Comment(CreateOrUpdateComment):
    id: int
    date: datetime.datetime

    class Config:
        orm_mode = True


class Addendum(CreateOrUpdateAddendum):
    id: int
    date: datetime.datetime

    class Config:
        orm_mode = True


class Proposal(CreateOrUpdateProposal):
    id: int
    date: datetime.datetime
    comments: t.List[Comment]
    addendums: t.List[Addendum]

    class Config:
        orm_mode = True
