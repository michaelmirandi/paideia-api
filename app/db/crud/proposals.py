import typing as t

from sqlalchemy.orm import Session

from db.models.proposals import Proposal, ProposalReference, ProposalLike, ProposalFollower, Comment, Addendum
from db.schemas.proposal import Proposal as ProposalSchema, CreateProposal as CreateProposalSchema, UpdateProposalBasic as UpdateProposalBasicSchema, CreateOrUpdateAddendum, CreateOrUpdateComment

#####################################
### CRUD OPERATIONS FOR PROPOSALS ###
#####################################


def get_basic_proposal_by_id(db: Session, id: int):
    return db.query(Proposal).filter(Proposal.id == id).first()


def get_likes_by_proposal_id(db: Session, proposal_id: int):
    db_likes = db.query(ProposalLike).filter(
        ProposalLike.proposal_id == proposal_id).all()
    likes = list(map(lambda x: x.user_id, filter(lambda x: x.liked, db_likes)))
    dislikes = list(map(lambda x: x.user_id, filter(
        lambda x: x.liked == False, db_likes)))
    return {
        "proposal_id": proposal_id,
        "likes": likes,
        "dislikes": dislikes
    }


def set_likes_by_proposal_id(db: Session, proposal_id: int, user_id: int, type: str):
    if type not in ("like", "dislike", "remove"):
        return None
    db.query(ProposalLike).filter(ProposalLike.proposal_id == proposal_id).filter(
        ProposalLike.user_id == user_id).delete()
    if type == "like":
        db_like = ProposalLike(
            proposal_id=proposal_id,
            user_id=user_id,
            liked=True
        )
        db.add(db_like)
    if type == "dislike":
        db_like = ProposalLike(
            proposal_id=proposal_id,
            user_id=user_id,
            liked=False
        )
        db.add(db_like)

    db.commit()
    return get_likes_by_proposal_id(db, proposal_id)


def get_followers_by_proposal_id(db: Session, proposal_id: int):
    db_followers = db.query(ProposalFollower).filter(
        ProposalFollower.proposal_id == proposal_id).all()
    followers = list(map(lambda x: x.user_id, db_followers))
    return {
        "proposal_id": proposal_id,
        "followers": followers
    }


def set_followers_by_proposal_id(db: Session, proposal_id: int, user_id: int, type: str):
    if type not in ("follow", "unfollow"):
        return None
    db.query(ProposalFollower).filter(ProposalFollower.proposal_id == proposal_id).filter(
        ProposalFollower.user_id == user_id).delete()
    if type == "follow":
        db_follow = ProposalFollower(
            proposal_id=proposal_id,
            user_id=user_id,
        )
        db.add(db_follow)

    db.commit()
    return get_followers_by_proposal_id(db, proposal_id)


def get_references_by_proposal_id(db: Session, proposal_id: int):
    db_references = db.query(ProposalReference).filter(
        ProposalReference.referring_proposal_id == proposal_id
    ).all()
    references = list(map(lambda x: x.referred_proposal_id, db_references))
    return {
        "proposal_id": proposal_id,
        "references": references
    }


def add_reference_by_proposal_id(db: Session, user_id: int, proposal_id: int, referred_proposal_id: int):
    db_proposal = get_basic_proposal_by_id(db, proposal_id)
    if not db_proposal or db_proposal.user_id != user_id:
        return None
    db_reference = ProposalReference(
        referred_proposal_id=referred_proposal_id,
        referring_proposal_id=proposal_id
    )
    db.add(db_reference)
    db.commit()
    db.refresh(db_reference)
    return db_reference


def get_comments_by_proposal_id(db: Session, proposal_id: int):
    db_comments = db.query(Comment).filter(
        Comment.proposal_id == proposal_id).all()
    return db_comments


