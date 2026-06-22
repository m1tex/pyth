from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from django.middleware.csrf import get_token
from django.core.signing import TimestampSigner
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.hashers import PBKDF2PasswordHasher
import re
import json


def call_func(name: str, parameters: dict = None):

    with connection.cursor() as cursor:
        if parameters:
            this_params = []
            for value in parameters.values():
                if value is None:
                    this_params.append("NULL")
                elif isinstance(value, str):
                    escaped_value = value.replace("'", "''")
                    this_params.append(f"'{escaped_value}'")
                elif isinstance(value, int):
                    this_params.append(str(value))
                elif isinstance(value, float):
                    this_params.append(str(value))
                elif isinstance(value, bool):
                    this_params.append(str(value).upper())
                else:
                    escaped_value = str(value).replace("'", "''")
                    this_params.append(f"'{escaped_value}'")
            
            query = f"SELECT * FROM testdrive.{name}({', '.join(this_params)})"
            cursor.execute(query)
        else:
            cursor.execute(f"SELECT * FROM testdrive.{name}()")
        
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def api_get_xcsrf(request):
    data = {'X-CSRF-Token': get_token(request)}
    return JsonResponse(data, safe=False, status=200)


def is_auth(request):

    if not request.headers.get('Authorization'):
        return None
    
    token = request.headers.get('Authorization').split(' ')[-1]
    signer = TimestampSigner(salt='django.core.signing')
    
    try:
        login = signer.unsign(
            force_str(urlsafe_base64_decode(token)),
            max_age=1000
        )
    except:
        return None
    
    user = call_func('user_get', {'in_search_value': login})
    return user[0] if user else None


