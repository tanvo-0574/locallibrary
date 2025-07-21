from django.test import TestCase
from django.urls import reverse

from catalog.models import Book, Author, BookInstance
from catalog.constants import LoanStatus


class AuthorListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):

        # Create 13 authors for pagination tests
        number_of_authors = 13

        for author_id in range(number_of_authors):
            Author.objects.create(
                first_name=f'Christian {author_id}',
                last_name=f'Surname {author_id}',
                )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/catalog/authors/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('authors'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('authors'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/author_list.html')

    def test_pagination_is_ten(self):
        response = self.client.get(reverse('authors'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] is True)
        self.assertTrue(len(response.context['author_list']) == 10)

    def test_lists_all_authors(self):
        # Get second page and confirm it has (exactly) remaining 3 items
        response = self.client.get(reverse('authors')+'?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] is True)
        self.assertTrue(len(response.context['author_list']) == 3)


class IndexViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        author = Author.objects.create(first_name='Christian', last_name='Doe')
        book = Book.objects.create(
            title='Test Book',
            summary='Summary',
            isbn='1234567890123',
            author=author
        )
        BookInstance.objects.create(
            book=book,
            status=LoanStatus.AVAILABLE.value
        )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/catalog/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('index'))
        self.assertTemplateUsed(response, 'index.html')

    def test_session_visit_count_increments(self):
        session = self.client.session
        session['num_visits'] = 5
        session.save()

        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['num_visits'], 5)


class BookListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        author = Author.objects.create(first_name='Christian', last_name='Doe')
        for i in range(15):
            Book.objects.create(
                title=f'Book {i}',
                summary='Summary',
                isbn=f'12345678901{i}',
                author=author
            )

    def test_view_url_exists(self):
        response = self.client.get('/catalog/books/')
        self.assertEqual(response.status_code, 200)

    def test_view_accessible_by_name(self):
        response = self.client.get(reverse('books'))
        self.assertEqual(response.status_code, 200)

    def test_correct_template_used(self):
        response = self.client.get(reverse('books'))
        self.assertTemplateUsed(response, 'catalog/book_list.html')

    def test_pagination_is_correct(self):
        response = self.client.get(reverse('books'))
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['book_list']), 10)

    def test_second_page_has_remaining_books(self):
        response = self.client.get(reverse('books') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['book_list']), 5)


class BookDetailViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        author = Author.objects.create(
            first_name='Christian',
            last_name='Doe'
        )
        book = Book.objects.create(
            title='Detail Book',
            summary='Summary',
            isbn='1234567890123',
            author=author
        )
        BookInstance.objects.create(
            book=book,
            status=LoanStatus.AVAILABLE.value
        )

    def test_view_url_exists(self):
        book = Book.objects.first()
        response = self.client.get(reverse('book-detail', args=[book.id]))
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        book = Book.objects.first()
        response = self.client.get(reverse(
            'book-detail',
            args=[book.id]))
        self.assertTemplateUsed(response, 'catalog/book_detail.html')

    def test_context_has_book_instances(self):
        book = Book.objects.first()
        response = self.client.get(reverse('book-detail', args=[book.id]))
        self.assertIn('book_instances', response.context)


class AuthorDetailViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = Author.objects.create(
            first_name='Christian',
            last_name='Doe'
        )

    def test_view_url_exists(self):
        response = self.client.get(reverse(
            'author-detail',
            args=[self.author.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        response = self.client.get(reverse(
            'author-detail',
            args=[self.author.id])
        )
        self.assertTemplateUsed(response, 'catalog/author_detail.html')

    def test_context_includes_books_by_author(self):
        response = self.client.get(reverse(
            'author-detail',
            args=[self.author.id])
        )
        self.assertIn('book_set', response.context)
