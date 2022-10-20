from tortoise import fields
from tortoise.models import Model


class Account(Model):
    """ORM model for table of user accounts"""

    user_id = fields.BigIntField(pk=True)
    username = fields.CharField(max_length=255, null=False, unique=True)
    email = fields.CharField(max_length=255, null=False, unique=True)
    #: `password_hash` is the user's password stored as a hash
    password_hash = fields.CharField(max_length=255, null=False)
    salt = fields.CharField(max_length=255, null=False)

    class Meta:
        table = "account"


class Login(Model):
    """ORM model for table of user logins"""

    user: fields.ForeignKeyRelation[Account] = fields.ForeignKeyField(
        model_name="models.Account",
        related_name="login_user_id",
        on_delete=fields.CASCADE,
        to_field="user_id",
        pk=True,
    )
    #: `refresh_token_hash` is the user's refresh token stored as a hash
    refresh_token_hash = fields.CharField(max_length=255, null=False)

    class Meta:
        table = "login"


class WorkSpace(Model):
    """ORM model for table of user's workspace"""

    workspace_id = fields.BigIntField(pk=True)
    workspace_default_name = fields.CharField(max_length=255, null=False)
    workspace_owner: fields.ForeignKeyRelation[Account] = fields.ForeignKeyField(
        model_name="models.Account",
        related_name="worker_owner_id",
        on_delete=fields.CASCADE,
        to_field="user_id",
    )

    class Meta:
        table = "workspace"


class WorkSpaceAccountLink(Model):
    """Linkage table between workspaces and users"""

    workspace: fields.ForeignKeyRelation[WorkSpace] = fields.ForeignKeyField(
        model_name="models.WorkSpace",
        related_name="joined_user_ids",
        on_delete=fields.CASCADE,
        to_field="workspace_id",
    )
    user: fields.ForeignKeyRelation[Account] = fields.ForeignKeyField(
        model_name="models.Account",
        related_name="joined_workspace_ids",
        on_delete=fields.CASCADE,
        to_field="user_id",
    )
    locale_view_name = fields.CharField(max_length=255, null=False)

    class Meta:
        table = "workspace_account_link"
        unique_together = ("workspace", "user")
        indexes = ("workspace", "user")


class TodoLists(Model):
    """ORM model for todo list table in user's workspace"""

    todolist_id = fields.BigIntField(pk=True)
    workspace: fields.ForeignKeyRelation[WorkSpace] = fields.ForeignKeyField(
        model_name="models.WorkSpace",
        related_name="todolist_ids",
        on_delete=fields.CASCADE,
    )

    class Meta:
        table = "todo_lists"


class Todos(Model):
    """ORM model for todos table in user's todo list"""

    todo_id = fields.IntField(pk=True)
    todolist: fields.ForeignKeyRelation[TodoLists] = fields.ForeignKeyField(
        model_name="models.TodoLists",
        related_name="todo_ids",
        on_delete=fields.CASCADE,
    )
    workspace: fields.ForeignKeyRelation[WorkSpace] = fields.ForeignKeyField(
        model_name="models.WorkSpace",
        related_name="todo_ids",
        on_delete=fields.CASCADE,
    )
    name = fields.CharField(max_length=255, null=False)
    description = fields.CharField(max_length=1000, null=False)
    due_date = fields.DatetimeField(null=False, auto_now=True)
    status = fields.CharField(max_length=255, null=False)
    priority = fields.CharField(max_length=255, null=False)
    last_modified = fields.DatetimeField(null=False, auto_now=True)

    class Meta:
        table = "todos"
