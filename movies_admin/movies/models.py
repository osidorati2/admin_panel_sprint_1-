import uuid

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class TimeStampedMixin(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Genre(UUIDMixin, TimeStampedMixin):
    name = models.CharField('name', max_length=255)
    description = models.TextField('description', blank=True)

    class Meta:
        db_table = 'content"."genre'

        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class Person(UUIDMixin, TimeStampedMixin):
    full_name = models.CharField('full name', max_length=255)

    class Meta:
        db_table = 'content"."person'

        verbose_name = 'Персона'
        verbose_name_plural = 'Персоны'

    def __str__(self):
        return self.full_name


class FilmWork(UUIDMixin, TimeStampedMixin):

    class Types(models.TextChoices):
        MOVIE = 'movie', 'Movie'
        TV_SHOW = 'tv_show', 'TV Show'

    title = models.CharField('title', max_length=255)
    description = models.TextField('description', blank=True)

    creation_date = models.DateField(
        'creation date',
        blank=True,
        null=True
    )
    certificate = models.CharField('certificate', max_length=512, blank=True)
    file_path = models.FileField('file', blank=True, null=True, upload_to='movies/')
    rating = models.FloatField('rating', blank=True,
                               validators=[MinValueValidator(0),
                                           MaxValueValidator(10)])

    type = models.TextField(
        'type',
        choices=Types.choices,
        default=Types.MOVIE
    )

    genres = models.ManyToManyField(
        Genre,
        through='GenreFilmWork'
    )

    persons = models.ManyToManyField(
        Person,
        through='PersonFilmWork'
    )

    class Meta:
        db_table = 'content"."film_work'

        verbose_name = 'Кинопроизведение'
        verbose_name_plural = 'Кинопроизведения'

    def __str__(self):
        return self.title


class GenreFilmWork(UUIDMixin):
    film_work = models.ForeignKey(
        'FilmWork',
        on_delete=models.CASCADE
    )

    genre = models.ForeignKey(
        'Genre',
        on_delete=models.CASCADE
    )

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'content"."genre_film_work'

        verbose_name = 'Жанр произведения'
        verbose_name_plural = 'Жанры произведений'


class PersonFilmWork(UUIDMixin):
    film_work = models.ForeignKey(
        'FilmWork',
        on_delete=models.CASCADE
    )

    person = models.ForeignKey(
        'Person',
        on_delete=models.CASCADE
    )

    role = models.TextField('role')

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'content"."person_film_work'

        verbose_name = 'Участник произведения'
        verbose_name_plural = 'Участники произведений'