from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('books/', views.BookListView.as_view(), name='books'),
    path('book/<int:pk>', views.BookDetailView.as_view(), name='book-detail'),
    path('mybooks/', views.LoanedBooksByUserListView.as_view(), name='my-borrowed'),
    path(
        'books/<uuid:pk>/return/',
        views.MarkBookAsReturnedView.as_view(),
        name='mark-returned',
    ),
    path(
        'book/<uuid:pk>/renew/',
        views.renew_book_librarian,
        name='renew-book-librarian'
    ),
    path('authors/', views.AuthorListView.as_view(), name='authors'),
    path(
        "author/<int:pk>/",
        views.AuthorDetailView.as_view(),
        name="author-detail",
    ),
    path('author/create/', views.AuthorCreate.as_view(), name='author-create'),
    path('author/<int:pk>/update/', views.AuthorUpdate.as_view(), name='author-update'),
    path('author/<int:pk>/delete/', views.AuthorDelete.as_view(), name='author-delete'),
]
