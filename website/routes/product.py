from os import abort
import os
from flask import Blueprint, render_template, request, flash, redirect, jsonify, abort, url_for
from website import db, limiter
from website.models.product import Product
from website.models.branch import Branch
from flask_login import login_required, current_user
from sqlalchemy.sql.expression import func
import requests

product = Blueprint('product', __name__)

@product.route('/product', methods=['GET', 'POST'])
@limiter.limit("20/minute")
@login_required
def prod():
    """products available in the inventory and in their entries"""

    #if user is not confirmed, block access and send to home
    #if current_user.confirmed is False:
    #    flash('Please confirm your account, check your email (and spam folder)', 'error')
    #    return redirect(url_for('views.home'))

    # if user presses Search
    if request.method == 'POST' and "btn-srch" in request.form:
        search = request.form.get("search")

        #checks that products are from user
        userprod = Product.query.filter(Product.owner == current_user.email)

        # search input section
        data = userprod.filter(
            (Product.id.like(search)) | (Product.name.like('%' + search + '%')) | (Product.qr_barcode.like(search)))

        return render_template('product.html', user=current_user, products=data)

    if request.method == 'POST' and "btn-add" in request.form:
        prodDict = request.form.to_dict()
        name = prodDict.get('name')    
        qr_barcode = prodDict.get('qr_barcode')
        description = prodDict.get('description')


        if name:
            name = name.strip()
            currentName = Product.query.filter(
                (Product.name==name) & (Product.owner==current_user.email)).first()
            if currentName and name.lower() == currentName.name.lower():
                flash('Product already exists', 'error')
                return redirect(url_for('product.prod'))

            prodDict['name'] = name
            # adding new product instance to database
            prodDict['owner'] = current_user.email
            if description == '' or description is None:
                prodDict['description'] = 'No description'
            new_prod = Product(**prodDict)
            db.session.add(new_prod)
            db.session.commit()
            if qr_barcode == 'qr':
                generate_qr(new_prod.id)
            elif qr_barcode == 'barcode':
                generate_barcode(new_prod.id)
            db.session.commit()
            flash("Poduct added", category='success')
            return redirect('/product')
        else:
            flash('Name, Branch and Quantity are mandatory fields', category='error')
    # branches to display as options in add product table
    branches = Branch.query.filter_by(owner=current_user.email)
    # hardprint next id for new product
    nextid = db.session.query(func.max(Product.id)).scalar()

    data = Product.query.filter_by(owner=current_user.email).paginate(per_page=10)
    return render_template('product.html', user=current_user,
                           branches=branches, nextid=nextid, products=data)


@product.route('/product/<id>', methods=['POST','GET'], strict_slashes=False)
@limiter.limit("20/minute")
@login_required
def prodUpdate(id):
    """updating or consulting item from product"""
    item = Product.query.filter_by(id=id).first()
    if request.method == 'POST':
        prodDict = request.form.to_dict()

        if prodDict is None:
            abort(404)

        #updating description if exists

        description = prodDict.get('descriptionUpdate')
        if description is None:

            description = prodDict.get('descriptionBarcodeUpdate')

        if description:
            item.description = description
            db.session.commit()

        qr_barcode = prodDict.get('qr_barcodeUpdate')
        if qr_barcode is None:
            qr_barcode = prodDict.get('qr_barcodeBarcodeUpdate')
        if qr_barcode:

            if qr_barcode == 'qr' and item.qr_barcode != qr_barcode:
                generate_qr(item.id)
            elif qr_barcode == 'barcode' and item.qr_barcode != qr_barcode:
                generate_barcode(item.id)

            item.qr_barcode = qr_barcode
            db.session.commit()

            flash("Item updated successfully!", category='success')
            return redirect('/product')
        else:
            flash('Name, Branch and Quantity are mandatory fields', category='error')
    try:
        # filter query by logged user and id
        product = Product.query.filter(
            (Product.owner==current_user.email) & (Product.id==id)).first()
        # making a diccionary to use the GET method as API
        toDict = product.__dict__
        toDict.pop('_sa_instance_state')
        branches = Branch.query.filter_by(owner=current_user.email).all()
        toDict['branches'] = [branch.name for branch in branches]
        return jsonify(toDict)
    except Exception:
        abort(404)

def generate_qr(id):
    """consulting API which generates a qr"""
    url = "https://qrickit-qr-code-qreator.p.rapidapi.com/api/qrickit.php"

    querystring = {"d":f'{id}'}

    headers = {
	            "X-RapidAPI-Key": "b542ab94a6msh4122c7211f10621p125c2ejsne10b1b5c4697",
	            "X-RapidAPI-Host": "qrickit-qr-code-qreator.p.rapidapi.com"
                }

    response = requests.request("GET", url, headers=headers, params=querystring)

    #taking the content's bytes to write the PNG img
    image_data = response._content
    path = f'./../static/images/qr.{id}.png'
    with open(os.path.join(os.path.dirname(__file__), path), 'wb+') as out_file:
        out_file.write(image_data)

def generate_barcode(id):
    """consulting API which generates a barcode"""
    
    url = "https://barcode-generator4.p.rapidapi.com/"

    querystring = {"text":f'{id}',"barcodeType":"C128","imageType":"PNG"}

    headers = {
    	"X-RapidAPI-Key": "71760ccf2fmshaa151dcb49bd23cp1ad4b7jsn1d74bdc7fa4e",
    	"X-RapidAPI-Host": "barcode-generator4.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    image_data = response.json().get('barcode')
    import base64
    try:
        #encoding string to bytes to then write a file with the PNG img
        image_data = base64.b64decode(image_data.replace('data:image/PNG;base64,', '').encode())
        path = f'./../static/images/barcode.{id}.png'
        with open(os.path.join(os.path.dirname(__file__), path), 'wb+') as out_file:
            out_file.write(image_data)
        return response.json().get('barcode')
    except:
        pass