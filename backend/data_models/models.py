from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, ForeignKeyConstraint, Table
from sqlalchemy.orm import relationship
from .connection import Base

class WorkSpaceAccountLink(Base):
    __tablename__ = "workspace_account_link"
    user_id = Column(BigInteger, ForeignKey("account.user_id"), primary_key=True)
    workspace_id = Column(BigInteger, ForeignKey("workspace.workspace_id"), primary_key = True)
    
    locale_alias = Column(String(255), nullable=True)

    member = relationship("Account", back_populates="workspaces")
    workspace = relationship("WorkSpace", back_populates="members")

class Account(Base):
    __tablename__ = "account"

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=False, unique=True, index = True)
    email = Column(String(255), nullable=False, unique=True, index = True)
    password_hash = Column(String(255), nullable=False)
    password_salt = Column(String(255), nullable=False)

    refresh_token = relationship("Login", back_populates="user")
    workspaces = relationship("WorkSpaceAccountLink", back_populates = "member")

class Login(Base):
    __tablename__ = "login"

    user_id = Column(BigInteger, ForeignKey("account.user_id", ondelete = "CASCADE"), primary_key=True)
    refresh_token_hash = Column(String(255), nullable=False)
    refresh_token_salt = Column(String(255), nullable=False)
    expiry_date = Column(DateTime, nullable=False)

    user = relationship("Account", back_populates="refresh_token")

class WorkSpace(Base):
    __tablename__ = "workspace"

    workspace_id = Column(BigInteger, primary_key = True)
    workspace_default_name = Column(String(255), nullable=False, unique=True, index = True)
    workspace_owner_id = Column(BigInteger, ForeignKey("account.user_id"))

    members = relationship("WorkSpaceAccountLink", back_populates = "workspace")
    todolists = relationship("TodoList", back_populates = "workspace")
    todos = relationship("Todo", back_populates = "workspace")
class TodoList(Base):
    __tablename__ = "todo_list"

    todolist_id = Column(BigInteger, primary_key = True)
    workspace_id = Column(BigInteger, ForeignKey("workspace.workspace_id", ondelete = "CASCADE"))
    
    workspace = relationship("WorkSpace", back_populates="todolists")
    todos = relationship("Todo", back_populates = "todolist")

class Todo(Base):

    __tablename__ = "todo"

    todo_id = Column(BigInteger, primary_key = True)
    todolist_id = Column(BigInteger, ForeignKey("todo_list.todolist_id", ondelete = "CASCADE"))
    workspace_id = Column(BigInteger, ForeignKey("workspace.workspace_id", ondelete = "CASCADE"))
    name = Column(String(255), nullable=False, index = True)
    description = Column(String(1000), nullable=False, index = True)
    due_date = Column(DateTime, nullable=False, index = True)
    status = Column(String(255), nullable=False, index = True)
    priority = Column(String(255), nullable=False, index = True)
    last_modified = Column(DateTime, nullable=False)

    todolist = relationship("TodoList", back_populates="todos")
    workspace = relationship("WorkSpace", back_populates="todos")



