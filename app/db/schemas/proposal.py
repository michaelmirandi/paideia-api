from pydantic import BaseModel
import typing as t
import datetime


class CreateOrUpdateComment(BaseModel):
    user_details_id: int
    comment: t.Optional[str]
    parent: t.Optional[int]


class CreateOrUpdateAddendum(BaseModel):
    name: str
    content: t.Optional[str]


class CreateProposal(BaseModel):
    dao_id: int
    user_details_id: int
    name: str
    image_url: t.Optional[str]
    category: t.Optional[str]
    content: t.Optional[str]
    voting_system: t.Optional[str]
    references: t.List[int] = [] # list of proposal ids
    actions: t.Optional[t.List[dict]] = []
    tags: t.Optional[t.List[str]]
    attachments: t.List[str]
    status: t.Optional[str] = "discussion"
    is_proposal: bool = False


class UpdateProposalBasic(CreateProposal):
    pass


class CreateOrUpdateProposal(CreateProposal):
    comments: t.List[CreateOrUpdateComment]
    likes: t.List[int]  # list of user_details_ids who like
    dislikes: t.List[int]  # list of user_details_ids who dislike
    followers: t.List[int]  # list of user_details_ids who follow
    addendums: t.List[CreateOrUpdateAddendum]


class Comment(CreateOrUpdateComment):
    id: int
    proposal_id: int
    date: datetime.datetime
    alias: str
    profile_img_url: t.Optional[str]
    likes: t.List[int]  # list of user_details_ids who like
    dislikes: t.List[int]  # list of user_details_ids who dislike

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
    references_meta: t.List
    profile_img_url: t.Optional[str]
    user_followers: t.List[int]
    created: int
    alias: str

    class Config:
        orm_mode = True


class LikeProposalRequest(BaseModel):
    user_details_id: int
    type: str


class FollowProposalRequest(BaseModel):
    user_details_id: int
    type: str


class AddReferenceRequest(BaseModel):
    referred_proposal_id: int


class ProposalReference(BaseModel):
    id: int
    name: str
    likes: t.List[int]
    dislikes: t.List[int]
    img: str
    is_proposal: bool
