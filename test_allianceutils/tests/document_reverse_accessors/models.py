from django import db
from django.db import models
from django.db.models import CharField


class Person(models.Model):
    name = db.models.CharField(max_length=255)
    # non_existent -> test_allianceutils.tests.document_reverse_accessors.models.NonExistent.model_field
    # task_set -> test_allianceutils.tests.document_reverse_accessors.models.Task.person

    non_field_attribute = True

    class Meta:
        verbose_name_plural = 'people'

    def __str__(self):
        return self.name


class Task(models.Model):
    name = models.CharField(max_length=255)
    person = models.ForeignKey('Person', on_delete=models.CASCADE)
    reviewer = models.ForeignKey('Person', on_delete=models.CASCADE, related_name='reviewers')
    auditor = models.ForeignKey('Person', on_delete=models.CASCADE, related_name='auditors')


class TaskItem(models.Model):
    name = models.CharField(max_length=255)
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='items')
