#import
from sqlalchemy.sql import func;
from sqlalchemy.orm import sessionmaker
from flask import Flask, render_template, request, redirect, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, ForeignKey

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
from sqlalchemy.orm import relationship

#deklarasi aplikasi baru flask
app = Flask(__name__)    
app.secret_key = "Secret Key"

#menghubungkan ke database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/smartcard'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

engine = create_engine('mysql://root:''@localhost/smartcard', echo = True)

#table models
class Siswa(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(10))
    nis = db.Column(db.String(10), unique = True)
    kelas = db.Column(db.String(5))
    saldo = db.Column(db.Integer)

    def __init__(self, name, nis, kelas, saldo):
        self.name = name
        self.nis = nis
        self.kelas = kelas
        self.saldo = saldo

class Barang(db.Model):
     id = db.Column(db.Integer, primary_key = True)
     kd_barang = db.Column(db.String(5), unique=True)
     harga = db.Column(db.Integer)
     nama = db.Column(db.String(10))

     def __init__(self, kd_barang, harga, nama):
            self.kd_barang = kd_barang
            self.nama = nama
            self.harga = harga
    
class Pembelian(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    kd_barang = db.Column(db.String(5), ForeignKey('barang.kd_barang', ondelete="CASCADE"))
    harga = db.Column(db.Integer)

    def __init__(self, kd_barang, harga):
        self.kd_barang = kd_barang
        self.harga = harga
    
    barang = relationship(Barang)

class Riwayat(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    siswa_id = db.Column(db.Integer, ForeignKey('siswa.id', ondelete="CASCADE"))
    saldo = db.Column(db.Integer)
    total = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def __init__(self, siswa_id, saldo, total):
            self.siswa_id = siswa_id
            self.saldo = saldo
            self.total = total

    siswa = relationship(Siswa)

with app.app_context():
    db.create_all()

Session = sessionmaker(bind = engine)
session = Session()

#route 
@app.route('/')
def home():
    siswa = session.query(Siswa).all()
    return render_template('info.html', siswa = siswa)

@app.route('/beli')
def beli():
    siswa = session.query(Siswa).all()
    beli = session.query(Pembelian).all()

    totalList = []
    for harga in beli:
         harga = harga.harga
         totalList.append(harga)
    total = sum(totalList)

    return render_template('beli.html', siswa = siswa, table = beli, total = total)

@app.route('/beli/tambah', methods=['GET', 'POST'])
def tambah():
     if request.method == "POST":
        kd_barang = request.form.get("kode_barang")
        barang = session.query(Barang).filter_by(kd_barang = kd_barang).first()

        new_Pembelian = Pembelian(kd_barang=kd_barang,
                                harga=barang.harga)
        session.add(new_Pembelian)
        session.commit()

        # return redirect('/beli')
        return jsonify('berhasil')

@app.route('/beli/bayar',  methods=['GET', 'POST'])
def bayar():
     if request.method == "POST":
            nis = request.form.get("nis")
            siswa = session.query(Siswa).filter_by(nis = nis).first()
            saldo = siswa.saldo
            beli = session.query(Pembelian).all()

            totalList = []
            for harga in beli:
                harga = harga.harga
                totalList.append(harga)
            total = sum(totalList)

            if(total<=saldo):
                sisa = saldo - total
                session.query(Siswa).filter(Siswa.nis == nis).update({
                    Siswa.saldo: sisa
                })

                newRi = Riwayat(siswa_id=siswa.id,
                                saldo=sisa,
                                total=total)
                
                session.add(newRi)
                session.commit()
                result = 'berhasil'
            else:
                session.query(Pembelian).delete()
                session.commit()
                result = "Saldo Tidak Cukup"
            return render_template('kode.html', result = result)

@app.route('/siswa', methods=['GET', 'POST'])
def siswa():
    if request.method == "GET":
            nis = request.args.get("nis")
            name = request.args.get("nama")
            # siswa_id = request.args.get("id")
            siswa = session.query(Siswa).filter_by(nis = nis, name = name).first()
            if(siswa == None):
                 flash('Siswa Tidak Tersedia')
                 return redirect("/")
            else:
                siswa_id = siswa.id
                riwayat = session.query(Riwayat).filter_by(siswa_id = siswa_id)
                return render_template('siswa.html', siswa = siswa, riwayat = riwayat)

if __name__ == "__main__":
    app.run(debug=True)
