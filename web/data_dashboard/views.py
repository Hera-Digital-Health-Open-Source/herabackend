from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from datetime import datetime
from django.db import connection
from rest_framework import status
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

class UserCustomAuthenticationViewSet(ViewSet):
    """This class is responsible to authenticate users to the data dashboard"""
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def csrf_generator(self, request: Request):
        return JsonResponse({'message': 'CSRF token is generated'})

    @action(detail=False, methods=['post'])
    def login(self, request: Request):
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            response = JsonResponse({'message': 'Authentication successful'})
            response.status_code = 200
            response.set_cookie('sessionid', request.session.session_key, httponly=True, secure=True) # Set session cookie
            return response
        else:
            response = JsonResponse({'message': 'Invalid credentials'})
            response.status_code = 401
            return response

    @action(detail=False, methods=['post'])
    def logout(self, request: Request):
        print('I am drere')
        if request.user.is_authenticated:
            logout(request)
            response = JsonResponse({'message': 'Logged out successfully'})
            response.status_code = 200
            response.delete_cookie('sessionid') # Delete session cookie
            return response
        else:
            response = JsonResponse({'message': 'User is not authenticated'})
            response.status_code = 401
            return response


class UsersDataDashboardViewSet(ViewSet):
    """This API endpoints will provide a statiscal information about users"""
    permission_classes = [IsAuthenticated]

    def get_meta_data(self, condition, values):
        meta_query = """
            SELECT userprofile.user_id, COUNT(pregnancy.id) as pregnancy_id, COUNT(child.id) as child_id
            FROM user_profile_userprofile userprofile
            LEFT JOIN child_health_pregnancy pregnancy ON pregnancy.user_id = userprofile.user_id
            LEFT JOIN child_health_child child ON child.user_id = userprofile.user_id
            {0}
            GROUP BY userprofile.user_id
        """
        meta_query = meta_query.format(condition)
        with connection.cursor() as cursor:
            cursor.execute(meta_query, values)
            rows = cursor.fetchall()

        pregnancy_no_kids = [row for row in rows if row[1] > 0 and row[2] == 0]
        pregnancy_with_kids = [row for row in rows if row[1] > 0 and row[2] > 0]
        no_pregnancy_no_kids = [row for row in rows if row[1] == 0 and row[2] == 0]
        no_pregnancy_with_kids = [row for row in rows if row[1] == 0 and row[2] > 0]
        
        return {
            'pregnancy_no_kids': len(pregnancy_no_kids),
            'pregnancy_with_kids': len(pregnancy_with_kids),
            'no_pregnancy_no_kids': len(no_pregnancy_no_kids),
            'no_pregnancy_with_kids': len(no_pregnancy_with_kids)
        }

    def get_users_date_range_statistics(self, from_date, to_date):
        main_query = """
            SELECT DATE(userprofile.agree_to_terms_at) as date, Count(userprofile.user_id) as user_count
            FROM user_profile_userprofile userprofile
            WHERE userprofile.agree_to_terms_at BETWEEN %s AND %s
            GROUP BY date
        """
        # Convert string variables to datetime objects
        main_query = main_query.format(from_date, to_date)
        values = [from_date, to_date]

        rows = []
        with connection.cursor() as cursor:
            cursor.execute(main_query, values)
            rows = cursor.fetchall()
        final_data = rows
        
        return {
            'data': [{'date': en[0], 'occurrence': en[1]} for en in final_data], 
            'meta': self.get_meta_data("WHERE userprofile.agree_to_terms_at BETWEEN %s AND %s", values)
        }

    def get_users_monthly_statistics(self, month, year):
        main_query = """
            SELECT EXTRACT(WEEK from userprofile.agree_to_terms_at) as week, Count(userprofile.user_id) as user_count
            FROM user_profile_userprofile userprofile
            WHERE EXTRACT(MONTH from userprofile.agree_to_terms_at) = {0} AND EXTRACT(YEAR from userprofile.agree_to_terms_at) = {1}
            GROUP BY week
        """
        main_query = main_query.format(month, year)
        values = [month, year]

        rows = []
        with connection.cursor() as cursor:
            cursor.execute(main_query, values)
            rows = cursor.fetchall()
        final_data = rows
        
        return {
            'data': [{'week': int(en[0]), 'occurrence': en[1]} for en in final_data], 
            'meta': self.get_meta_data("WHERE EXTRACT(MONTH from userprofile.agree_to_terms_at) = %s AND EXTRACT(YEAR from userprofile.agree_to_terms_at) = %s", values)
        }

    def get_users_yearly_statistics(self, year):
        main_query = """
            SELECT EXTRACT(MONTH from userprofile.agree_to_terms_at) as month, Count(userprofile.user_id) as user_count
            FROM user_profile_userprofile userprofile
            WHERE EXTRACT(YEAR from userprofile.agree_to_terms_at) = {0}
            GROUP BY month
        """
        main_query = main_query.format(year)
        values = [year]

        rows = []
        with connection.cursor() as cursor:
            cursor.execute(main_query, values)
            rows = cursor.fetchall()
        final_data = rows
        
        return {
            'data': [{'month': int(en[0]), 'occurrence': en[1]} for en in final_data], 
            'meta': self.get_meta_data("WHERE EXTRACT(YEAR from userprofile.agree_to_terms_at) = %s", values)
        }

    @action(detail=False, methods=['get']) 
    def users(self, request: Request):
        params = request.GET
        
        if ('from' in params and not 'to' in params) or (not 'from' in params and 'to' in params):
            return Response({'error': 'Both "from" and "to" parameters must be included'}, status=status.HTTP_400_BAD_REQUEST)
        elif ('from' in params and 'to' in params):
            # Convert string variables to datetime objects
            from_date = datetime.strptime(params['from'], "%Y-%m-%d").replace(hour=0, minute=0, second=0)
            to_date = datetime.strptime(params['to'], "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            result = self.get_users_date_range_statistics(from_date=from_date, to_date=to_date)
            return Response(result, status=status.HTTP_200_OK)
            
        if 'month' in params and not 'year' in params:
            return Response({'error': 'If you provide a "month" parameter, you should also provide the "year" parameter.'}, status=status.HTTP_400_BAD_REQUEST)
        elif 'month' in params and 'year' in params:
            result = self.get_users_monthly_statistics(params['month'], params['year'])
            return Response(result, status=status.HTTP_200_OK)

        if 'year' in params:
            result = self.get_users_yearly_statistics(params['year'])
            return Response(result, status=status.HTTP_200_OK)
        
        return Response({'error': 'You need to specify "from" and "to" parameters together, "month" parameter, or "year" parameter.'}, status=status.HTTP_400_BAD_REQUEST)
    

class PregnancyDataDashboardViewSet(ViewSet):
    """This API endpoints will provide a statiscal information about pregnancy"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get']) 
    def pregnancy(self, request: Request):
        params = request.GET
        
        if ('from' in params and not 'to' in params) or (not 'from' in params and 'to' in params):
            return Response({'error': 'Both "from" and "to" parameters must be included'}, status=status.HTTP_400_BAD_REQUEST)
        elif ('from' in params and 'to' in params):
            # Convert string variables to datetime objects
            from_date = datetime.strptime(params['from'], "%Y-%m-%d").replace(hour=0, minute=0, second=0)
            to_date = datetime.strptime(params['to'], "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            
            main_query = """
                WITH RankedResponses AS (
                    SELECT
                        user_id,
                        created_at,
                        responded_at,
                        response,
                        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY response) AS check_up_no
                    FROM
                        surveys_survey survey
                    WHERE survey.event_key LIKE %s AND (survey.created_at BETWEEN %s AND %s)
                )
                SELECT
                    check_up_no,
                    SUM(CASE WHEN response = 'yes' THEN 1 ELSE 0 END) AS count_yes,
                    SUM(CASE WHEN response = 'no' THEN 1 ELSE 0 END) AS count_no,
                    SUM(CASE WHEN response IS NULL THEN 1 ELSE 0 END) AS count_null
                FROM
                    RankedResponses
                GROUP BY
                    check_up_no
            """
            # Convert string variables to datetime objects
            values = ['prenatal-checkup%', from_date, to_date]

            rows = []
            with connection.cursor() as cursor:
                cursor.execute(main_query, values)
                rows = cursor.fetchall()
            final_data = rows

            result = {
                'data': [{'check_up_no': en[0], 'yes': en[1], 'no': en[2], 'no_response': en[3]} for en in final_data]
            }

            return Response(result, status=status.HTTP_200_OK)
        

class VaccinationDataDashboardViewSet(ViewSet):
    """This API endpoints will provide a statiscal information about vaccinations"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get']) 
    def vaccinations(self, request: Request):
        params = request.GET
        
        if ('from' in params and not 'to' in params) or (not 'from' in params and 'to' in params):
            return Response({'error': 'Both "from" and "to" parameters must be included'}, status=status.HTTP_400_BAD_REQUEST)
        elif ('from' in params and 'to' in params):
            # Convert string variables to datetime objects
            from_date = datetime.strptime(params['from'], "%Y-%m-%d").replace(hour=0, minute=0, second=0)
            to_date = datetime.strptime(params['to'], "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            
            main_query = """
                SELECT
                    vaccine.name as vaccine_name,
                    SUM(CASE WHEN survey.response = 'yes' THEN 1 ELSE 0 END) AS count_yes,
                    SUM(CASE WHEN survey.response = 'no' THEN 1 ELSE 0 END) AS count_no,
                    SUM(CASE WHEN survey.response IS NULL THEN 1 ELSE 0 END) AS count_null
                FROM child_health_vaccine vaccine
                JOIN surveys_survey survey ON survey.context -> 'vaccine_names' LIKE '%' || vaccine.name || '%'
                WHERE survey.created_at BETWEEN '{0}' AND '{1}'
                GROUP BY vaccine.name, survey.response 
            """
            main_query = main_query.format(from_date, to_date)


            rows = []
            with connection.cursor() as cursor:
                cursor.execute(main_query)
                rows = cursor.fetchall()
            final_data = rows

            result = {
                'data': [{'vaccine_name': en[0], 'yes': en[1], 'no': en[2], 'no_response': en[3]} for en in final_data]
            }

            return Response(result, status=status.HTTP_200_OK)