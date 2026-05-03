from django.contrib import admin

from .models import FilmWork, Genre, GenreFilmWork, Person, PersonFilmWork


class GenreFilmWorkInline(admin.TabularInline):
    model = GenreFilmWork


class PersonFilmWorkInline(admin.TabularInline):
    model = PersonFilmWork


@admin.register(FilmWork)
class FilmWorkAdmin(admin.ModelAdmin):
    inlines = (
        GenreFilmWorkInline,
        PersonFilmWorkInline,
    )

    list_display = (
        "title",
        "type",
        "creation_date",
        "rating",
    )

    list_filter = ("type",)

    search_fields = ("title", "description", "id")


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("full_name",)

    search_fields = ("full_name",)


@admin.register(GenreFilmWork)
class GenreFilmWorkAdmin(admin.ModelAdmin):
    pass


@admin.register(PersonFilmWork)
class PersonFilmWorkAdmin(admin.ModelAdmin):
    pass
