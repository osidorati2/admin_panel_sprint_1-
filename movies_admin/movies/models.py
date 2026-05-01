import uuid

from django.db import models


class Genre(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField('name', max_length=255)
    description = models.TextField('description', blank=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'content"."genre'

        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class FilmWork(models.Model):

    class Types(models.TextChoices):
        MOVIE = 'movie', 'Movie'
        TV_SHOW = 'tv_show', 'TV Show'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField('title', max_length=255)
    description = models.TextField('description', blank=True)

    creation_date = models.DateField('creation date', blank=True, null=True)

    rating = models.FloatField('rating', blank=True, null=True)

    type = models.TextField(
        'type',
        choices=Types.choices,
        default=Types.MOVIE
    )

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'content"."film_work'

        verbose_name = 'Кинопроизведение'
        verbose_name_plural = 'Кинопроизведения'

    def __str__(self):
        return self.title