from flask import Flask, abort, render_template, redirect, url_for, flash
from . import pages_bp



@pages_bp.route("/")
def home():
    return render_template('home.html')


@pages_bp.route("/contact")
def contact():
    return render_template('contact.html')


@pages_bp.route("/about")
def about():
    return render_template('about.html')


