from django.shortcuts import render, get_object_or_404
from django.views import generic
from catalog.models import Book, Author, BookInstance, Genre
from catalog.constants import LoanStatus, PAGINATION_SIZE


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_books = Book.objects.count()
    num_instances = BookInstance.objects.count()

    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(
        status__exact=LoanStatus.AVAILABLE.value
    ).count()

    # The 'all()' is implied by default.
    num_authors = Author.objects.count()

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)


class BookListView(generic.ListView):

    model = Book
    paginate_by = PAGINATION_SIZE
    context_object_name = 'book_list'
    template_name = 'catalog/book_list.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(BookListView, self).get_context_data(**kwargs)
        # Create any data and add it to the context
        context['some_data'] = 'This is just some data'
        return context


class BookDetailView(generic.DetailView):
    model = Book

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book_instances = self.object.bookinstance_set.select_related().all()
        
        # Add a flag to each book instance to indicate if it is available
        for copy in book_instances:
            copy.is_available = (copy.status == LoanStatus.AVAILABLE.value)

        context['book_instances'] = book_instances        
        return context


    def book_detail_view(request, primary_key):
        book = get_object_or_404(Book, pk=primary_key)
        book_instances = book.bookinstance_set.select_related().all()

        context = {
            'book': book,
            'book_instances': book_instances,
        }
        return render(
            request,
            'catalog/book_detail.html',
            context=context
        )