def api_statuses(request):

    if request.method == 'GET':
        try:
            result = call_func('status_get')
            formatted = [{'pk_status': r['pk_status'], 'title': r['title']} for r in result]
            return JsonResponse(formatted, safe=False, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, safe=False, status=500)
    
    if request.method == 'POST':
        auth_result = is_auth(request)
        if not auth_result:
            return JsonResponse({"message": "Доступ запрещен"}, status=403)

        user = auth_result
        if not user.get('is_admin'):
            return JsonResponse(
                {"message": "Доступ запрещен. Только для администратора"},
                status=403
            )

        if request.content_type == 'application/json':
            data = json.loads(request.body)
            title = data.get('title')
        else:
            title = request.POST.get('title')

        if not title:
            return JsonResponse({"error": "Название статуса обязательно"}, status=400)

        try:
            result = call_func('status_post', {'in_title': str(title)})
            return JsonResponse({
                "message": "Статус успешно создан",
                "pk_status": result[0]["pk_status"],
                "title": title
            }, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


def api_payment_types(request):

    if request.method == 'GET':
        try:
            result = call_func('payment_type_get')
            formatted = [{'pk_payment_type': r['pk_payment_type'], 'title': r['title']} for r in result]
            return JsonResponse(formatted, safe=False, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, safe=False, status=500)

    if request.method == 'POST':
        auth_result = is_auth(request)
        if not auth_result:
            return JsonResponse({"message": "Доступ запрещен"}, status=403)

        user = auth_result
        if not user.get('is_admin'):
            return JsonResponse(
                {"message": "Доступ запрещен. Только для администратора"},
                status=403
            )

        if request.content_type == 'application/json':
            data = json.loads(request.body)
            title = data.get('title')
        else:
            title = request.POST.get('title')

        if not title:
            return JsonResponse({"error": "Название способа оплаты обязательно"}, status=400)

        try:
            result = call_func('payment_type_post', {'in_title': str(title)})
            return JsonResponse({
                "message": "Способ оплаты успешно создан",
                "pk_payment_type": result[0]["pk_payment_type"],
                "title": title
            }, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


def api_cars(request):

    if request.method == 'GET':
        try:
            result = call_func('car_get')
            formatted = []
            for item in result:
                formatted.append({
                    'pk_car': item['pk_car'],
                    'brand': item['car_brand_title'],
                    'model': item['car_model_title']
                })
            return JsonResponse(formatted, safe=False, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, safe=False, status=500)

    if request.method == 'POST':
        auth_result = is_auth(request)
        if not auth_result:
            return JsonResponse({"message": "Доступ запрещен"}, status=403)

        user = auth_result
        if not user.get('is_admin'):
            return JsonResponse(
                {"message": "Доступ запрещен. Только для администратора"},
                status=403
            )

        if request.content_type == 'application/json':
            data = json.loads(request.body)
            car_number = data.get('car_number')
            brand = data.get('brand')
            model = data.get('model')
        else:
            car_number = request.POST.get('car_number')
            brand = request.POST.get('brand')
            model = request.POST.get('model')

        if not car_number:
            return JsonResponse({"error": "Номер автомобиля обязателен"}, status=400)
        if not brand:
            return JsonResponse({"error": "Название бренда обязательно"}, status=400)
        if not model:
            return JsonResponse({"error": "Название модели обязательно"}, status=400)

        try:
            result = call_func('car_post', {
                'in_car_number': str(car_number),
                'in_title_car_brand': str(brand),
                'in_title_car_model': str(model)
            })
            return JsonResponse({
                "message": "Автомобиль успешно добавлен",
                "pk_car": result[0]["pk_car"],
                "car_number": car_number,
                "brand": brand,
                "model": model
            }, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


def api_applications(request):

    auth_result = is_auth(request)
    if not auth_result:
        return JsonResponse({"message": "Доступ запрещен"}, safe=False, status=403)

    user = auth_result

    if request.method == 'GET':
        try:
            if user['is_admin']:
                results = call_func('application_get', {'id_user': None})
            else:
                results = call_func('application_get', {'id_user': user['pk_user']})
            return JsonResponse(results, safe=False, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, safe=False, status=500)

    if request.method == 'POST':
        errors = []

        contact_info = request.POST.get('contact_info')
        address = request.POST.get('address')
        date = request.POST.get('date')
        time = request.POST.get('time')
        fk_payment_type = request.POST.get('fk_payment_type')
        fk_car = request.POST.get('fk_car')

        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        time_pattern = re.compile(r'^\d{2}:\d{2}(:\d{2})?$')

        if not contact_info:
            errors.append("Поле 'Контактная информация' обязательно для заполнения.")
        if not address:
            errors.append("Поле 'Адрес' обязательно для заполнения.")
        if not date:
            errors.append("Поле 'Дата' обязательно для заполнения.")
        elif not date_pattern.match(date):
            errors.append("Некорректный формат даты. Используйте YYYY-MM-DD")
        if not time:
            errors.append("Поле 'Время' обязательно для заполнения.")
        elif not time_pattern.match(time):
            errors.append("Некорректный формат времени. Используйте HH:MM:SS")
        if not fk_payment_type:
            errors.append("Поле 'Тип оплаты' обязательно для заполнения.")
        if not fk_car:
            errors.append("Поле 'Автомобиль' обязательно для заполнения.")

        if errors:
            return JsonResponse({"errors": errors}, safe=False, status=400)

        try:
            result = call_func('application_post', {
                'in_contact_info': contact_info,
                'in_address': address,
                'in_date': date,
                'in_time': time,
                'id_payment_type': int(fk_payment_type),
                'id_user': user['pk_user'],
                'id_car': int(fk_car)
            })
            new_id = result[0].get('pk_application') or list(result[0].values())[0]
            return JsonResponse({
                "message": "Заявка успешно создана",
                "pk_application": new_id
            }, safe=False, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, safe=False, status=500)

    if request.method == 'PATCH':
        if not user.get('is_admin'):
            return JsonResponse(
                {"message": "Доступ запрещен. Только для администратора"},
                safe=False, status=403
            )

        errors = []
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            pk_application = data.get('pk_application')
            pk_status = data.get('pk_status')
            reason = data.get('reason')
        else:
            pk_application = request.POST.get('pk_application') or request.GET.get('pk_application')
            pk_status = request.POST.get('pk_status') or request.GET.get('pk_status')
            reason = request.POST.get('reason') or request.GET.get('reason')

        if not pk_application:
            errors.append("Не указан pk_application")
        if not pk_status:
            errors.append("Не указан pk_status")

        if errors:
            return JsonResponse({"errors": errors}, safe=False, status=400)

        try:
            result = call_func('application_patch', {
                'id_application': int(pk_application),
                'id_status': int(pk_status),
                'in_reason': reason
            })
            success = result[0].get('confirm') or list(result[0].values())[0]
            if success:
                return JsonResponse({
                    "message": "Статус заявки успешно изменен",
                    "pk_application": pk_application,
                    "new_status": pk_status
                }, safe=False, status=200)
            else:
                return JsonResponse({
                    "message": "Заявка не найдена",
                    "pk_application": pk_application
                }, safe=False, status=404)
        except Exception as e:
            return JsonResponse(
                {"message": f"Ошибка при изменении статуса: {str(e)}"},
                safe=False, status=500
            )


def api_users(request):

    if is_auth(request):
        return JsonResponse({"message": "Вы уже авторизованы"}, safe=False, status=403)

    if request.method == 'POST':
        errors = []

        lastname = request.POST.get('lastname')
        firstname = request.POST.get('firstname')
        middlename = request.POST.get('middlename')
        login = request.POST.get('login')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        email = request.POST.get('email')

        name_pattern = re.compile(r'^[a-zA-Zа-яА-ЯёЁ\s\-]+$')
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        phone_pattern = re.compile(r'^\+?[0-9\-\(\)\s]{7,15}$')

        if not lastname:
            errors.append("Поле 'Фамилия' обязательно для заполнения.")
        elif len(lastname) < 2 or len(lastname) > 50:
            errors.append("Фамилия должна быть длиной от 2 до 50 символов.")
        elif not name_pattern.match(lastname):
            errors.append("Фамилия может содержать только буквы, пробелы и дефисы.")

        if not firstname:
            errors.append("Поле 'Имя' обязательно для заполнения.")
        elif len(firstname) < 2 or len(firstname) > 50:
            errors.append("Имя должно быть длиной от 2 до 50 символов.")
        elif not name_pattern.match(firstname):
            errors.append("Имя может содержать только буквы, пробелы и дефисы.")

        if middlename:
            if len(middlename) < 2 or len(middlename) > 50:
                errors.append("Отчество должно быть длиной от 2 до 50 символов.")
            elif not name_pattern.match(middlename):
                errors.append("Отчество может содержать только буквы, пробелы и дефисы.")

        if not login:
            errors.append("Поле 'Логин' обязательно для заполнения.")
        elif len(login) < 4 or len(login) > 150:
            errors.append("Логин должен быть длиной от 4 до 150 символов.")

        if not password:
            errors.append("Поле 'Пароль' обязательно для заполнения.")
        elif len(password) < 6 or len(password) > 128:
            errors.append("Пароль должен быть длиной от 6 до 128 символов.")

        if not email:
            errors.append("Поле 'Email' обязательно для заполнения.")
        elif not email_pattern.match(email):
            errors.append("Некорректный формат email.")
        elif len(email) > 255:
            errors.append("Email должен быть короче 255 символов.")

        if not phone:
            errors.append("Поле 'Номер телефона' обязательно для заполнения.")
        elif not phone_pattern.match(phone):
            errors.append("Некорректный формат номера телефона.")

        if errors:
            return JsonResponse({"errors": errors}, status=400)

        try:
            existing_by_login = call_func('user_get', {'in_search_value': login})
            existing_by_email = call_func('user_get', {'in_search_value': email})
            if existing_by_login or existing_by_email:
                return JsonResponse({
                    "message": "Пользователь с таким логином или email уже существует"
                }, status=409)
        except Exception:
            pass

        hasher = PBKDF2PasswordHasher()
        hashed_password = hasher.encode(password, salt='extra', iterations=1200000)

        try:
            result = call_func('user_post', {
                'in_lastname': lastname,
                'in_firstname': firstname,
                'in_middlename': middlename if middlename else '',
                'in_phone': phone,
                'in_email': email,
                'in_login': login,
                'in_password_hash': hashed_password
            })
            new_user_id = result[0].get('pk_user') or list(result[0].values())[0]
            return JsonResponse({
                "message": "Пользователь успешно создан",
                "pk_user": new_user_id
            }, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


def api_auth(request):

    if is_auth(request):
        return JsonResponse({"message": "Доступ запрещен"}, safe=False, status=403)

    if request.method == 'POST':
        errors = []
        login = request.POST.get('login')
        password = request.POST.get('password')

        if not login:
            errors.append("Поле 'Логин' обязательно для заполнения.")
        elif len(login) < 4 or len(login) > 150:
            errors.append("Логин должен быть длиной от 4 до 150 символов.")

        if not password:
            errors.append("Поле 'Пароль' обязательно для заполнения.")
        elif len(password) < 6 or len(password) > 128:
            errors.append("Пароль должен быть длиной от 6 до 128 символов.")

        if errors:
            return JsonResponse({"errors": errors}, status=400)

        user_result = call_func('user_get', {'in_search_value': login})
        if user_result and len(user_result) > 0:
            user = user_result[0]
            hasher = PBKDF2PasswordHasher()
            if hasher.verify(password, user['password_hash']):
                signer = TimestampSigner(salt='django.core.signing')
                token = urlsafe_base64_encode(force_bytes(signer.sign(login)))
                response = {
                    "pk_user": user['pk_user'],
                    "lastname": user['lastname'],
                    "firstname": user['firstname'],
                    "middlename": user['middlename'],
                    "login": user['login'],
                    "phone": user['phone'],
                    "email": user['email'],
                    "is_admin": user['is_admin'],
                    "is_active": user['is_active'],
                    "token": token
                }
                return JsonResponse(response, safe=False, status=200)
            else:
                return JsonResponse({"message": "Неверный логин или пароль"}, safe=False, status=401)
        else:
            return JsonResponse({"message": "Неверный логин или пароль"}, safe=False, status=401)