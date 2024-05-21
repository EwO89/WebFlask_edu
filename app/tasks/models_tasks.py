# -*- coding: utf-8 -*-

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship

from ..extensions import db
from ..utils import get_current_time

from flask_login import current_user
from flask_admin.contrib import sqla


class MyTaskModel(db.Model):
    __tablename__ = 'mytask_model'

    id = Column(Integer, primary_key=True)
    task = Column(String(2048))
    added_time = Column(DateTime, default=get_current_time)
    users_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("Users", uselist=False, backref="mytask_model")

    def __unicode__(self):
        _str = 'ID: %s, Post: %s' % (self.id, self.task)
        return str(_str)


class TaskCategory(db.Model):
    __tablename__ = 'task_category'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    tasks = relationship("MyTaskModel", backref="category")

    def __unicode__(self):
        return self.name


class UserNotification(db.Model):
    __tablename__ = 'user_notification'

    id = Column(Integer, primary_key=True)
    message = Column(String(1024))
    is_read = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("Users", backref="notifications")
    created_time = Column(DateTime, default=get_current_time)

    def __unicode__(self):
        _str = 'ID: %s, Message: %s' % (self.id, self.message)
        return str(_str)


class MyTaskManager:
    def __init__(self, db_session):
        self.db_session = db_session

    def add_task(self, task_description, user_id, category_id=None):
        new_task = MyTaskModel(task=task_description, users_id=user_id, category_id=category_id)
        self.db_session.add(new_task)
        try:
            self.db_session.commit()
            return new_task
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Error adding task: {e}")
            return None

    def update_task(self, task_id, new_description):
        task = self.db_session.query(MyTaskModel).get(task_id)
        if task:
            task.task = new_description
            try:
                self.db_session.commit()
                return task
            except SQLAlchemyError as e:
                self.db_session.rollback()
                print(f"Error updating task: {e}")
                return None
        return None

    def delete_task(self, task_id):
        task = self.db_session.query(MyTaskModel).get(task_id)
        if task:
            self.db_session.delete(task)
            try:
                self.db_session.commit()
                return True
            except SQLAlchemyError as e:
                self.db_session.rollback()
                print(f"Error deleting task: {e}")
                return False
        return False

    def get_task(self, task_id):
        return self.db_session.query(MyTaskModel).get(task_id)

    def get_all_tasks_for_user(self, user_id):
        return self.db_session.query(MyTaskModel).filter_by(users_id=user_id).all()

    def search_tasks(self, search_term):
        return self.db_session.query(MyTaskModel).filter(MyTaskModel.task.like(f"%{search_term}%")).all()


class TaskCategoryManager:
    def __init__(self, db_session):
        self.db_session = db_session

    def add_category(self, name):
        new_category = TaskCategory(name=name)
        self.db_session.add(new_category)
        try:
            self.db_session.commit()
            return new_category
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Error adding category: {e}")
            return None

    def get_all_categories(self):
        return self.db_session.query(TaskCategory).all()


class UserNotificationManager:
    def __init__(self, db_session):
        self.db_session = db_session

    def add_notification(self, message, user_id):
        new_notification = UserNotification(message=message, user_id=user_id)
        self.db_session.add(new_notification)
        try:
            self.db_session.commit()
            return new_notification
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Error adding notification: {e}")
            return None

    def mark_as_read(self, notification_id):
        notification = self.db_session.query(UserNotification).get(notification_id)
        if notification:
            notification.is_read = True
            try:
                self.db_session.commit()
                return notification
            except SQLAlchemyError as e:
                self.db_session.rollback()
                print(f"Error marking notification as read: {e}")
                return None
        return None

    def get_unread_notifications(self, user_id):
        return self.db_session.query(UserNotification).filter_by(user_id=user_id, is_read=False).all()


# Customized MyTask model admin
class MyTaskModelAdmin(sqla.ModelView):
    column_sortable_list = ('id', 'users_id', 'added_time')
    column_filters = ('id', 'users_id', 'added_time')

    def __init__(self, session):
        super(MyTaskModelAdmin, self).__init__(MyTaskModel, session)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin'


# Customized TaskCategory model admin
class TaskCategoryModelAdmin(sqla.ModelView):
    column_sortable_list = ('id', 'name')
    column_filters = ('id', 'name')

    def __init__(self, session):
        super(TaskCategoryModelAdmin, self).__init__(TaskCategory, session)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin'


# Customized UserNotification model admin
class UserNotificationModelAdmin(sqla.ModelView):
    column_sortable_list = ('id', 'user_id', 'created_time')
    column_filters = ('id', 'user_id', 'created_time')

    def __init__(self, session):
        super(UserNotificationModelAdmin, self).__init__(UserNotification, session)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin'
