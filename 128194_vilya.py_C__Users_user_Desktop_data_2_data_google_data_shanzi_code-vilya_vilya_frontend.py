# -*- coding: utf-8 -*-
from flask import (Blueprint,
                   render_template)
from . import route

bp = Blueprint('shanks', __name__)


@route(bp, '/')
def index():
    """Returns the index interface."""
    return render_template('index.html')
