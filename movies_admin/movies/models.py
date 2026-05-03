import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedMixin(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Genre(UUIDMixin, TimeStampedMixin):
    name = models.CharField(_("name"), max_length=255)
    description = models.TextField(_("description"), blank=True)

    class Meta:
        db_table = 'content"."genre'

        verbose_name = _("Жанр")
        verbose_name_plural = _("Жанры")

    def __str__(self):
        return self.name


class Person(UUIDMixin, TimeStampedMixin):
    full_name = models.CharField(_("full name"), max_length=255)

    class Meta:
        db_table = 'content"."person'

        verbose_name = _("Персона")
        verbose_name_plural = _("Персоны")

    def __str__(self):
        return self.full_name


class FilmWork(UUIDMixin, TimeStampedMixin):
    class Types(models.TextChoices):
        MOVIE = "movie", _("Movie")
        TV_SHOW = "tv_show", _("TV Show")

    title = models.CharField(_("title"), max_length=255)

    description = models.TextField(_("description"), blank=True)

    creation_date = models.DateField(_("creation date"), blank=True, null=True)
    certificate = models.CharField("certificate", max_length=512, blank=True)
    file_path = models.FileField("file", blank=True, null=True, upload_to="movies/")
    rating = models.FloatField(
        "rating", blank=True, validators=[MinValueValidator(0), MaxValueValidator(10)]
    )

    type = models.TextField(_("type"), choices=Types.choices, default=Types.MOVIE)

    genres = models.ManyToManyField(
        Genre, through="GenreFilmWork", verbose_name=_("genres")
    )

    persons = models.ManyToManyField(
        Person, through="PersonFilmWork", verbose_name=_("persons")
    )

    class Meta:
        db_table = 'content"."film_work'

        verbose_name = _("Кинопроизведение")
        verbose_name_plural = _("Кинопроизведения")

        indexes = [
            models.Index(fields=["creation_date"]),
        ]

    def __str__(self):
        return self.title


class GenreFilmWork(UUIDMixin):
    film_work = models.ForeignKey(FilmWork, on_delete=models.CASCADE)

    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'content"."genre_film_work'

        verbose_name = _("Жанр произведения")
        verbose_name_plural = _("Жанры произведений")

        constraints = [
            models.UniqueConstraint(
                fields=["film_work", "genre"], name="film_work_genre_idx"
            ),
        ]


class PersonFilmWork(UUIDMixin):
    class Roles(models.TextChoices):
        ACTOR = "actor", _("Actor")
        DIRECTOR = "director", _("Director")
        WRITER = "writer", _("Writer")

    film_work = models.ForeignKey(FilmWork, on_delete=models.CASCADE)

    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    role = models.TextField(_("role"), choices=Roles.choices)

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'content"."person_film_work'

        verbose_name = _("Участник произведения")
        verbose_name_plural = _("Участники произведений")

        constraints = [
            models.UniqueConstraint(
                fields=["film_work", "person", "role"], name="film_work_person_role_idx"
            ),
        ]
