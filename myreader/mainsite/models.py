# encoding: utf-8

from django.db import models
from django.db.models.deletion import CASCADE

# Create your models here.
class Book(models.Model):
    # 书名
    title = models.CharField(max_length=200)
    # 作者
    author = models.CharField(max_length=200)
    # 简介
    desc = models.TextField(max_length=4096)
    # 封面
    poster = models.ImageField(null=True, blank=True)
    # 分类
    tag = models.CharField(max_length=20, blank=True)
    # 状态
    status = models.CharField(max_length=20, blank=True)
    # 最新章节
    latest = models.IntegerField(null=True, blank=True) # 取章节表的section字段
    # 更新时间
    updated = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('title', 'author',)
        ordering = ('title', )

    def __str__(self):
        return "书名: {} 作者: {}".format(self.title, self.author)

class Chapter(models.Model):
    # 外键关联
    book = models.ForeignKey(Book, on_delete=CASCADE)
    # 章节序号
    section = models.IntegerField()
    # 标题
    title = models.CharField(max_length=200)
    # 正文
    content = models.TextField(max_length=64000)

    class Meta:
        unique_together = ('book', 'section',)
        ordering = ('section', )

    def __str__(self):
        return "章节名: {}".format(self.title)

class BookOriginalSource(models.Model):
    # 一本书的源头，允许创建多条，默认有效
    book_name = models.CharField(max_length=200)
    # 作者
    author = models.CharField(max_length=200)
    # 书目来源
    url = models.URLField(max_length=1024)
    # 完整目录
    all = models.URLField(max_length=1024)
    # 当前book使用的，处于激活态
    activate = models.BooleanField()

    def __str__(self):
        return "书名: {} 作者: {} 来源: {}".format(self.book_name, self.author, self.url)

