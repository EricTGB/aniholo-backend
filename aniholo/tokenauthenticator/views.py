from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from django.forms.models import model_to_dict

from . import models
from aniholo import settings

import jwt

from datetime import datetime
import time
import ast

def isValidToken(token):
	secret_key = settings.SECRET_KEY

	payload = None

	try:
		payload = jwt.decode(token, secret_key)
	except (Exception):
		return False

	if ("expire_time" in payload):
		received_expire_time = payload.get("expire_time")
		return int(time.time()) < received_expire_time
	return True

@csrf_exempt 
@api_view(['GET', 'POST', ])
def register(request):
	content = {'status': 'success'}

	event1 = models.Account(username=request.POST.get("username"), email=request.POST.get("email"), password=request.POST.get("password"), created_on=datetime.today())
	
	try:
		event1.save()
	except:
		content = {'status': 'failed'}

	return Response(content)

@csrf_exempt 
@api_view(['GET', 'POST', ])
def login_request(request):
	#TODO - Set server-side limits to refresh times
	#TODO - Have password hashing for security
	#TODO - Sanitize everything
	if request.method == 'POST':
		username = ""
		if "username" in request.POST:
			username = request.POST.get("username")
		else:
			return Response({"status": "failed - must include both username and password"})
		password = ""
		if "password" in request.POST:
			password = request.POST.get("password")
		else:
			return Response({"status": "failed - must include both username and password"})
		expire_time = 600
		if "expire_time" in request.POST:
			expire_time = int(request.POST.get('expire_time'))
		refresh_expire_time = 60 * 60 * 24
		if "refresh_expire_time" in request.POST:
			refresh_expire_time = int(request.POST.get('refresh_expire_time'))

		record = models.Account.objects.get(username=username)
		if (not password == record.password):
			return Response({"status": "failed - incorrect login details"})

		ts = int(time.time()) # adding issual_time and expire_time
		secret_key = settings.SECRET_KEY #get server's secret key from settings.py
		actual_json_data = model_to_dict(record)
		refresh_token_content = {
				"username": actual_json_data.get('username'),
				"issual_time": ts,
				"expire_time" : ts+refresh_expire_time
	    }
		refresh_Token = {'refreshToken': jwt.encode(refresh_token_content, secret_key)}
		temp = refresh_Token.get('refreshToken')
		actual_refresh_token = temp.decode("utf-8")

		ts = int(time.time()) # adding issual_time and expire_time
		access_token_content = {
			"username": actual_json_data.get('username'),
			"issual_time": ts,
			"expire_time" : ts+expire_time
		}
		jwt_token = {'token': jwt.encode(access_token_content,secret_key)}
		u = jwt_token.get('token')
		actual_access_token = u.decode("utf-8")
		ts = float(time.time())

		headers = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Origin, X-Requested-With, Content-Type, Accept"}
		return Response({"status": "success", "refresh": actual_refresh_token, "access": actual_access_token}, headers=headers)

@csrf_exempt 
@api_view(['GET', 'POST', ])
def refresh_request(request):
	if request.method == 'POST':
		refresh_token = ""
		if ("refresh" in request.POST):
			refresh_token = request.POST.get('refresh')
		else:
			return Response({"status: failed - must include refresh token"})

		secret_key = settings.SECRET_KEY

		if not isValidToken(refresh_token):
			return Response({"access": "failed"})

		payload = jwt.decode(refresh_token, secret_key)
		
		username = payload.get('username')
		expire_time = int(request.POST.get('expire_time'))

		ts = int(time.time()) # adding issual_time and expire_time
		access_token_content = {
			"username": username,
			"issual_time": ts,
			"expire_time" : ts+expire_time
		}
		jwt_token = {'token': jwt.encode(access_token_content,secret_key)}
		u = jwt_token.get('token')
		actual_access_token = u.decode("utf-8")

		return Response({"status": "success", "access": actual_access_token})

@csrf_exempt 
@api_view(['GET', 'POST', ])
def test_token(request):
	if request.method == 'POST':
		if isValidToken(request.POST.get("token")):
			return Response({"valid": "true"})
		return Response({"valid": "false"})

@csrf_exempt 
@api_view(['GET', 'POST', ])
def create_post(request):
	if request.method == 'POST':

		if not isValidToken(request.POST.get("token")):
			return Response({"status": "failed - invalid token"})

		secret_key = settings.SECRET_KEY
		payload = jwt.decode(request.POST.get("token"), secret_key)

		username = payload.get("username")
		title = request.POST.get("title")

		image_link = ""
		if ("link" in request.POST):
			image_link = request.POST.get("link")

		date_posted = datetime.today()
		current_upvotes = "0"
		current_downvotes = "0"

		is_nsfw = False
		if ("is_nsfw" in request.POST):
			is_nsfw = bool(request.POST.get('is_nsfw'))

		is_spoiler = False
		if ("is_spoiler" in request.POST):
			is_spoiler = bool(request.POST.get('is_spoiler'))

		is_announcement = False
		if ("is_announcement" in request.POST):
			is_announcement = bool(request.POST.get('is_announcement'))

		required_tag = "Discussion"
		if ("required_tag" in request.POST):
			required_tag = bool(request.POST.get('required_tag'))
		else:
			return Response({"status: failed - must a required tag"})

		other_tags = ""
		if ("tags" in request.POST):
			other_tags = str(request.POST.get('tags'))
		other_tags_array = ast.litera_val(other_tags)

		source_material = ""
		if ("source_material" in request.POST):
			source_material = bool(request.POST.get('source_material'))

		post_text = ""
		if ("post_text" in request.POST):
			post_text = bool(request.POST.get('post_text'))

		post_type = ""
		if ("post_type" in request.POST):
			post_type = bool(request.POST.get('post_type'))

		post = models.Posts(author=username, title=title,
						   upvotes=current_upvotes, downvotes=current_downvotes,
						   date_posted=date_posted, image_link=image_link, is_nsfw=is_nsfw,
						   is_spoiler=is_spoiler, is_announcement=is_announcement,
						   required_tag=required_tag,
						   source_material=source_material,
						   post_text=post_text, post_type=post_type)

		content = {'status': 'success'}
		
		try:
			# for tag in other_tags_array:
				# if (len(models.Tags.objects.filter(tag_name=tag.lower()) == 0)):
					# tag = models.Tags(tag_name=tag.lower())
					

			post.save()
		except:
			content = {'status': 'failed'}

		return Response(content)