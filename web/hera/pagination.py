from rest_framework.pagination import CursorPagination


class StandardPagination(CursorPagination):
	ordering = '-pk'
