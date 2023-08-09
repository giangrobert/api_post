from fastapi import HTTPException, Depends,status, APIRouter
from typing import List, Optional
from ..database import engine, get_db
from sqlalchemy.orm import Session
#from sqlalchemy.sql.functions import func
from sqlalchemy import func
from .. import models,schemas, oauth2

router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)

@router.get("/", response_model=List[schemas.PostOut])
def get_posts(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user), limit: int = 10, skip: int = 0, search: Optional[str] = ""):
    # results = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
    #     models.Vote, models.Vote.post_id == models.Post.id, isouter=True).group_by(models.Post.id)

    # cursor.execute("""SELECT * FROM posts """)
    # posts = cursor.fetchall()

    # posts = db.execute(
    #     'select posts.*, COUNT(votes.post_id) as votes from posts LEFT JOIN votes ON posts.id=votes.post_id  group by posts.id')
    # results = []
    # for post in posts:
    #     results.append(dict(post))
    # print(results)
    # posts = db.query(models.Post).filter(
    #     models.Post.title.contains(search)).limit(limit).offset(skip).all()

    posts = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
        models.Vote, models.Vote.post_id == models.Post.id, isouter=True).group_by(models.Post.id).filter(models.Post.title.contains(search)).limit(limit).offset(skip).all()
    return posts

@router.get("/{id}", response_model=schemas.Post)
def get_id(id:int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()
    if not post:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} does not exist")  
    return post

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Post)
def create(post: schemas.PostCreate,db: Session = Depends(get_db), current_user:int=Depends(oauth2.get_current_user)):
    new_post=models.Post(owner_id= current_user.id,**post.dict())
    
    #Print User
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@router.put("/{id}", response_model=schemas.Post)
def update(post: schemas.PostCreate,id:int,db: Session = Depends(get_db),current_user: int = Depends(oauth2.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post_recovery = post_query.first()
    if post_recovery == None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} does not exist")
    if post_recovery.owner_id != current_user.id:
        raise HTTPException(status_code= status.HTTP_403_FORBIDDEN, detail="Not authorized to perform requested action")
    
    post_query.update(post.dict(),synchronize_session=False)
    db.commit()
    return post_query.first()

@router.delete("/{id}")
def delete(id:int,db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()
    if post == None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} does not exist")
    if post.owner_id != current_user.id:
        raise HTTPException(status_code= status.HTTP_403_FORBIDDEN, detail="Not authorized to perform requested action")
    post_query.delete(synchronize_session=False)
    db.commit()
    return {"detail":f'Delete Succefull posts number {id}'}