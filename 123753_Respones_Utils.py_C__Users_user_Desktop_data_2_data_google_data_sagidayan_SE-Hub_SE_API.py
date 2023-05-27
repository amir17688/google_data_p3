__author__ = 'Aran'

from flask import Response
import json


def ok(message='OK'):
    return Response(response=json.dumps({'message': message}),
                        status=200,
                        mimetype="application/json")

def created(message='Created'):
    return Response(response=json.dumps({'message': message}),
                        status=201,
                        mimetype="application/json")

def accepted(message='Accepted'):
    return Response(response=json.dumps({'message': message}),
                        status=202,
                        mimetype="application/json")


def no_content(message='No Content'):
    return Response(response=json.dumps({'message': message}),
                        status=204,
                        mimetype="application/json")


def bad_request(message='Bad Request'):
    return Response(response=json.dumps({'message': message}),
                        status=400,
                        mimetype="application/json")


def forbidden(message='Forbidden'):
    return Response(response=json.dumps({'message': message}),
                        status=403,
                        mimetype="application/json")