from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from mail2 import send_email
import random
import string
import pymysql
from yes2 import connminh
app = Flask(__name__)
CORS(app)
