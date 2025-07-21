from django.shortcuts import render, get_object_or_404
from django.views import generic, View
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from catalog.models import Book, Author, BookInstance, Genre
from catalog.constants import LoanStatus, PAGINATION_SIZE
from catalog.forms import RenewBookForm

import datetime

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

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 1)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits,
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
        context["can_mark_returned"] = self.request.user.has_perm(
            "catalog.can_mark_returned"
        )

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

class LoanedBooksByUserListView(generic.ListView):

    model = BookInstance
    template_name = "catalog/bookinstance_list_borrowed_user.html"
    paginate_by = PAGINATION_SIZE

    def get_queryset(self):
        """Return the books on loan to the current user."""
        return (
            BookInstance.objects.filter(
                borrower=self.request.user,
                status__exact=LoanStatus.ON_LOAN.value
            ).order_by("due_back")
        )

class MarkBookAsReturnedView(PermissionRequiredMixin, View):

    permission_required = "catalog.can_mark_returned"

    def get(self, request, *args, **kwargs):
        book_instance = get_object_or_404(BookInstance, pk=kwargs["pk"])
        return render(
            request,
            "catalog/bookinstance_mark_as_returned.html",
            {
                "bookinstance": book_instance,
            },
        )

    def post(self, request, *args, **kwargs):
        """Process the form submission (confirm return)."""
        book_instance = get_object_or_404(BookInstance, pk=kwargs["pk"])
        book_instance.status = LoanStatus.AVAILABLE.value
        book_instance.borrower = None
        book_instance.save()

        # Redirect to the book detail page after returning
        return redirect("book-detail", pk=book_instance.book.pk)


@login_required
def my_borrowed_books(request):
    borrowed_books = BookInstance.objects.filter(
        borrower=request.user,
        status=LoanStatus.ON_LOAN.value
    )
    context = {
        'borrowed_books': borrowed_books,
        'LoanStatus': LoanStatus,
    }
    return render(request, 'catalog/my_borrowed_books.html', context=context)

class AuthorCreate(CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial = {'date_of_death': '11/06/2020'}

class AuthorUpdate(UpdateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']

class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('authors')

class AuthorListView(generic.ListView):
    """Generic class-based view for a list of authors."""

    model = Author
    paginate_by = PAGINATION_SIZE
    context_object_name = "author_list"
    template_name = "catalog/author_list.html"
    queryset = Author.objects.all().order_by("last_name", "first_name")

    def get_context_data(self, **kwargs):
        """Add additional context data to the view."""
        context = super(AuthorListView, self).get_context_data(**kwargs)
        context["can_add_author"] = self.request.user.has_perm(
            "catalog.can_add_author"
        )
        return context

class AuthorDetailView(generic.DetailView):
    """Generic class-based view for an author detail page."""

    model = Author

    def get_context_data(self, **kwargs):
        """Add additional context data to the view."""
        context = super(AuthorDetailView, self).get_context_data(**kwargs)
        context["book_set"] = Book.objects.filter(author=self.object).order_by(
            "title"
        )
        context["can_update_author"] = self.request.user.has_perm(
            "catalog.change_author"
        )
        context["can_delete_author"] = self.request.user.has_perm(
            "catalog.delete_author"
        )
        return context


@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def mark_book_returned(request, bookinstance_id):
    bookinstance = get_object_or_404(BookInstance, id=bookinstance_id)
    if request.method == 'POST':
        bookinstance.status = LoanStatus.AVAILABLE.value
        bookinstance.borrower = None
        bookinstance.due_date = None
        bookinstance.save()
    return redirect('catalog:my_borrowed_books')


@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    
    book_instance = get_object_or_404(BookInstance, pk=pk)
    
    # If this is a POST request then process the Form data
    if request.method == 'POST':
        form = RenewBookForm(request.POST)
        # Check if the form is valid:
        if form.is_valid():
        # process the data in form.cleaned_data as required (here we just write it to the modeldue_back field)
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            return HttpResponseRedirect(reverse('my-borrowed') )

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)
