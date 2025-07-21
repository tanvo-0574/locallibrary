import uuid
from datetime import date, timedelta

from django.test import TestCase
from django.contrib.auth.models import User

from catalog.models import Author, Genre, Book, BookInstance


class AuthorModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
        cls.author = Author.objects.create(first_name='Big', last_name='Bob')

    def test_first_name_label(self):
        field_label = self.author._meta.get_field('first_name').verbose_name
        self.assertEqual(field_label, 'first name')

    def test_date_of_death_label(self):
        field_label = self.author._meta.get_field('date_of_death').verbose_name
        self.assertEqual(field_label, 'Died')

    def test_first_name_max_length(self):
        max_length = self.author._meta.get_field('first_name').max_length
        self.assertEqual(max_length, 100)

    def test_object_name_is_last_name_comma_first_name(self):
        expected = f'{self.author.last_name}, {self.author.first_name}'
        self.assertEqual(str(self.author), expected)

    def test_get_absolute_url(self):
        self.assertEqual(
            self.author.get_absolute_url(),
            f'/catalog/author/{self.author.id}/'
        )


class GenreModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.genre = Genre.objects.create(name='Science Fiction')

    def test_name_label(self):
        field_label = self.genre._meta.get_field('name').verbose_name
        self.assertEqual(field_label, 'name')

    def test_name_max_length(self):
        max_length = self.genre._meta.get_field('name').max_length
        self.assertEqual(max_length, 200)

    def test_string_representation(self):
        self.assertEqual(str(self.genre), 'Science Fiction')


class BookModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = Author.objects.create(first_name='Big', last_name='Bob')
        cls.genre = Genre.objects.create(name='Fantasy')
        cls.book = Book.objects.create(
            title='Test Book',
            summary='A summary here.',
            isbn='1234567890123',
            author=cls.author
        )
        cls.book.genre.add(cls.genre)

    def test_title_label(self):
        field_label = self.book._meta.get_field('title').verbose_name
        self.assertEqual(field_label, 'title')

    def test_isbn_label(self):
        field_label = self.book._meta.get_field('isbn').verbose_name
        self.assertEqual(field_label, 'ISBN')

    def test_object_name_is_title(self):
        self.assertEqual(str(self.book), 'Test Book')

    def test_get_absolute_url(self):
        self.assertEqual(
            self.book.get_absolute_url(),
            f'/catalog/book/{self.book.id}'
        )

    def test_display_genre(self):
        self.assertEqual(self.book.display_genre(), 'Fantasy')


class BookInstanceModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = Author.objects.create(
            first_name='John',
            last_name='Smith'
        )
        cls.book = Book.objects.create(
            title='Book Title',
            summary='Summary',
            isbn='9876543210123',
            author=cls.author
        )
        cls.book_instance = BookInstance.objects.create(
            book=cls.book,
            imprint='Imprint Name',
            due_back=date.today() + timedelta(days=5),
            status='m'
        )

    def test_id_is_uuid(self):
        self.assertIsInstance(self.book_instance.id, uuid.UUID)

    def test_imprint_label(self):
        field_label = self.book_instance._meta.get_field('imprint').verbose_name
        self.assertEqual(field_label, 'imprint')

    def test_is_overdue_false(self):
        self.assertFalse(self.book_instance.is_overdue)

    def test_string_representation(self):
        self.assertIn(
            str(self.book_instance.book.title),
            str(self.book_instance)
        )
