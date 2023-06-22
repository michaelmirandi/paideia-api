import uuid
from pydantic import BaseModel
import typing as t
import datetime


class CreateOrUpdateComment(BaseModel):
    user_details_id: uuid.UUID
    comment: t.Optional[str]
    parent: t.Optional[uuid.UUID]


class CreateOrUpdateAddendum(BaseModel):
    name: str
    content: t.Optional[str]


class CreateProposal(BaseModel):
    dao_id: uuid.UUID
    user_details_id: uuid.UUID
    name: str
    image_url: t.Optional[str]
    category: t.Optional[str]
    content: t.Optional[str]
    voting_system: t.Optional[str]
    references: t.List[uuid.UUID] = [] # list of proposal ids
    actions: t.Optional[t.List[dict]] = []
    tags: t.Optional[t.List[str]]
    attachments: t.List[str]
    status: t.Optional[str] = "discussion"
    is_proposal: bool = False


class UpdateProposalBasic(CreateProposal):
    pass


class CreateOrUpdateProposal(CreateProposal):
    comments: t.List[CreateOrUpdateComment]
    likes: t.List[uuid.UUID]  # list of user_details_ids who like
    dislikes: t.List[uuid.UUID]  # list of user_details_ids who dislike
    followers: t.List[uuid.UUID]  # list of user_details_ids who follow
    addendums: t.List[CreateOrUpdateAddendum]


class Comment(CreateOrUpdateComment):
    id: uuid.UUID
    proposal_id: uuid.UUID
    date: datetime.datetime
    alias: str
    profile_img_url: t.Optional[str]
    likes: t.List[uuid.UUID]  # list of user_details_ids who like
    dislikes: t.List[uuid.UUID]  # list of user_details_ids who dislike

    class Config:
        orm_mode = True


class Addendum(CreateOrUpdateAddendum):
    id: uuid.UUID
    date: datetime.datetime

    class Config:
        orm_mode = True


class Proposal(CreateOrUpdateProposal):
    id: uuid.UUID
    date: datetime.datetime
    comments: t.List[Comment]
    addendums: t.List[Addendum]
    references_meta: t.List
    profile_img_url: t.Optional[str]
    user_followers: t.List[uuid.UUID]
    created: int
    alias: str

    class Config:
        orm_mode = True


class LikeProposalRequest(BaseModel):
    user_details_id: uuid.UUID
    type: str


class FollowProposalRequest(BaseModel):
    user_details_id: uuid.UUID
    type: str


class AddReferenceRequest(BaseModel):
    referred_proposal_id: uuid.UUID


class ProposalReference(BaseModel):
    id: uuid.UUID
    name: str
    likes: t.List[uuid.UUID]
    dislikes: t.List[uuid.UUID]
    img: str
    is_proposal: bool