def add_commment_by_proposal_id(db: Session, proposal_id: int, comment: CreateOrUpdateComment):
    db_comment = Comment(
        proposal_id=proposal_id,
        user_id=comment.user_id,
        parent=comment.parent,
        comment=comment.comment
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def get_addendums_by_proposal_id(db: Session, proposal_id: int):
    db_addendums = db.query(Addendum).filter(
        Addendum.proposal_id == proposal_id).all()
    return db_addendums


def add_addendum_by_proposal_id(db: Session, user_id: int, proposal_id: int, addendum: CreateOrUpdateAddendum):
    db_proposal = get_basic_proposal_by_id(db, proposal_id)
    if not db_proposal or db_proposal.user_id != user_id:
        return None
    db_addendum = Addendum(
        proposal_id=proposal_id,
        name=addendum.name,
        content=addendum.content
    )
    db.add(db_addendum)
    db.commit()
    db.refresh(db_addendum)
    return db_addendum


def get_proposal_by_id(db: Session, id: int):
    db_proposal = db.query(Proposal).filter(Proposal.id == id).first()
    if not db_proposal:
        return None
    likes = get_likes_by_proposal_id(db, id)
    followers = get_followers_by_proposal_id(db, id)
    references = get_references_by_proposal_id(db, id)
    comments = get_comments_by_proposal_id(db, id)
    addendums = get_addendums_by_proposal_id(db, id)
    tags = db_proposal.tags["tags_list"] if "tags_list" in db_proposal.tags else []
    attachments = db_proposal.attachments["attachments_list"] if "attachments_list" in db_proposal.attachments else []
    actions = db_proposal.actions["actions_list"] if "actions_list" in db_proposal.actions else []
    proposal = ProposalSchema(
        id=db_proposal.id,
        dao_id=db_proposal.dao_id,
        user_id=db_proposal.user_id,
        name=db_proposal.name,
        image_url=db_proposal.image_url,
        category=db_proposal.category,
        content=db_proposal.content,
        voting_system=db_proposal.voting_system,
        references=references["references"],
        actions=actions,
        comments=comments,
        likes=likes["likes"],
        dislikes=likes["dislikes"],
        followers=followers["followers"],
        tags=tags,
        attachments=attachments,
        addendums=addendums,
        date=db_proposal.date,
        is_proposal=db_proposal.is_proposal
    )
    return proposal


def get_proposals_by_dao_id(db: Session, dao_id: int):
    db_proposals = db.query(Proposal).filter(Proposal.dao_id == dao_id).all()
    proposals = list(map(lambda x: get_proposal_by_id(db, x.id), db_proposals))
    return proposals


def create_new_proposal(db: Session, proposal: CreateProposalSchema):
    db_proposal = Proposal(
        dao_id=proposal.dao_id,
        user_id=proposal.user_id,
        name=proposal.name,
        image_url=proposal.image_url,
        category=proposal.category,
        content=proposal.content,
        voting_system=proposal.voting_system,
        actions={"actions_list": proposal.actions},
        tags={"tags_list": proposal.tags},
        attachments={"attachments_list": proposal.attachments},
        is_proposal=proposal.is_proposal
    )
    db.add(db_proposal)
    db.commit()
    db.refresh(db_proposal)
    return get_proposal_by_id(db, db_proposal.id)


def edit_proposal_basic_by_id(db: Session, user_id: int, id: int, proposal: UpdateProposalBasicSchema):
    db_proposal = db.query(Proposal).filter(Proposal.id == id).first()
    if not db_proposal:
        return None

    # safety check
    if db_proposal.user_id != user_id or proposal.user_id != user_id:
        return None

    update_data = proposal.dict(exclude_unset=True)

    if "actions" in update_data:
        update_data["actions"] = {"actions_list": proposal.actions}

    if "tags" in update_data:
        update_data["tags"] = {"tags_list": proposal.tags}

    if "attachments" in update_data:
        update_data["attachements"] = {
            "attachments_list": proposal.attachments}

    for key, value in update_data.items():
        setattr(db_proposal, key, value)

    db.add(db_proposal)
    db.commit()
    return get_proposal_by_id(db, id)


def delete_proposal_by_id(db: Session, id: int):
    proposal = get_proposal_by_id(db, id)
    if not proposal:
        return None
    # delete stuff
    db.query(ProposalReference).filter(ProposalReference.referred_proposal_id ==
                                       id or ProposalReference.referring_proposal_id == id).delete()
    db.query(ProposalFollower).filter(
        ProposalFollower.proposal_id == id).delete()
    db.query(ProposalLike).filter(ProposalLike.proposal_id == id).delete()
    db.query(Addendum).filter(Addendum.proposal_id == id).delete()
    db.query(Comment).filter(Comment.proposal_id == id).delete()
    db.query(Proposal).filter(Proposal.id == id).delete()
    db.commit()
    return proposal