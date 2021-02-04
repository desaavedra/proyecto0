from flask import Flask, request,flash
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin, LoginManager , login_user, current_user, logout_user
import datetime
from flask_cors import CORS
app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
ma = Marshmallow(app)
api = Api(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
CORS(app, resources={"*": {
    "origins":{"*","http://localhost:3000/editareventos"},
    }},
    allow_headers={"origin", "content-Type", "Accept", "Authorization",
     "X-Request-With",
     "access-control-allow-credentials",
     "Cookie"
    },
    supports_credentials= True
    )

class Usuario(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column( db.String(50) )
    contrasenia = db.Column( db.String(150) )

class Eventos(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    usuarioid = db.Column(db.Integer, db.ForeignKey('usuario.id'),nullable=False)
    nombre = db.Column( db.String(50) )
    categoria = db.Column( db.String(50) )
    lugar = db.Column( db.String(50) )
    direccion = db.Column( db.String(50) )
    fechaInicio = db.Column( db.DateTime )
    fechaFin = db.Column( db.DateTime )
    isPresencial= db.Column( db.Boolean)

class Evento_Schema(ma.Schema):
    class Meta:
        fields = ("id", "usuarioid", "nombre", "categoria","lugar",
        "direccion","fechaInicio","fechaFin","isPresencial")

class User_Schema(ma.Schema):
    class Meta:
        fields = ("id", "email")

evento_schema = Evento_Schema()
user_schema = User_Schema()
eventos_schema = Evento_Schema(many = True)

class RecursoRegistroUsuarios(Resource):
    def post(self):
        username = request.json['correo']
        password = request.json['password']
        error = None
        if not username:
            error = 'Correo is required.'
        elif not password:
            error = 'Password is required.'
        elif Usuario.query.filter_by(email=username).first() is not None:
            error = 'User {} is already registered.'.format(username)

        if error is None:
            nuevoUsuario = Usuario(email= username,contrasenia=generate_password_hash(password))
            db.session.add(nuevoUsuario)
            db.session.commit()
            return user_schema.dump(nuevoUsuario)
        print(error)
        return error, 202
class RecursoLogoutUsuarios(Resource):
    def post(self):
        logout_user()
        return "Ha cerrado sesión correctamente",200

class RecursoLoginUsuarios(Resource):
    def post(self):
        data=request.get_json(force=True)
        correo = data['correo']
        password = data['password']
        strRemember = data['remember']
        print(strRemember)
        remember= False
        if strRemember==True:
            remember= True
        error = None
        print(remember)
        user = Usuario.query.filter_by(email=correo).first()
        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user.contrasenia, password):
            error = 'Incorrect password.'
        if error is None:
            login_user(user, remember=remember)
            return "exito",200
        else:
            return error, 202

class RecursoRegistrarEventos(Resource):
    def post(self):
        if(current_user.is_authenticated):
            nombre = request.json['nombre']
            categoria =request.json['categoria']
            lugar = request.json['lugar']
            direccion = request.json['direccion']
            fechaIncio = request.json['fechaInicio']
            fechaFin= request.json['fechaFin']
            isPresencial= request.json["ispresencial"]
            user = current_user.id
            error = None
            if not nombre:
                error = 'nombre is required.'
            elif not categoria:
                error = 'categoria is required.'
            elif not lugar:
                error = 'lugar is required.'
            elif not direccion:
                error = 'direccion is required.'
            elif not fechaIncio:
                error = 'fechaIncio is required.'
            elif not fechaFin:
                error = 'fechaFin is required.'
            elif not user:
                error = 'Usuario is required.'
            
            if error is None:
                nuevoEvento = Eventos(
                    nombre=nombre,
                    usuarioid=user,
                    categoria=categoria,
                    lugar= lugar,
                    direccion= direccion,
                    fechaInicio = datetime.datetime.strptime(fechaIncio, '%Y-%m-%d'),
                    fechaFin=datetime.datetime.strptime(fechaFin, '%Y-%m-%d'),
                    isPresencial=isPresencial)
                db.session.add(nuevoEvento)
                db.session.commit()
                return evento_schema.dump(nuevoEvento)
                
            print(error)
            return error, 202
        return "No está autorizado para hacer esta operación", 401
    
    def get(self):
        error = None
        if not current_user.is_authenticated:
            error= 'No esta logeado'
        if error is None:
            eventos =  Eventos.query.filter_by(usuarioid=current_user.id)
            return eventos_schema.dump(eventos)
        return error, 401

class RecursoUnEvento(Resource):
    def get(self, id_evento):
        if current_user.is_authenticated:
            evento = Eventos.query.get_or_404(id_evento)
            return evento_schema.dump(evento)
        else:
            return "No está logeado", 401
    def put(self, id_evento):
        if current_user.is_authenticated:
            evento = Eventos.query.get_or_404(id_evento)
            evento.nombre = request.json['nombre']
            evento.categoria =request.json['categoria']
            evento.lugar = request.json['lugar']
            evento.direccion = request.json['direccion']
            print(request.json['fechaInicio'])
            evento.fechaInicio = datetime.datetime.strptime(request.json['fechaInicio'], '%Y-%m-%dT00:00:00')
            evento.fechaFin= datetime.datetime.strptime(request.json['fechaFin'],'%Y-%m-%dT00:00:00')
            evento.isPresencial = request.json['ispresencial']
            db.session.commit()
            return evento_schema.dump(evento)
        else:
            return "No está logeado", 401
    def delete(self, id_evento):
        if current_user.is_authenticated:
            evento = Eventos.query.get_or_404(id_evento)
            db.session.delete(evento)
            db.session.commit()
            return "Ha eliminado con éxito", 200
        else:
            return "No está logeado", 401


api.add_resource(RecursoRegistroUsuarios, '/registrar')
api.add_resource(RecursoLoginUsuarios, '/login')
api.add_resource(RecursoLogoutUsuarios, '/logout')
api.add_resource(RecursoRegistrarEventos, '/events')
api.add_resource(RecursoUnEvento, '/events/<int:id_evento>')
if __name__ == '__main__':
    app.secret_key = 'super secret key'
    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return Usuario.query.get(int(user_id))

    app.run(debug=True)