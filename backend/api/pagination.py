from rest_framework.pagination import PageNumberPagination


class StandartPagination(PageNumberPagination):
    """Пользовательский пагинатор."""
    page_size = 6
    page_size_query_param = 'page_size'
    page_query_param = 'page'
